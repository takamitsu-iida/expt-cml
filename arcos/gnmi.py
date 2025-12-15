#!/usr/bin/env python

import sys

try:
    from pygnmi.client import gNMIclient
except ImportError:
    print(f"pygnmiをインストールしてください")
    sys.exit(1)


# 接続情報
HOST = "192.168.254.1"
# PORT = 50051  # gNMIのデフォルトポート（ルータの設定によって異なる場合があります）
PORT = 9339
USER = "cisco"
PASSWORD = "cisco123"

# 収集したいインターフェース情報（OpenConfigパス）
# すべてのインターフェースの設定と状態を取得するためのパス
# /interfaces/interface[name=*]/state/... を指定することで、すべてのインターフェースの状態情報を取得できます。
INTERFACE_PATH = ["/interfaces/interface[name=*]/state/..."]

try:
    # 1. gNMI クライアントの初期化と接続
    with gNMIclient(target=(HOST, PORT),
                    username=USER,
                    password=PASSWORD,
                    insecure=True) as gc:

        print(f"✅ ルータ {HOST}:{PORT} への接続に成功しました。")

        # 2. Getリクエストの実行
        # , encoding='proto'
        response = gc.get(path=INTERFACE_PATH, datatype='state')

        # 3. 取得結果の処理
        if 'notification' in response and response['notification']:
            print("\n📜 取得したインターフェース情報:")
            for notification in response['notification']:
                if 'update' in notification:
                    for update in notification['update']:
                        # パスと値を整形して出力
                        path_str = gc.format_path(update['path'])

                        # PROTOエンコーディングの場合、値は生のProtobuf形式で返されるため、
                        # pygnmiが内部でデコードした結果を取り出す必要があります。
                        # 通常、値は 'val' キーに直接、デコードされたPythonオブジェクト（辞書など）として格納されます。
                        value = update.get('val', 'N/A (No value)')

                        # より詳細なデバッグが必要な場合は、以下のコメントアウトを外して、レスポンス全体の構造を確認できます。
                        # import pprint; pprint.pprint(update)

                        print(f"  - パス: {path_str}")
                        print(f"    値: {value}")

        else:
            print("❌ ルータから情報が取得できませんでした。（'notification'フィールドが空です）")

except Exception as e:
    print(f"🚨 接続またはデータ取得中にエラーが発生しました: {e}")
