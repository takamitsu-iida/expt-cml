#!/usr/bin/env python

"""
【事前準備】

＊適当な作業ディレクトリを作成

mkdir proto
cd proto

＊gNMI protoファイルを取得

wget https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi/gnmi.proto
wget https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi_ext/gnmi_ext.proto

＊必要なライブラリをインストール

pip install grpcio grpcio-tools

＊プロトコルバッファをコンパイル

python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    gnmi.proto gnmi_ext.proto

これで、gnmi_pb2.py と gnmi_pb2_grpc.py が生成される


"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, AsyncIterator

import ssl
import grpc.aio

# ローカルにある、生成したprotobufモジュールをインポート
import gnmi_pb2
import gnmi_pb2_grpc # gnmi_pb2_grpc.py が生成されている場合


# ロギング設定 (変更なし)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gNMI_Telemetry')

# 再接続設定
INITIAL_DELAY = 1      # 最初の再接続までの待機時間（秒）
MAX_RETRY_DELAY = 120  # 最大待機時間（秒）
MAX_RETRY_ATTEMPTS = 5 # 接続を諦めるまでの最大試行回数 (無限ループのため、省略可だが、実用上は必要)

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


TARGET_ADDRESS = "192.168.254.1:9339"


async def collector(host: str, port: int, user: str, password: str, data_queue: asyncio.Queue):

    retry_delay = INITIAL_DELAY

    while True:
        channel = None # ループごとにクライアント変数をリセット

        try:

            # SSL/TLS 接続の場合
            # 必要に応じて、信頼されたルート証明書 (root_certificates) や
            # クライアント証明書とキー (private_key, certificate_chain) を設定
            # production環境では必ずSSL/TLSを使用してください
            # insecure_channelを使用すると警告が出されます。
            # credentials = grpc.ssl_channel_credentials()
            # channel = Channel(TARGET_ADDRESS, credentials=credentials)

            # 開発/テスト目的で、SSL/TLSなしの接続（非推奨）
            # 実際にはTLSを使用すべきです
            channel = Channel(f"{host}:{port}", plaintext=True)

            # gNMI Stub を作成
            # gnmi_pb2_grpc に AsyncgNMIStub が含まれていると期待します
            # grpcio-tools のバージョンによっては、AsyncStub のクラス名が異なる場合があります
            # もし AsyncgNMIStub が見つからない場合:
            # 1. gnmi_pb2_grpc.py の中身を確認し、正しい Stub オブジェクト名を探す
            # 2. 最新のgrpcio-toolsでは、非同期Stubは grpc.aio.ClientInterceptor か、
            #    より高レベルなインターフェースで提供されることが多いです。
            #    asyncio-grpc 自体が非同期バージョンとして機能するので、
            #    gnmi_pb2_grpc.gNMIStub(channel) でも Async を扱える可能性があります。
            # ここでは asyncio-grpc の推奨される方法で Stub を取得します。
            # gnmi_pb2_grpc.gNMIStub は同期 Stub なので、asyncio-grpc の Channel を通して使う方式です。
            stub = gnmi_pb2_grpc.gNMIStub(channel)

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

            print("Sending SubscribeRequest...")
            # Subscribe RPC を呼び出し、レスポンスを非同期でイテレート
            async for response in stub.Subscribe(subscribe_request):
                print("\n--- Received gNMI Notification ---")
                if response.sync_response:
                    print("Sync response received.")
                elif response.error:
                    print(f"Error: {response.error}")
                elif response.update:
                    update = response.update
                    # タイムスタンプはナノ秒単位で来るので、秒単位に変換
                    timestamp_s = update.timestamp / 1e9
                    print(f"Timestamp: {timestamp_s}")

                    if update.prefix:
                        # prefixはPathオブジェクトなので、文字列に変換して表示
                        prefix_path = "/".join([elem.name for elem in update.prefix.elem])
                        print(f"Prefix: /{prefix_path}")

                    for delete_path in update.delete:
                        delete_path_str = "/".join([elem.name for elem in delete_path.elem])
                        print(f"  Deleted: /{delete_path_str}")

                    for update_val in update.update:
                        path_str = "/".join([elem.name for elem in update_val.path.elem])
                        # 値のタイプによって表示を調整
                        if update_val.val.HasField("json_ietf_val"):
                            # json_ietf_valはbytesなのでデコード
                            print(f"  Updated: /{path_str} = {update_val.val.json_ietf_val.decode('utf-8')}")
                        elif update_val.val.HasField("string_val"):
                            print(f"  Updated: /{path_str} = {update_val.val.string_val}")
                        elif update_val.val.HasField("int_val"):
                            print(f"  Updated: /{path_str} = {update_val.val.int_val}")
                        # 他のvalタイプも必要に応じて追加
                        else:
                            print(f"  Updated: /{path_str} = (Value Type Not Handled) {update_val.val}")

                        telemetry_record = {
                            'host': host,
                            'path': path_str,
                            'value': update_val.val,
                            'timestamp': timestamp_s,
                            'received_at': time.time()
                        }

                        # キューにデータを投入
                        await data_queue.put(telemetry_record)

            logger.warning(f"[{host}] Stream ended normally. Attempting to reconnect.")


        except asyncio.CancelledError:
            logger.warning(f"[{host}] Telemetry collection task was cancelled. Exiting.")
            break

        except Exception as e:
            logger.error(f"[{host}] Connection failed: {e.__class__.__name__}: {e}. Retrying.")

        finally:

            if channel:
                try:
                    await channel.close()
                except Exception as close_e:
                    # close自体が失敗する場合もあるが、無視して再接続へ
                    logger.debug(f"[{host}] Error during channel close: {close_e}")

            await asyncio.sleep(retry_delay)
            new_delay = retry_delay * 2

            # ジッター (ランダムなノイズ) の追加
            jitter = random.uniform(0.8, 1.2)
            retry_delay = min(new_delay * jitter, MAX_RETRY_DELAY)


# =================================================================
# 3. メイン実行部
# =================================================================

async def main():

    # テスト用
    # ルータのインベントリ情報 (実際には外部ファイルやDBから読み込む)
    router_inventory = [
        { "host": "192.168.254.1", "port": 9339, "user": "cisco", "password": "cisco123"},
        { "host": "192.168.254.2", "port": 9339, "user": "cisco", "password": "cisco123"},
    ]

    # データ共有のためのasyncio.Queueを初期化
    data_queue = asyncio.Queue(maxsize=1000) # キューサイズを設定 (一時的なバッファリング)

    # データ処理タスクを開始 (単一または複数)
    processor_task = asyncio.create_task(data_processor(data_queue))

    # 全ルータの収集Taskを作成
    collection_tasks = []
    for router in router_inventory:
        task = asyncio.create_task(
            collector(router['host'], router['port'], router['user'], router['password'], data_queue)
        )
        collection_tasks.append(task)

    logger.info(f"Total {len(collection_tasks)} collection tasks and 1 processor task started.")

    # 全ての収集タスクが継続的に実行されるように待機
    # 実際には、プログラムが終了するまで実行し続けます
    await asyncio.gather(*collection_tasks, return_exceptions=True)

    # 収集タスクが全て終了した場合、プロセッサタスクもキャンセル
    processor_task.cancel()
    await processor_task

if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program stopped by user via KeyboardInterrupt.")
