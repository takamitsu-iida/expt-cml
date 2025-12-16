#!/usr/bin/env python

import asyncio
import logging
import random
import time
from typing import Dict, Any

from pygnmi.client import gNMIclient



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


# =================================================================
# 2. 接続・収集タスク (TelemetryCollector)
# =================================================================

async def collect_telemetry(host: str, port: int, user: str, password: str, data_queue: asyncio.Queue):
    """
    指定されたルータに接続し、データを受信したらキューに投入する。
    切断時には指数バックオフで再接続を試みる。
    """
    retry_delay = INITIAL_DELAY

    while True:
        client = None # ループごとにクライアント変数をリセット

        try:
            logger.info(f"[{host}] Attempting connection. Delay: {retry_delay:.2f}s")


            client = gNMIclient(
                target=(host, port),
                username=user,
                password=password,
                insecure=True,
                # Keepalive設定は、インスタンス化の引数で渡します (前述の通り)
            )

            await client.connect()

            logger.info(f"[{host}] Successfully connected. Starting subscribe stream...")

            # 接続成功 => 遅延時間をリセット
            retry_delay = INITIAL_DELAY


            async for stream_data in client.subscribe(subscribe=SUBSCRIBE_REQUEST):

                if stream_data.HasField('update'):
                    updates = stream_data.update.update
                    # タイムスタンプはナノ秒単位で来るので、秒単位に変換
                    timestamp_s = stream_data.update.timestamp / 1e9

                    # --- キューへの投入処理 ---
                    for update in updates:
                        path = client.path_to_string(update.path)
                        value = client.gnmi_to_value(update)

                        telemetry_record = {
                            'host': host,
                            'path': path,
                            'value': value,
                            'timestamp': timestamp_s,
                            'received_at': time.time()
                        }

                        # キューにデータを投入
                        await data_queue.put(telemetry_record)
                    # -------------------------

                elif stream_data.HasField('error'):
                    logger.error(f"[{host}] Stream Error received: {stream_data.error}")

            logger.warning(f"[{host}] Stream ended normally. Attempting to reconnect.")

        except asyncio.CancelledError:
            logger.warning(f"[{host}] Telemetry collection task was cancelled. Exiting.")
            break

        except Exception as e:
            logger.error(f"[{host}] Connection failed: {e.__class__.__name__}: {e}. Retrying.")

        finally:

            if client:
                # 切断も非同期操作なので await が必要
                try:
                    await client.close()
                except Exception as close_e:
                    # close自体が失敗する場合もあるが、無視して再接続へ
                    logger.debug(f"[{host}] Error during client close: {close_e}")

            # 3. 再接続のための待機と指数バックオフ計算
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
            collect_telemetry(router['host'], router['port'], router['user'], router['password'], data_queue)
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
