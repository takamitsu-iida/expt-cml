#!/usr/bin/env python

import sys

try:
    from pygnmi.client import gNMIclient
except ImportError:
    print(f"pygnmiをインストールしてください")
    sys.exit(1)


# 接続情報
HOST = "192.168.0.1"
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
    # secure=False は、TLS/SSL証明書の検証を行わないことを示します。本番環境では証明書を設定し、secure=True にすることを推奨します。
    # ここでは便宜上、認証なしの接続を想定していますが、
    # 多くのデバイスでは `insecure=False` の場合、認証情報（USER/PASSWORD）が必要です。
    # 接続するルータが自己署名証明書などを使用している場合は、`insecure=True` が必要になることがあります。
    # 接続テストとして、ここでは認証情報を使った接続を試みます。
    with gNMIclient(target=(HOST, PORT),
                    username=USER,
                    password=PASSWORD,
                    insecure=True) as gc:

        print(f"✅ ルータ {HOST}:{PORT} への接続に成功しました。")

        # 2. Getリクエストの実行
        # path に指定した情報（インターフェースの状態データ）を取得します。
        response = gc.get(path=INTERFACE_PATH, datatype='state')

        # 3. 取得結果の処理
        if response['notification']:
            print("\n📜 取得したインターフェース情報:")
            for notification in response['notification']:
                if 'update' in notification:
                    for update in notification['update']:
                        # パスと値を整形して出力
                        path_str = gc.format_path(update['path'])
                        value = update['val']
                        print(f"  - パス: {path_str}")
                        print(f"    値: {value}")

        else:
            print("❌ ルータから情報が取得できませんでした。（'notification'フィールドが空です）")

except Exception as e:
    print(f"🚨 接続またはデータ取得中にエラーが発生しました: {e}")
    print("ヒント: ポート番号（デフォルト 50051）や、TLS/SSLの設定（`insecure=True/False`）を確認してください。")