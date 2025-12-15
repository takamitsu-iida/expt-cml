#!/usr/bin/env python

import sys

try:
    from pygnmi.client import gNMIclient, telemetryParser
except ImportError:
    print(f"pygnmiをインストールしてください")
    sys.exit(1)


# 接続情報
HOST = "192.168.254.1"
PORT = 9339
USER = "cisco"
PASSWORD = "cisco123"

# 例: 3回更新を受け取ったら終了
# 取得するデータが2個あるので、2倍する
MAX_UPDATES = 3 * 2

try:
    # 1. gNMI クライアントの初期化と接続
    # 初期化時の default_encoding は、subscribe リクエスト全体で上書きされるため、今回は削除します。
    # エンコーディングとバージョンは subscribe 呼び出し内で明示的に指定します。
    with gNMIclient(target=(HOST, PORT),
                    username=USER,
                    password=PASSWORD,
                    insecure=True,
                    ) as gc:

        print(f"✅ ルータ {HOST}:{PORT} への接続に成功しました。")

        path1 = 'interfaces/interface[name=swp1]/state/counters/in-octets'
        path2 = 'interfaces/interface[name=swp1]/state/counters/out-octets'

        subscribe = {
            'subscription': [
                {
                    'path': path1,
                    'mode': 'sample',
                    'sample_interval': 30000  # ミリ秒 = 30秒 ArcOSの最小値
                },
                {
                    'path': path2,
                    'mode': 'sample',
                    'sample_interval': 30000
                },
            ],
            'use_aliases': False,
            'mode': 'stream',
            'encoding': 'proto'
        }

        print("\n⏳ Subscribe (mode=STREAM) リクエストを送信中... (Ctrl+Cで終了)")
        telemetry_stream = gc.subscribe(subscribe=subscribe)

        update_count = 0
        try:
            for telemetry_entry in telemetry_stream:

                parsed_data = telemetryParser(telemetry_entry)

                if 'update' in parsed_data:

                    for update in parsed_data['update']['update']:
                        timestamp = parsed_data['update']['timestamp']
                        path = update['path']
                        value = update['val']

                        print(f"時刻: {timestamp}, パス: {path}, 値: {value}")

                        update_count += 1

                        if update_count >= MAX_UPDATES:
                            break

                if update_count >= MAX_UPDATES:
                    break

        except KeyboardInterrupt:
            print("\n\n🛑 ユーザーによって処理が中断されました (Ctrl+C)。")

        print("✅ プログラムを終了します。")

except Exception as e:
    print(f"🚨 接続またはデータ取得中にエラーが発生しました: {e}")
