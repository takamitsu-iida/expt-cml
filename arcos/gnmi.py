#!/usr/bin/env python

import sys
import pprint


try:
    from pygnmi.client import gNMIclient
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
    # ルータの報告に基づき、PROTO エンコーディングと gNMI 0.7.0 バージョンを指定
    with gNMIclient(target=(HOST, PORT),
                    username=USER,
                    password=PASSWORD,
                    insecure=True
                    ) as gc:

        print(f"✅ ルータ {HOST}:{PORT} への接続に成功しました。")

        # 2. Subscribeリクエストの実行 (ONCEモード)
        # mode='ONCE': 一度データを取得したら接続を閉じます。Get()に最も近い挙動です。
        print("\n⏳ Subscribe (mode=ONCE) リクエストを送信中...")

        # Subscribeリクエストはジェネレータ（イテレータ）を返します
        subscribe_response = gc.subscribe(
            subscribe=[('state', path) for path in INTERFACE_PATH],
            mode='ONCE'
        )

        # 3. 取得結果の処理
        for response in subscribe_response:
            if 'update' in response:
                print("\n📜 取得したインターフェース情報 (Subscribe Update):")
                # 複数の更新が含まれる可能性があるため、反復処理
                for update in response['update']:
                    path_str = gc.format_path(update['path'])
                    # PROTOエンコーディングの場合、値は val に直接格納されるはず
                    value = update.get('val', 'N/A (No value)')

                    print(f"  - パス: {path_str}")
                    print(f"    値: {value}")

            elif 'sync_response' in response:
                # ONCEモードの場合、sync_response はデータの終端を示します
                print("--- データの終端に到達しました (Sync Response) ---")

            # Subscribeの場合、エラーが発生するとストリーム全体が閉じます
            elif 'error' in response:
                print(f"❌ Subscribe中にエラーが発生しました: {response['error']}")
                break

            # 通知以外のメッセージ（例: heartbeat, sync_response）も受け取る
            # pprint.pprint(response) # デバッグ用

        print("✅ Subscribe リクエストの処理が完了しました。")

except Exception as e:
    print(f"🚨 接続またはデータ取得中にエラーが発生しました: {e}")
    print("ヒント: ArcOSは Get() をサポートしておらず、Subscribe() のみサポートしているようです。")