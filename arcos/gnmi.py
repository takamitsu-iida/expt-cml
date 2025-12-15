#!/usr/bin/env python

import sys

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
    # 初期化時の default_encoding は、subscribe リクエスト全体で上書きされるため、今回は削除します。
    # エンコーディングとバージョンは subscribe 呼び出し内で明示的に指定します。
    with gNMIclient(target=(HOST, PORT),
                    username=USER,
                    password=PASSWORD,
                    insecure=True,
                    ) as gc:

        print(f"✅ ルータ {HOST}:{PORT} への接続に成功しました。")

        # 2. Subscribeリクエストの実行 (ONCEモード)
        print("\n⏳ Subscribe (mode=ONCE) リクエストを送信中...")

        # 🚨 修正点: subscribe 引数を dict のリスト形式で定義し、
        #           mode と encoding も合わせて指定する

        # OpenConfigのstateデータ（センサー値）を取得
        SUBSCRIPTIONS = [
            {
                'path': path,
                'mode': 'once',         # ArcOSの Get() 非サポートに対応
                'encoding': 'proto',    # ArcOSがサポートする唯一のエンコーディング
                'sample_interval': 0,   # ONCEモードでは無視されますが、念のため設定
                'suppress_redundant': False, # ONCEモードでは無視されます
                'heartbeat_interval': 0,
            }
            for path in INTERFACE_PATH
        ]

        # Subscribeリクエストはジェネレータ（イテレータ）を返します
        # subscribe 引数には、上記で定義した SUBSCRIPTIONS リストを渡します。
        subscribe_response = gc.subscribe(
            subscribe=SUBSCRIPTIONS
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
                break # ONCEモードなので sync_response が来たら終了

            # Subscribeの場合、エラーが発生するとストリーム全体が閉じます
            elif 'error' in response:
                print(f"❌ Subscribe中にエラーが発生しました: {response['error']}")
                break

        print("✅ Subscribe リクエストの処理が完了しました。")

except Exception as e:
    print(f"🚨 接続またはデータ取得中にエラーが発生しました: {e}")
    print("ヒント: ArcOSの仕様と pygnmi の引数形式の両方に適合するように修正しました。")