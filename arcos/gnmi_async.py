#!/usr/bin/env python

r"""
【事前準備】

1. 適当な作業ディレクトリ(tmp)を作成して移動

mkdir -p tmp

tmpは.gitignoreで管理対象外に指定済み


2. tmpディレクトリに移動

cd tmp

3. 必要なディレクトリ構造を作成

mkdir -p github.com/openconfig/gnmi/proto/gnmi
mkdir -p github.com/openconfig/gnmi/proto/gnmi_ext

4. NMI protoファイルを取得

wget -O github.com/openconfig/gnmi/proto/gnmi/gnmi.proto \
    https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi/gnmi.proto

wget -O github.com/openconfig/gnmi/proto/gnmi_ext/gnmi_ext.proto \
    https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi_ext/gnmi_ext.proto


5. 必要なライブラリをインストール

pip install grpcio grpcio-tools

6. プロトコルバッファをコンパイル

python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --pyi_out=. \
    --grpc_python_out=. \
    github.com/openconfig/gnmi/proto/gnmi/gnmi.proto \
    github.com/openconfig/gnmi/proto/gnmi_ext/gnmi_ext.proto

これで、gnmi_pb2.py と gnmi_pb2_grpc.py が生成されるので、この2つを使いたい場所にコピー

cp github/com/openconfig/gnmi/proto/gnmi/gnmi_pb2.py ..
cp github/com/openconfig/gnmi/proto/gnmi/gnmi_pb2_grpc.py ..
cp github/com/openconfig/gnmi/proto/gnmi_ext/gnmi_ext_pb2.py ..

7. tmpディレクトリを削除して元のディレクトリに戻る

cd ..
rm -rf tmp


8. コピーした gnmi_pb2.py と gnmi_pb2_grpc.py のインポートパスを手動で編集するか、sedコマンドで修正する

# gnmi_pb2.py のインポートパスを修正
sed -i 's/from github\.com\.openconfig\.gnmi\.proto\.gnmi_ext import gnmi_ext_pb2/import gnmi_ext_pb2/g' gnmi_pb2.py

# gnmi_pb2_grpc.py も同様に修正（生成されている場合）
sed -i 's/from github\.com\.openconfig\.gnmi\.proto\.gnmi import gnmi_pb2/import gnmi_pb2/g' gnmi_pb2_grpc.py
sed -i 's/from github\.com\.openconfig\.gnmi\.proto\.gnmi import gnmi_pb2 as gnmi__pb2/import gnmi_pb2 as gnmi__pb2/g' gnmi_pb2_grpc.py
sed -i 's/import gnmi_ext_pb2 as github_dot_com_dot_openconfig_dot_gnmi_dot_proto_dot_gnmi__ext_dot_gnmi__ext__pb2/import gnmi_ext_pb2/g' gnmi_pb2.py

cd ~/git/expt-cml/arcos

# 念のため確認
grep "import gnmi_ext_pb2" gnmi_pb2.py

"""

import asyncio
import logging
import random
import time
from typing import Dict, Any
from enum import Enum
from collections import defaultdict

import grpc.aio

# ローカルに保存したprotobufモジュール（gnmi_pb2.pyとgnmi_pb2_grps.py）をインポート
import gnmi_pb2
import gnmi_pb2_grpc

# ロギング設定
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gNMI_Telemetry')

# 再接続設定（改善版）
INITIAL_DELAY = 1
MAX_RETRY_DELAY = 120
RETRY_RESET_TIME = 600  # 10分間成功したらリセット

# チャネル設定
GRPC_CONNECT_TIMEOUT = 10
GRPC_KEEPALIVE_TIME = 30
GRPC_KEEPALIVE_TIMEOUT = 5

# 収集するテレメトリパスの定義
TELEMETRY_PATH = [
    "/interfaces/interface[name=*]/state/counters/in-octets",
    "/interfaces/interface[name=*]/state/counters/out-octets",
]


class RetryableError(Enum):
    """リトライ可能なエラー判定"""
    UNAVAILABLE = "unavailable"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class CollectorMetrics:
    """簡易監視メトリクス"""
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'total_records': 0,
            'errors': 0,
            'last_error': None,
            'reconnects': 0,
            'last_update_time': None
        })

    def record_data(self, host: str):
        self.metrics[host]['total_records'] += 1
        self.metrics[host]['last_update_time'] = time.time()

    def record_error(self, host: str, error: str):
        self.metrics[host]['errors'] += 1
        self.metrics[host]['last_error'] = error

    def record_reconnect(self, host: str):
        self.metrics[host]['reconnects'] += 1

    def get_summary(self):
        return dict(self.metrics)


def is_retryable_error(error: grpc.aio.AioRpcError) -> bool:
    """gRPCエラーがリトライ可能かを判定"""
    retryable_codes = {
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        grpc.StatusCode.INTERNAL,
        grpc.StatusCode.UNKNOWN,
    }
    return error.code() in retryable_codes


def calculate_backoff(retry_count: int, initial: int = INITIAL_DELAY, max_delay: int = MAX_RETRY_DELAY) -> float:
    """指数バックオフ + ジッター（改善版）"""
    delay = min(initial * (2 ** retry_count), max_delay)
    jitter = random.uniform(0.8, 1.2)
    return delay * jitter


