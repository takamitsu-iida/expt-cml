#!/usr/bin/env python

from ncclient import manager
from ncclient.transport.errors import AuthenticationError, TransportError
from ncclient.operations.rpc import RPCError
import xml.dom.minidom

# --- 接続情報の設定 ---
TARGET_HOST = "192.168.254.1"
TARGET_PORT = 830
TARGET_USER = "cisco"
TARGET_PASS = "cisco123"

# 💥 変更点: インターフェースの状態を取得するための <get> フィルタ
# 'interfaces-state' は、標準の ietf-interfaces モデルで状態データが格納される場所です。
NETCONF_GET_FILTER = """
<filter type="subtree">
    <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface/>
    </interfaces-state>
</filter>
"""

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

        # --- データの取得 (get-config から get に戻す) ---
        print("\n➡️ <get> RPCを送信中 (インターフェース状態フィルタ)...")

        # 💥 変更点: conn.get_config から conn.get に変更
        result = conn.get(filter=NETCONF_GET_FILTER)

        # --- 結果の整形と表示 ---
        xml_output = result.xml
        dom = xml.dom.minidom.parseString(xml_output)

        print("\n--- 取得結果 (インターフェース状態 NETCONF XML) ---")
        print(dom.toprettyxml(indent="  "))
        print("\n...NETCONF通信が成功しました。")

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        print("💡 ヒント: ArcOSが標準のietf-interfacesをサポートしていない可能性があります。")
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")

if __name__ == "__main__":
    connect_to_netconf_device()