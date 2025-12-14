#!/usr/bin/env python

from ncclient import manager
from ncclient.transport.errors import AuthenticationError, TransportError # 💥 修正: TransportErrorを正しくインポート
import xml.dom.minidom

# --- 接続情報の設定 ---
TARGET_HOST = "192.168.254.1"
TARGET_PORT = 830
TARGET_USER = "cisco"
TARGET_PASS = "cisco123"

# 💥 修正: 最も汎用的な空の GET フィルターを使用
NETCONF_GET_FILTER = "<filter/>"

def connect_to_netconf_device():
    conn = None
    try:
        print(f"➡️ NETCONF接続を試行中: {TARGET_HOST}:{TARGET_PORT} (ユーザー: {TARGET_USER})")

        conn = manager.connect(
            host=TARGET_HOST,
            port=TARGET_PORT,
            username=TARGET_USER,
            password=TARGET_PASS,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=30
        )

        print(f"✅ NETCONFセッションが確立されました。セッションID: {conn.session_id}")

        # --- データの取得 ---
        print("\n➡️ <get> RPCを送信中...")
        # フィルタは ncclient の get メソッドに直接渡す
        result = conn.get(filter=NETCONF_GET_FILTER)

        # --- 結果の整形と表示 ---
        xml_output = result.xml
        dom = xml.dom.minidom.parseString(xml_output)

        print("\n--- 取得結果 (NETCONF XML) ---")
        print(dom.toprettyxml(indent="  "))
        print("\n...NETCONF通信が成功しました。")

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
    except TransportError as e: # 💥 修正: TransportError の例外処理
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
    except manager.operations.rpc.RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")

if __name__ == "__main__":
    connect_to_netconf_device()