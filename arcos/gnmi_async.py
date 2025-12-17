#!/usr/bin/env python

"""
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



cisco@jumphost:~/expt-cml/arcos$ ./gnmi_async.py
/home/cisco/expt-cml/arcos/./gnmi_async.py:3: SyntaxWarning: invalid escape sequence '\.'
  """
2025-12-17 11:31:51,289 - gNMI_Telemetry - INFO - Started 2 collection task(s) and 1 processor task.
2025-12-17 11:31:51,289 - gNMI_Telemetry - INFO - Data Processor task started.
2025-12-17 11:31:51,290 - gNMI_Telemetry - INFO - [192.168.254.1] Sending SubscribeRequest...
2025-12-17 11:31:51,291 - gNMI_Telemetry - INFO - [192.168.254.2] Sending SubscribeRequest...
2025-12-17 11:31:51,294 - gNMI_Telemetry - WARNING - [192.168.254.1] Collection task cancelled.
2025-12-17 11:31:51,295 - gNMI_Telemetry - WARNING - [192.168.254.2] Collection task cancelled.
2025-12-17 11:31:52,297 - gNMI_Telemetry - WARNING - Data Processor task cancelled.
2025-12-17 11:31:52,298 - gNMI_Telemetry - INFO - Data Processor task stopped.
cisco@jumphost:~/expt-cml/arcos$


