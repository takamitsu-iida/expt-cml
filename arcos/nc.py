#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NETCONF装置設定管理スクリプト

このスクリプトはncclientを使用してNETCONF対応装置の設定を取得・反映します。
主な機能:
- 設定の取得とXMLファイルへの保存
- XMLファイルからの設定反映
- confirmed commitによる安全な設定変更
- capability情報の表示
"""

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = 'netconfで装置から設定を取得・反映します'

import argparse
import os
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom

try:
    from ncclient import manager
    from ncclient.transport.errors import AuthenticationError, TransportError
    from ncclient.operations.rpc import RPCError
except ImportError:
    print("ncclientをインストールしてください")
    sys.exit(1)

# --- 接続情報の設定（検証用） ---
# 本番環境では環境変数や設定ファイルから読み込むことを推奨
TARGET_HOST = "192.168.254.1"  # NETCONF接続先ホスト
TARGET_PORT = 830              # NETCONFポート (標準: 830)
TARGET_USER = "cisco"          # 認証ユーザ名
TARGET_PASS = "cisco123"       # 認証パスワード

# 設定取得元データストア (running/candidate/startup)
NETCONF_GET_CONFIG_SOURCE = 'running'

# 保存先ファイルパス
OUTPUT_DIR = "/tmp"
OUTPUT_FILE = f"{OUTPUT_DIR}/{TARGET_HOST}.xml"
OUTPUT_JSON_FILE = f"{OUTPUT_DIR}/{TARGET_HOST}.json"

# confirmed commitのタイムアウト (秒)
# この時間内に確定コミットがない場合、設定は自動的にロールバックされる
COMMIT_CONFIRM_TIMEOUT = 120  # 2分

# confirmed commitに付与するID
PERSIST_ID = "ABC"


def connect_netconf() -> manager.Manager | None:
    """
    NETCONF接続を確立する

    Returns:
        manager.Manager | None: 接続成功時は接続オブジェクト、失敗時はNone

    Raises:
        なし (全ての例外はキャッチされ、エラーメッセージを表示してNoneを返す)
    """
    print(f"➡️ NETCONF接続を試行中: {TARGET_HOST}:{TARGET_PORT} (ユーザー: {TARGET_USER})")

    try:
        conn = manager.connect(
            host=TARGET_HOST,
            port=TARGET_PORT,
            username=TARGET_USER,
            password=TARGET_PASS,
            hostkey_verify=False,  # 検証環境用 (本番では True 推奨)
            allow_agent=False,
            look_for_keys=False,
            timeout=30
        )
        print(f"✅ NETCONFセッションが確立されました。セッションID: {conn.session_id}")
        return conn
    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
        return None
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
        print("   ヒント: ホスト到達性・ポート・ファイアウォール設定を確認してください。")
        return None
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return None


def format_netconf_xml(xml_output: str) -> str:
    """
    NETCONF応答XMLを整形する

    <data>要素の子要素のみを抽出し、読みやすい形式に整形する。

    Args:
        xml_output: NETCONF応答の生XML文字列

    Returns:
        str: 整形されたXML文字列 (data要素の子要素のみ)

    Raises:
        Exception: XML解析に失敗した場合 (呼び出し元でキャッチ)
    """
    # NETCONFの <data> 要素を解析
    data = ET.fromstring(xml_output)

    # <data>の子要素を抽出
    config_elements = []
    for child in data:
        config_elements.append(ET.tostring(child, encoding='unicode'))

    # 子要素が存在しない場合は空文字列を返す
    if not config_elements:
        return ""

    # 整形処理: 一時的にrootタグで囲んで整形
    dom_formatted = xml.dom.minidom.parseString(
        f'<root>{"".join(config_elements)}</root>'
    )
    xml_formatted = dom_formatted.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    # XML宣言と <root> タグを削除
    lines = xml_formatted.split('\n')[1:]  # XML宣言削除
    lines = [
        line for line in lines
        if not line.strip().startswith('<root') and not line.strip().startswith('</root')
    ]

    return '\n'.join(lines).strip()


def get_xml_config(config_file: str = OUTPUT_FILE) -> bool:
    """
    NETCONFで装置から設定を取得し、ファイルに保存する

    Args:
        config_file: 保存先のXML設定ファイルパス

    Returns:
        bool: 成功時True、失敗時False
    """
    conn = connect_netconf()
    if not conn:
        return False

    try:
        # --- データの取得 (<get-config> を実行) ---
        print(f"\n➡️ <get-config> RPCを送信中 (ソース: <{NETCONF_GET_CONFIG_SOURCE}>)...")
        result = conn.get_config(source=NETCONF_GET_CONFIG_SOURCE)
        xml_output = result.data_xml

        # XML整形処理
        try:
            xml_formatted = format_netconf_xml(xml_output)
        except Exception as e:
            print(f"⚠️ XMLの整形に失敗しました。元の形式のまま保存します: {e}")
            xml_formatted = xml_output

        # ファイル保存
        os.makedirs(os.path.dirname(config_file) or '.', exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(xml_formatted)

        print(f"✅ XML設定を保存しました: {config_file}")
        return True

    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        print("   ヒント: データストアが存在しない、または権限がない可能性があります。")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")


def load_xml_config(config_file: str) -> str | None:
    """
    XML設定ファイルを読み込み、NETCONF用に整形する

    Args:
        config_file: 読み込むXML設定ファイルのパス

    Returns:
        str | None: 成功時は整形済みXML文字列、失敗時はNone
    """
    try:
        if not os.path.exists(config_file):
            print(f"❌ 設定ファイルが見つかりません: {config_file}")
            return None

        with open(config_file, 'r', encoding='utf-8') as f:
            xml_config_content = f.read()

        # NETCONF <edit-config> 用にルート要素で囲む
        xml_config = (
            f'<nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">'
            f'{xml_config_content}'
            f'</nc:config>'
        )
        return xml_config

    except Exception as e:
        print(f"❌ 設定ファイルの読み込みに失敗しました: {e}")
        return None


def apply_xml_config_confirmed(config_file: str = OUTPUT_FILE) -> bool:
    """
    保存したXML設定ファイルをNETCONFで装置に反映させる (confirmed commitを使用)

    confirmed commitは、指定時間内に確定コミットがない場合、
    自動的に設定をロールバックする安全機構です。

    Args:
        config_file: 反映させるXML設定ファイルのパス

    Returns:
        bool: 成功時True、失敗時False
    """
    # 設定ファイル読み込み
    xml_config = load_xml_config(config_file)
    if xml_config is None:
        return False

    conn = connect_netconf()
    if not conn:
        return False

    # persist用のキーワードは固定にします
    persist_id = PERSIST_ID

    try:
        # --- 設定を装置に反映 (<edit-config> を実行) ---
        print(f"\n➡️ <edit-config> RPCを送信中...")
        print(f"   設定ファイル: {config_file}")
        conn.edit_config(target='candidate', config=xml_config)
        print(f"✅ <edit-config>が成功しました (target=candidate)")

        # --- 変更内容を confirmed コミット ---
        print(f"\n➡️ <commit confirmed> RPCを送信中 (timeout: {COMMIT_CONFIRM_TIMEOUT}秒)...")
        print(f"   persist ID: {persist_id}")
        result = conn.commit(confirmed=True, timeout=str(COMMIT_CONFIRM_TIMEOUT), persist=persist_id)
        # print(result)
        print(f"✅ <commit confirmed>が成功しました。")

        print(f"\n⚠️ 設定は一時的に適用されました。{COMMIT_CONFIRM_TIMEOUT}秒以内に以下のコマンドで変更を永続化してください:")
        print(f"   python {os.path.basename(__file__)} confirm")
        print(f"\n   時間内に確定コミットが行われない場合、変更は自動的にロールバックされます。")
        print(f"   手動でロールバックするには以下のコマンドを実行してください:")
        print(f"   python {os.path.basename(__file__)} cancel")

        return True

    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        print("   ヒント: 候補データストアが存在しない、または設定が無効な可能性があります。")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")


def confirm_commit() -> bool:
    """
    commit confirmedで保留中の変更を永続化する

    apply-confirmedで一時適用された設定を確定し、永続化します。

    Returns:
        bool: 成功時True、失敗時False
    """
    conn = connect_netconf()
    if not conn:
        return False

    persist_id = PERSIST_ID

    try:
        print(f"\n➡️ 設定変更を確定するため <commit> RPC を送信中...")
        conn.commit(confirmed=False, persist_id=persist_id)
        print(f"✅ <commit>が成功しました。保留中の変更が永続化されました。")
        return True
    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        print("   ヒント: 保留中のconfirmed commitが存在しない可能性があります。")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")


def cancel_commit() -> bool:
    """
    commit confirmedで保留中の変更をキャンセルする

    apply-confirmedで一時適用された設定をキャンセルし、ロールバックします。

    Returns:
        bool: 成功時True、失敗時False
    """
    conn = connect_netconf()
    if not conn:
        return False

    persist_id = PERSIST_ID

    try:
        print(f"\n➡️ 設定変更をキャンセルするため <cancel-commit> RPC を送信中...")
        conn.cancel_commit(persist_id=persist_id)
        print(f"✅ <cancel-commit>が成功しました。保留中の変更はロールバックされました。")
        return True
    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        print("   ヒント: 保留中のconfirmed commitが存在しない可能性があります。")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")


def apply_xml_config(config_file: str = OUTPUT_FILE) -> bool:
    """
    保存したXML設定ファイルをNETCONFで装置に反映させる

    即座に設定を確定します。ロールバック機能はありません。
    安全な設定変更には apply-confirmed の使用を推奨します。

    Args:
        config_file: 反映させるXML設定ファイルのパス

    Returns:
        bool: 成功時True、失敗時False
    """
    # 設定ファイル読み込み
    xml_config = load_xml_config(config_file)
    if xml_config is None:
        return False

    conn = connect_netconf()
    if not conn:
        return False

    try:
        # --- 設定を装置に反映 (<edit-config> を実行) ---
        print(f"\n➡️ <edit-config> RPCを送信中...")
        print(f"   設定ファイル: {config_file}")
        conn.edit_config(target='candidate', config=xml_config)
        print(f"✅ <edit-config>が成功しました")

        # --- 変更内容をコミット ---
        print(f"\n➡️ <commit> RPCを送信中...")
        conn.commit()
        print(f"✅ <commit>が成功しました。設定が装置に反映されました")
        return True

    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        print("   ヒント: 候補データストアが存在しない、または設定が無効な可能性があります。")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")


def show_capabilities(verbose: bool = False) -> bool:
    """
    NETCONFサーバのcapabilityを表示する

    装置がサポートするNETCONF機能・YANGモジュールを確認できます。

    Args:
        verbose: 詳細表示モード (デフォルト: False)
                 Falseの場合は主要なcapabilityのみ表示

    Returns:
        bool: 成功時True、失敗時False
    """
    conn = connect_netconf()
    if not conn:
        return False

    try:
        print(f"\n📋 サーバのCapabilities一覧 ({len(conn.server_capabilities)}件):\n")
        print("=" * 80)

        if verbose:
            # 詳細表示: 全Capability表示
            for i, capability in enumerate(sorted(conn.server_capabilities), start=1):
                print(f"{i:3d}. {capability}")
        else:
            # 簡易表示: カテゴリ別に整理して表示
            categories = {
                'Base': [],
                'YANG Modules': [],
                'Operations': [],
                'Others': []
            }

            for cap in conn.server_capabilities:
                if 'netconf/base' in cap:
                    categories['Base'].append(cap)
                elif '?module=' in cap or '&module=' in cap:
                    # YANG モジュール名を抽出
                    module_name = cap.split('module=')[1].split('&')[0] if 'module=' in cap else 'unknown'
                    categories['YANG Modules'].append(f"  - {module_name}")
                elif 'capability' in cap:
                    categories['Operations'].append(cap)
                else:
                    categories['Others'].append(cap)

            # Base Capabilities
            if categories['Base']:
                print("\n[Base Capabilities]")
                for cap in categories['Base']:
                    print(f"  {cap}")

            # YANG Modules (重複排除して表示、最大10件)
            if categories['YANG Modules']:
                unique_modules = sorted(set(categories['YANG Modules']))
                print(f"\n[YANG Modules] ({len(unique_modules)}件)")
                for module in unique_modules[:10]:
                    print(module)
                if len(unique_modules) > 10:
                    print(f"  ... and {len(unique_modules) - 10} more modules")
                    print("  (--verbose オプションで全て表示)")

            # Operations
            if categories['Operations']:
                print("\n[Operations]")
                for cap in categories['Operations']:
                    print(f"  {cap}")

        print("\n" + "=" * 80)
        return True

    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False
    finally:
        if conn:
            conn.close_session()
            print("\n接続を閉じました。")


def get_json_config_native(config_file: str = "config.json") -> bool:
    """
    ArcOS固有のRPCを使用して、NETCONF経由でJSON形式の設定を取得する
    """

    from lxml import etree

    conn = connect_netconf()
    if not conn:
        return False

    try:
        # 1. ArcOS固有のRPC構造を作成
        # <get-configuration xmlns="http://yang.arrcus.com/arcos/system">
        #   <encoding>JSON</encoding>
        # </get-configuration>
        rpc_input = etree.Element("{http://yang.arrcus.com/arcos/system}get-configuration")
        encoding = etree.SubElement(rpc_input, "{http://yang.arrcus.com/arcos/system}encoding")
        encoding.text = "JSON"

        print(f"➡️ ArcOS固有のJSON RPCを送信中...")

        # 2. dispatchメソッドでカスタムRPCを送信
        result = conn.dispatch(rpc_input)

        # 3. 返ってきたデータを取り出す
        # 通常、RPCの戻り値の .data_xml 内にJSON文字列が埋め込まれて返ります
        # (装置の応答仕様により、パースが必要な場合があります)
        raw_output = result.data_xml

        # ファイル保存
        os.makedirs(os.path.dirname(config_file) or '.', exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(raw_output)

        print(f"✅ JSON設定（Rawデータ）を保存しました: {config_file}")
        return True

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
    finally:
        if conn:
            conn.close_session()



def main() -> int:
    """
    メイン処理

    コマンドライン引数を解析し、対応する処理を実行します。

    Returns:
        int: 終了コード (0: 成功, 1: 失敗)
    """

    # グローバル変数を引数で上書き可能にする
    global COMMIT_CONFIRM_TIMEOUT

    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')

    # get コマンド
    get_parser = subparsers.add_parser('get', help='装置からXML形式の設定を取得してファイルに保存')
    get_parser.add_argument(
        '-f', '--file',
        type=str,
        default=OUTPUT_FILE,
        help=f'保存先ファイルパス (デフォルト: {OUTPUT_FILE})'
    )

    # get-json コマンド
    get_parser = subparsers.add_parser('get-json', help='装置からJSON形式の設定を取得してファイルに保存')
    get_parser.add_argument(
        '-f', '--file',
        type=str,
        default=OUTPUT_JSON_FILE,
        help=f'保存先ファイルパス (デフォルト: {OUTPUT_JSON_FILE})'
    )

    # apply コマンド
    apply_parser = subparsers.add_parser('apply', help='ファイルから設定を読み込んで装置に反映')
    apply_parser.add_argument(
        '-f', '--file',
        type=str,
        default=OUTPUT_FILE,
        help=f'設定ファイルパス (デフォルト: {OUTPUT_FILE})'
    )

    # apply-confirmed コマンド
    apply_confirmed_parser = subparsers.add_parser('apply-confirmed', help='ファイルから設定を読み込んで装置に一時反映 (commit confirmed)')
    apply_confirmed_parser.add_argument(
        '-f', '--file',
        type=str,
        default=OUTPUT_FILE,
        help=f'設定ファイルパス (デフォルト: {OUTPUT_FILE})'
    )
    apply_confirmed_parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=COMMIT_CONFIRM_TIMEOUT,
        help=f'commit confirmedのタイムアウト時間 (秒、デフォルト: {COMMIT_CONFIRM_TIMEOUT})'
    )

    # confirm コマンド
    confirm_parser = subparsers.add_parser('confirm', help='apply-confirmedで一時適用された設定を永続化')

    # cancel コマンド
    cancel_parser = subparsers.add_parser('cancel', help='apply-confirmedで一時適用された設定をキャンセルしロールバック')

    # capability コマンド
    cap_parser = subparsers.add_parser('capability', help='NETCONFサーバのcapabilityを表示')
    cap_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='全capabilityを詳細表示'
    )

    args = parser.parse_args()

    # 引数がなければhelpを表示
    if not args.command:
        parser.print_help()
        return 0

    # コマンド実行
    if args.command == 'get':
        success = get_xml_config(args.file)
    elif args.command == 'get-json':
        success = get_json_config_native(args.file)
    elif args.command == 'apply':
        success = apply_xml_config(args.file)
    elif args.command == 'apply-confirmed':
        # グローバルのタイムアウト値を更新
        COMMIT_CONFIRM_TIMEOUT = args.timeout
        success = apply_xml_config_confirmed(args.file)
    elif args.command == 'confirm':
        success = confirm_commit()
    elif args.command == 'cancel':
        success = cancel_commit()
    elif args.command == 'capability':
        success = show_capabilities(args.verbose)
    else:
        parser.print_help()
        return 0

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
