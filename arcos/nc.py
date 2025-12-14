#!/usr/bin/env python

from ncclient import manager
from ncclient.transport.errors import AuthenticationError
import xml.dom.minidom

# --- 接続情報の設定 ---
TARGET_HOST = "192.168.254.1"
TARGET_PORT = 830  # NETCONF over SSH の標準ポートは 830
TARGET_USER = "cisco"
TARGET_PASS = "cisco123"

# ArcOS向けの基本 GET フィルター
# ArcOSは独自の YANG モジュールを使用している可能性が高いため、
# 汎用的な YANG データではなく、デバイス固有の情報を取得するフィルターを使用
NETCONF_GET_FILTER = """
<filter type="subtree">
  <system-info xmlns="http://arrcus.com/yang/arcos-system"/>
</filter>
"""

def connect_to_netconf_device():
    conn = None
    try:
        print(f"➡️ NETCONF接続を試行中: {TARGET_HOST}:{TARGET_PORT} (ユーザー: {TARGET_USER})")

        # ncclient.manager.connect() を使用して直接接続
        conn = manager.connect(
            host=TARGET_HOST,
            port=TARGET_PORT,
            username=TARGET_USER,
            password=TARGET_PASS,
            hostkey_verify=False,  # 鍵交換時のホストキー確認を無効化 (ArcOS環境で必須の可能性あり)

            # Paramiko オプションの設定 (SSHエージェントやキーファイルの使用を無効化)
            allow_agent=False,
            look_for_keys=False,
            timeout=30  # タイムアウトを30秒に設定
        )

        print(f"✅ NETCONFセッションが確立されました。セッションID: {conn.session_id}")

        # --- データの取得 ---
        print("\n➡️ <get> RPCを送信中...")
        result = conn.get(filter=NETCONF_GET_FILTER)

        # --- 結果の整形と表示 ---
        xml_output = result.xml
        dom = xml.dom.minidom.parseString(xml_output)

        print("\n--- 取得結果 (NETCONF XML) ---")
        print(dom.toprettyxml(indent="  "))
        print("\n...NETCONF通信が成功しました。")

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
    except manager.TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")

if __name__ == "__main__":
    connect_to_netconf_device()