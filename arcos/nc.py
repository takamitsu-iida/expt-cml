#!/usr/bin/env python

from ncclient import manager
from ncclient.transport.errors import AuthenticationError, TransportError
from ncclient.operations.rpc import RPCError
import xml.dom.minidom

# --- 接続情報の設定 (変更なし) ---
TARGET_HOST = "192.168.254.1"
TARGET_PORT = 830
TARGET_USER = "cisco"
TARGET_PASS = "cisco123"

# 💥 変更点: OpenConfigインターフェースモデルに基づく、より単純なフィルタ (設定データと状態データの両方を含むパス)
OPENCONFIG_INTERFACE_NAMESPACE = "http://openconfig.net/yang/interfaces"

NETCONF_GET_FILTER = f"""
<filter type="subtree">
    <interfaces xmlns="{OPENCONFIG_INTERFACE_NAMESPACE}"/>
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

        # --- データの取得 ---
        print("\n➡️ <get> RPCを送信中 (OpenConfig 汎用インターフェースフィルタ)...")

        # 💥 修正: OpenConfigのトップレベルコンテナのみを指定
        result = conn.get(filter=NETCONF_GET_FILTER)

        # --- 結果の整形と表示 ---
        xml_output = result.xml
        dom = xml.dom.minidom.parseString(xml_output)

        print("\n--- 取得結果 (OpenConfig インターフェース状態 NETCONF XML) ---")
        print(dom.toprettyxml(indent="  "))
        print("\n...NETCONF通信が成功しました。")

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        # 💥 最終手段: フィルターなしの <get> を再試行
        if "unknown-element" in str(e):
             print("\n💡 OpenConfigフィルタが拒否されました。フィルターなしの全ステータス取得を再試行します (OpenConfigのルール違反の可能性)。")

             try:
                 print("\n➡️ <get> RPCを送信中 (フィルターなし、全ステータスデータ)...")
                 # フィルターを None に設定
                 full_status_result = conn.get(filter=None)

                 full_xml_output = full_status_result.xml
                 full_dom = xml.dom.minidom.parseString(full_xml_output)
                 print("\n--- 取得結果 (フィルターなし全ステータス NETCONF XML) ---")
                 print(full_dom.toprettyxml(indent="  "))
                 print("\n...全ステータスデータの取得に成功しました。インターフェース情報を手動で探してください。")
                 return # 成功したので終了
             except RPCError as full_e:
                 print(f"❌ フィルターなしの <get> も失敗しました: {full_e}")
             except Exception as full_e:
                 print(f"❌ フィルターなしの <get> で致命的なエラーが発生しました: {full_e}")

    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")

if __name__ == "__main__":
    connect_to_netconf_device()