async def request_generator(subscribe_request: gnmi_pb2.SubscribeRequest):
    """
    gNMI Subscribe のリクエストストリームを生成
    最初に SubscribeRequest を送信して終了
    """
    yield subscribe_request


async def data_processor(data_queue: asyncio.Queue, metrics: CollectorMetrics, shutdown_event: asyncio.Event):
    """
    改善版：バックプレッシャー対応、終了シグナル対応
    """
    logger.info("Data Processor task started.")
    data_buffer = []

    try:
        while not shutdown_event.is_set():
            try:
                # タイムアウト付きで取得（shutdown_event を定期的にチェック）
                data = await asyncio.wait_for(data_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # タイムアウト時もバッファが溜まっていたら処理
                if data_buffer:
                    logger.info(f"Processing {len(data_buffer)} records (timeout flush).")
                    data_buffer = []
                continue

            data_buffer.append(data)

            # ノンブロッキングで追加データを取得
            while not data_queue.empty() and len(data_buffer) < 50:  # 上限設定
                try:
                    data_buffer.append(data_queue.get_nowait())
                except asyncio.QueueEmpty:
                    break

            # バッチ処理
            if len(data_buffer) >= 10:
                logger.info(f"Processing {len(data_buffer)} records.")
                for record in data_buffer:
                    metrics.record_data(record['host'])
                data_buffer = []

            data_queue.task_done()

    except asyncio.CancelledError:
        logger.warning("Data Processor task cancelled.")
    except Exception as e:
        logger.error(f"Data Processor failed: {e}")
    finally:
        logger.info("Data Processor task stopped.")


async def collector(
    host: str,
    port: int,
    user: str,
    password: str,
    data_queue: asyncio.Queue,
    metrics: CollectorMetrics,
    shutdown_event: asyncio.Event
):
    """
    改善版：エラー分類、リソース管理強化、メトリクス記録
    """
    retry_count = 0
    last_success_time = time.time()

    while not shutdown_event.is_set():
        channel = None

        try:
            # チャネル作成（タイムアウト・キープアライブ設定）
            channel_opts = [
                ('grpc.max_connection_idle_ms', 60000),
                ('grpc.keepalive_time_ms', GRPC_KEEPALIVE_TIME * 1000),
                ('grpc.keepalive_timeout_ms', GRPC_KEEPALIVE_TIMEOUT * 1000),
            ]
            channel = grpc.aio.insecure_channel(f"{host}:{port}", options=channel_opts)
            stub = gnmi_pb2_grpc.gNMIStub(channel)
            metadata = [("username", user), ("password", password)]

            subscribe_request = gnmi_pb2.SubscribeRequest(
                subscribe=gnmi_pb2.SubscriptionList(
                    mode=gnmi_pb2.SubscriptionList.Mode.STREAM,
                    encoding=gnmi_pb2.Encoding.PROTO,
                    subscription=[
                        gnmi_pb2.Subscription(
                            path=gnmi_pb2.Path(
                                elem=[
                                    gnmi_pb2.PathElem(name="interfaces"),
                                    gnmi_pb2.PathElem(name="interface", key={"name": "*"}),
                                    gnmi_pb2.PathElem(name="state"),
                                    gnmi_pb2.PathElem(name="counters"),
                                    gnmi_pb2.PathElem(name="in-octets"),
                                ]
                            ),
                            mode=gnmi_pb2.SubscriptionMode.SAMPLE,
                            sample_interval=10_000_000_000,
                        ),
                        gnmi_pb2.Subscription(
                            path=gnmi_pb2.Path(
                                elem=[
                                    gnmi_pb2.PathElem(name="interfaces"),
                                    gnmi_pb2.PathElem(name="interface", key={"name": "*"}),
                                    gnmi_pb2.PathElem(name="state"),
                                    gnmi_pb2.PathElem(name="counters"),
                                    gnmi_pb2.PathElem(name="out-octets"),
                                ]
                            ),
                            mode=gnmi_pb2.SubscriptionMode.SAMPLE,
                            sample_interval=10_000_000_000,
                        ),
                    ],
                )
            )

            logger.info(f"[{host}] Connecting... (attempt {retry_count + 1})")
            request_iter = request_generator(subscribe_request)

            async for response in stub.Subscribe(request_iter, metadata=metadata):
                logger.debug(f"[{host}] Received gNMI response.")

                # レスポンスの種類を判定
                if response.HasField("sync_response"):
                    logger.info(f"[{host}] Sync response received.")
                    retry_count = 0  # 成功時はリセット
                    last_success_time = time.time()

                elif response.HasField("error"):
                    # エラーオブジェクトの詳細を表示
                    error_code = response.error.code
                    error_message = response.error.message
                    logger.error(f"[{host}] Error in response: Code={error_code}, Message={error_message}")
                    # Code=0 は OK、つまりエラーではないので処理を続行
                    if error_code != 0:
                        break

                elif response.HasField("update"):
                    update = response.update
                    logger.debug(f"[{host}] Update response received.")

                    # タイムスタンプはナノ秒単位で来るので、秒単位に変換
                    timestamp_s = update.timestamp / 1e9

                    if update.prefix:
                        # prefixはPathオブジェクトなので、文字列に変換して表示
                        prefix_path = "/".join([elem.name for elem in update.prefix.elem])
                    else:
                        prefix_path = ""

                    for delete_path in update.delete:
                        delete_path_str = "/".join([elem.name for elem in delete_path.elem])
                        logger.debug(f"[{host}] Deleted: /{prefix_path}/{delete_path_str}")

                    for update_val in update.update:
                        path_str = "/".join([elem.name for elem in update_val.path.elem])

                        # 値のタイプによって表示を調整
                        value_str = None
                        if update_val.val.HasField("json_ietf_val"):
                            value_str = update_val.val.json_ietf_val.decode('utf-8')
                        elif update_val.val.HasField("string_val"):
                            value_str = update_val.val.string_val
                        elif update_val.val.HasField("int_val"):
                            value_str = str(update_val.val.int_val)
                        elif update_val.val.HasField("uint_val"):
                            value_str = str(update_val.val.uint_val)
                        elif update_val.val.HasField("bytes_val"):
                            value_str = update_val.val.bytes_val.hex()
                        else:
                            value_str = str(update_val.val)

                        logger.info(f"[{host}] Updated: /{prefix_path}/{path_str} = {value_str}")

                        telemetry_record = {
                            'host': host,
                            'path': path_str,
                            'value': value_str,
                            'timestamp': timestamp_s,
                            'received_at': time.time()
                        }

                        # キューにデータを投入
                        await data_queue.put(telemetry_record)

                else:
                    logger.debug(f"[{host}] Unknown response type received.")

            logger.warning(f"[{host}] Stream ended. Reconnecting...")

        except grpc.aio.AioRpcError as e:
            is_retryable = is_retryable_error(e)
            logger.error(
                f"[{host}] gRPC error: {e.code()} - {e.details()} (retryable={is_retryable})"
            )
            metrics.record_error(host, f"{e.code()}")

            if not is_retryable:
                logger.error(f"[{host}] Non-retryable error. Stopping collector.")
                break

        except asyncio.CancelledError:
            logger.warning(f"[{host}] Collection task cancelled.")
            break

        except Exception as e:
            logger.error(f"[{host}] Error: {e.__class__.__name__}: {e}")
            metrics.record_error(host, str(e))

        finally:
            if channel:
                try:
                    await asyncio.wait_for(channel.close(), timeout=GRPC_CONNECT_TIMEOUT)
                except asyncio.TimeoutError:
                    logger.warning(f"[{host}] Channel close timeout.")
                except Exception as close_e:
                    logger.debug(f"[{host}] Channel close error: {close_e}")

            # リセット判定：10分以上成功していたらリトライ数をリセット
            if time.time() - last_success_time > RETRY_RESET_TIME:
                retry_count = 0

            if not shutdown_event.is_set():
                backoff_time = calculate_backoff(retry_count)
                logger.info(f"[{host}] Retrying in {backoff_time:.1f}s (retry_count={retry_count})")
                await asyncio.sleep(backoff_time)
                retry_count += 1
                metrics.record_reconnect(host)


# =================================================================
# メイン実行部
# =================================================================

async def main():
    """
    改善版：グレースフルシャットダウン、メトリクス報告
    """
    # ルータのインベントリ情報 (実際には外部ファイルやDBから読み込む)
    router_inventory = [
        {"host": "192.168.254.1", "port": 9339, "user": "cisco", "password": "cisco123"},
        {"host": "192.168.254.2", "port": 9339, "user": "cisco", "password": "cisco123"},
    ]

    # データ共有のためのasyncio.Queueを初期化
    data_queue = asyncio.Queue(maxsize=500)  # キューサイズを明示的に設定
    metrics = CollectorMetrics()
    shutdown_event = asyncio.Event()

    # データ処理タスクを開始
    data_processor_task = asyncio.create_task(
        data_processor(data_queue, metrics, shutdown_event)
    )

    # 全ルータの収集Taskを作成
    collection_tasks = []
    for router in router_inventory:
        task = asyncio.create_task(
            collector(
                router['host'],
                router['port'],
                router['user'],
                router['password'],
                data_queue,
                metrics,
                shutdown_event
            )
        )
        collection_tasks.append(task)

    logger.info(f"Started {len(collection_tasks)} collection task(s) and 1 processor task.")

    try:
        # 全ての収集タスクが継続的に実行されるように待機
        # return_exceptions=True により、個別タスクエラーで全体が止まらない
        await asyncio.gather(*collection_tasks, data_processor_task, return_exceptions=True)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal.")
    finally:
        shutdown_event.set()
        # 全収集タスクをキャンセル
        for task in collection_tasks + [data_processor_task]:
            if not task.done():
                task.cancel()

        # 収集タスクのキャンセルを待機
        await asyncio.gather(*collection_tasks, data_processor_task, return_exceptions=True)

        # 最終メトリクス表示
        logger.info(f"Final Metrics: {metrics.get_summary()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
