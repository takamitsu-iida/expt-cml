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

# 収集したいインターフェース情報（OpenConfigパス）
INTERFACE_PATH = ["/interfaces/interface/..."]

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

        subscribe = {
            'subscription': [
                {
                    'path': 'interfaces/interface[name=swp1]/state/counters/in-octets',
                    'mode': 'sample',
                    'sample_interval': 3000  # ミリ秒
                },
                {
                    'path': 'interfaces/interface[name=swp1]/state/counters/out-octets',
                    'mode': 'sample',
                    'sample_interval': 3000  # ミリ秒
                },
            ],
            'use_aliases': False,
            'mode': 'stream',
            'encoding': 'proto'
        }

        telemetry_stream = gc.subscribe(subscribe=subscribe)

        for telemetry_entry in telemetry_stream:
            print(telemetryParser(telemetry_entry))

except Exception as e:
    print(f"🚨 接続またはデータ取得中にエラーが発生しました: {e}")
