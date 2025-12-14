#!/usr/bin/env python

from ncclient import manager
from ncclient.transport.errors import AuthenticationError, TransportError
from ncclient.operations.rpc import RPCError
import xml.dom.minidom
import xml.etree.ElementTree as ET

# --- 接続情報の設定 (変更なし) ---
TARGET_HOST = "192.168.254.1"
TARGET_PORT = 830
TARGET_USER = "cisco"
TARGET_PASS = "cisco123"

# 実行する操作: <get-config> のみ
NETCONF_GET_CONFIG_SOURCE = 'running'

# OpenConfigのネームスペース定義
OC_IF_NS = "http://openconfig.net/yang/interfaces"
OC_STATE_TAG = f"{{{OC_IF_NS}}}state" # XPathで名前空間を使用するためのタグ

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

        # --- データの取得 (前回成功した <get-config> を実行) ---
        print(f"\n➡️ <get-config> RPCを送信中 (ソース: <{NETCONF_GET_CONFIG_SOURCE}>)...")

        result = conn.get_config(source=NETCONF_GET_CONFIG_SOURCE)

        # --- 結果の解析とインターフェース状態の抽出 ---
        xml_output = result.xml

        # 1. XMLをElementTreeでパース
        root = ET.fromstring(xml_output)

        # 2. OpenConfigのネームスペースを登録
        namespaces = {'oc-if': OC_IF_NS}

        # 3. インターフェースの 'state' データを検索
        # OpenConfigのパス: /interfaces/interface/state
        # ncclientの応答は <rpc-reply><data> から始まる
        interface_states = root.findall('.//oc-if:interface/oc-if:state', namespaces)

        if not interface_states:
            # state タグが見つからなかった場合、別のパスで検索するか、コンフィグと状態が分離していると結論
            print("\n⚠️ OpenConfigの '/interface/state' パスから状態データを見つけられませんでした。")
            print("ArcOSは状態データと設定データを分離しており、<get>操作を意図的にブロックしているようです。")
            print("しかし、取得したXML全体を整形して表示します。インターフェースの状態（Config部分）が含まれているか確認してください。")

            # 見つからなかった場合、取得したXML全体を整形して表示
            dom = xml.dom.minidom.parseString(xml_output)
            print("\n--- 取得結果 (全 running config XML) ---")
            print(dom.toprettyxml(indent="  "))
        else:
            # 状態データが見つかった場合
            print("\n✅ インターフェース状態データを発見しました。")

            # 各インターフェースの状態を出力
            for state_elem in interface_states:
                name_tag = state_elem.find('../oc-if:name', namespaces)
                name = name_tag.text if name_tag is not None else "Unknown"

                oper_status_tag = state_elem.find('oc-if:oper-status', namespaces)
                oper_status = oper_status_tag.text if oper_status_tag is not None else "N/A"

                print(f"--- インターフェース: {name} ---")
                print(f"  オペレーショナルステータス: {oper_status}")
                # XML要素を文字列に変換して表示 (詳細)
                print("  詳細データ:")
                print(ET.tostring(state_elem, encoding='unicode', method='xml'))

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")

if __name__ == "__main__":
    connect_to_netconf_device()