"""

import asyncio
import base64
import logging
import random
import time
from typing import Dict, Any

import grpc.aio

# ローカルに保存したprotobufモジュール（gnmi_pb2.pyとgnmi_pb2_grps.py）をインポート
import gnmi_pb2
import gnmi_pb2_grpc

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gNMI_Telemetry')

# 再接続設定
INITIAL_DELAY = 1      # 最初の再接続までの待機時間（秒）
MAX_RETRY_DELAY = 120  # 最大待機時間（秒）

# 収集するテレメトリパスの定義
TELEMETRY_PATH = [
    "/interfaces/interface[name=*]/state/counters/in-octets",
    "/interfaces/interface[name=*]/state/counters/out-octets",
]

# gNMI Subscribeリクエスト
SUBSCRIBE_REQUEST = {
    "subscription": [
        {
            "path": path,
            "mode": "sample",
            "sample_interval": 30_000_000_000,  # ナノ秒 = 30秒
        } for path in TELEMETRY_PATH
    ]
}


# =================================================================
# 1. データ処理タスク (DataProcessor)
# =================================================================

async def data_processor(data_queue: asyncio.Queue):
    """
    キューからテレメトリデータを取り出して処理を行うタスク
    """
    logger.info("Data Processor task started.")

    # リアルタイム処理用のバッファ
    data_buffer = []

    try:
        while True:
            # キューからデータを取り出す (キューが空の場合は待機)
            data: Dict[str, Any] = await data_queue.get()

            # データの処理・バッファリング
            data_buffer.append(data)

            # キューにデータがある場合は、できるだけ早く取り出す (まとめて処理するため)
            while not data_queue.empty():
                data_buffer.append(data_queue.get_nowait())

            # 一定サイズに達したら、データベースにまとめて書き込む
            if len(data_buffer) >= 10: # 例: 10個溜まったらDBに書き込む

                # --- ここにデータベース書き込み処理を実装 ---
                # 例: InfluxDBへの書き込み、KafkaへのPublishなど
                #
                # 実際のDB I/Oは時間がかかるため、
                # DBクライアントがasyncに対応していない場合は、
                # `await asyncio.to_thread(sync_db_write, data_buffer)`
                # のように別スレッドで実行することを推奨します。

                logger.info(f"Processing {len(data_buffer)} records. (Host: {data['host']}, Path: {data['path']})")

                data_buffer = [] # バッファをクリア
                # ----------------------------------------------

            # キューのタスク完了を通知
            data_queue.task_done()

    except asyncio.CancelledError:
        logger.warning("Data Processor task cancelled.")
    except Exception as e:
        logger.error(f"Data Processor failed: {e}")

    logger.info("Data Processor task stopped.")


def build_auth_metadata(user: str, password: str) -> list:
    """
    基本認証用メタデータを作成
    """
    credentials = f"{user}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return [("authorization", f"Basic {encoded}")]


async def collector(host: str, port: int, user: str, password: str, data_queue: asyncio.Queue):
    """
    gNMI テレメトリ収集タスク (非同期)
    """
    retry_delay = INITIAL_DELAY

    while True:
        channel = None

        try:
            # grpc.aio.secure_channel() または grpc.aio.insecure_channel() を使用
            # 本番環境ではセキュアチャンネル推奨、開発環境では insecure でテスト可能
            channel = grpc.aio.insecure_channel(f"{host}:{port}")

            # 非同期 gNMI Stub を作成
            stub = gnmi_pb2_grpc.gNMIStub(channel)

            # 基本認証メタデータを準備
            metadata = build_auth_metadata(user, password)

            # SubscribeRequest の設定
            subscribe_request = gnmi_pb2.SubscribeRequest(
                subscribe=gnmi_pb2.SubscriptionList(
                    mode=gnmi_pb2.SubscriptionList.Mode.STREAM,
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
                            sample_interval=10_000_000_000,  # 10秒（ナノ秒）
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
                            sample_interval=10_000_000_000,  # 10秒（ナノ秒）
                        ),
                    ],
                )
            )

            logger.info(f"[{host}] Sending SubscribeRequest...")

            # Subscribe RPC を呼び出し、レスポンスを非同期でイテレート
            async for response in stub.Subscribe(subscribe_request, metadata=metadata):
                logger.debug(f"[{host}] Received gNMI response.")

                if response.sync_response:
                    logger.info(f"[{host}] Sync response received.")

                elif response.error:
                    logger.error(f"[{host}] Error in response: {response.error}")

                elif response.update:
                    update = response.update
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
                        else:
                            value_str = str(update_val.val)

                        logger.debug(f"[{host}] Updated: /{prefix_path}/{path_str} = {value_str}")

                        telemetry_record = {
                            'host': host,
                            'path': path_str,
                            'value': value_str,
                            'timestamp': timestamp_s,
                            'received_at': time.time()
                        }

                        # キューにデータを投入
                        await data_queue.put(telemetry_record)

            logger.warning(f"[{host}] Stream ended normally. Attempting to reconnect.")

        except grpc.aio.AioRpcError as e:
            logger.error(f"[{host}] gRPC error: {e.code()} - {e.details()}. Retrying in {retry_delay}s.")

        except asyncio.CancelledError:
            logger.warning(f"[{host}] Collection task cancelled.")
            break

        except Exception as e:
            logger.error(f"[{host}] Connection failed: {e.__class__.__name__}: {e}. Retrying in {retry_delay}s.")

        finally:
            if channel:
                try:
                    await channel.close()
                except Exception as close_e:
                    logger.debug(f"[{host}] Error during channel close: {close_e}")

            # 再接続までの待機
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)

            # ジッター (ランダムなノイズ) の追加
            jitter = random.uniform(0.8, 1.2)
            retry_delay = retry_delay * jitter


# =================================================================
# 2. メイン実行部
# =================================================================

async def main():
    """
    メイン関数：全ての非同期タスクを管理
    """
    # ルータのインベントリ情報 (実際には外部ファイルやDBから読み込む)
    router_inventory = [
        {"host": "192.168.254.1", "port": 9339, "user": "cisco", "password": "cisco123"},
        {"host": "192.168.254.2", "port": 9339, "user": "cisco", "password": "cisco123"},
    ]

    # データ共有のためのasyncio.Queueを初期化
    data_queue = asyncio.Queue(maxsize=1000)

    # データ処理タスクを開始
    processor_task = asyncio.create_task(data_processor(data_queue))

    # 全ルータの収集Taskを作成
    collection_tasks = []
    for router in router_inventory:
        task = asyncio.create_task(
            collector(
                router['host'],
                router['port'],
                router['user'],
                router['password'],
                data_queue
            )
        )
        collection_tasks.append(task)

    logger.info(f"Started {len(collection_tasks)} collection task(s) and 1 processor task.")

    # 全ての収集タスクが継続的に実行されるように待機
    await asyncio.gather(*collection_tasks, return_exceptions=True)

    # 収集タスクが全て終了した場合、プロセッサタスクもキャンセル
    processor_task.cancel()
    try:
        await processor_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program stopped by user via KeyboardInterrupt.")
