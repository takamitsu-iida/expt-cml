#!/usr/bin/env python

from ncclient import manager
from ncclient.transport.errors import AuthenticationError, TransportError
from ncclient.operations.rpc import RPCError # RPCErrorも明示的にインポート
import xml.dom.minidom

# --- 接続情報の設定 ---
TARGET_HOST = "192.168.254.1"
TARGET_PORT = 830
TARGET_USER = "cisco"
TARGET_PASS = "cisco123"

# フィルターは使用せず、設定データソースのみを指定する
# <get-config> はフィルターを省略すると全設定を取得する
NETCONF_GET_CONFIG_SOURCE = 'running'
NETCONF_GET_FILTER = "<filter/>" # ただし、get_configではフィルターを省略する

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

        # --- データの取得 (get-config に変更) ---
        print(f"\n➡️ <get-config> RPCを送信中 (ソース: <{NETCONF_GET_CONFIG_SOURCE}>)...")

        # 💥 修正: conn.get から conn.get_config に変更。
        # source パラメータは必須。filter は空のまま、または省略。
        result = conn.get_config(
            source=NETCONF_GET_CONFIG_SOURCE,
            # filter=NETCONF_GET_FILTER # ArcOSが filter を嫌うため、ここでは省略
        )

        # --- 結果の整形と表示 ---
        xml_output = result.xml
        dom = xml.dom.minidom.parseString(xml_output)

        print("\n--- 取得結果 (NETCONF XML) ---")
        print(dom.toprettyxml(indent="  "))
        print("\n...NETCONF通信が成功しました。")

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
    except RPCError as e: # RPCErrorを明示的に捕捉
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")

if __name__ == "__main__":
    connect_to_netconf_device()