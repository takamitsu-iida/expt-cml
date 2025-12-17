#!/usr/bin/env python
# -*- coding: utf-8 -*-

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = 'netconfで装置から設定を取得・反映するツール'

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

# --- 接続情報の設定 ---
TARGET_HOST = "192.168.254.1"
TARGET_PORT = 830
TARGET_USER = "cisco"
TARGET_PASS = "cisco123"

# running, candidate, startup
NETCONF_GET_CONFIG_SOURCE = 'running'

# 保存先ファイルパス
OUTPUT_DIR = "/tmp"
OUTPUT_FILE = f"{OUTPUT_DIR}/{TARGET_HOST}.xml"

def get_xml_config(config_file: str = OUTPUT_FILE):
    """
    NETCONFで装置から設定を取得し、ファイルに保存する

    Args:
        config_file: 保存先のXML設定ファイルパス

    Returns:
        bool: 成功時True、失敗時False
    """
    try:

        print(f"➡️ NETCONF接続を試行中: {TARGET_HOST}:{TARGET_PORT} (ユーザー: {TARGET_USER})")

        with manager.connect(
            host=TARGET_HOST,
            port=TARGET_PORT,
            username=TARGET_USER,
            password=TARGET_PASS,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=30
        ) as conn:

            print(f"✅ NETCONFセッションが確立されました。セッションID: {conn.session_id}")

            # --- データの取得 (<get-config> を実行) ---
            print(f"\n➡️ <get-config> RPCを送信中 (ソース: <{NETCONF_GET_CONFIG_SOURCE}>)...")

            result = conn.get_config(source=NETCONF_GET_CONFIG_SOURCE)

            xml_output = result.data_xml

            try:
                dom = xml.dom.minidom.parseString(xml_output)
                xml_formatted = dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
                # XML宣言を削除
                if xml_formatted.startswith('<?xml'):
                    xml_formatted = '\n'.join(xml_formatted.split('\n')[1:]).lstrip()

                # <data> 要素を削除し、その中身のみを抽出
                root = ET.fromstring(xml_output)

                # <data> 要素の子要素のみを抽出
                config_elements = []
                for child in root:
                    config_elements.append(ET.tostring(child, encoding='unicode'))

                if config_elements:
                    # 複数の要素を整形して保存
                    xml_formatted = '\n'.join(config_elements)
                    # 整形処理
                    dom_formatted = xml.dom.minidom.parseString(f'<root>{"".join(config_elements)}</root>')
                    xml_formatted = dom_formatted.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
                    # XML宣言と <root> タグを削除
                    lines = xml_formatted.split('\n')[1:]  # XML宣言削除
                    lines = [line for line in lines if not line.strip().startswith('<root') and not line.strip().startswith('</root')]
                    xml_formatted = '\n'.join(lines).strip()

            except Exception as e:
                print(f"⚠️ XMLフォーマット失敗、元の形式で保存します: {e}")
                xml_formatted = xml_output

            # XMLをファイルに保存
            os.makedirs(os.path.dirname(config_file) or '.', exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                # XML宣言を追加
                # f.write('<?xml version="1.0" encoding="UTF-8"?>\n')

                f.write(xml_formatted)

            print(f"✅ XML設定を保存しました: {config_file}")

            return True

        print("\n接続を閉じました。")

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
        return False
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
        return False
    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False


def apply_xml_config(config_file: str = OUTPUT_FILE):
    """
    保存したXML設定ファイルをNETCONFで装置に反映させる

    Args:
        config_file: 反映させるXML設定ファイルのパス

    Returns:
        bool: 成功時True、失敗時False
    """
    try:
        # ファイルの存在確認
        if not os.path.exists(config_file):
            print(f"❌ 設定ファイルが見つかりません: {config_file}")
            return False

        # XMLファイルを読み込む
        with open(config_file, 'r', encoding='utf-8') as f:
            xml_config_content = f.read()

        # ルート要素
        #   <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        # の中にXML形式のコンフィグを格納する
        xml_config = f'<nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">{xml_config_content}</nc:config>'

        print(f"➡️ NETCONF接続を試行中: {TARGET_HOST}:{TARGET_PORT} (ユーザー: {TARGET_USER})")

        with manager.connect(
            host=TARGET_HOST,
            port=TARGET_PORT,
            username=TARGET_USER,
            password=TARGET_PASS,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=30
        ) as conn:

            print(f"✅ NETCONFセッションが確立されました。セッションID: {conn.session_id}")

            # --- 設定を装置に反映 (<edit-config> を実行) ---
            print(f"\n➡️ <edit-config> RPCを送信中...")

            print(f"   設定ファイル: {config_file}")

            result = conn.edit_config(
                target='candidate',
                config=xml_config
            )

            print(f"✅ <edit-config>が成功しました")

            # --- 変更内容をコミット ---
            print(f"\n➡️ <commit> RPCを送信中...")

            result = conn.commit()

            print(f"✅ <commit>が成功しました。設定が装置に反映されました")
            return True

        print("\n接続を閉じました。")

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
        return False
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
        return False
    except RPCError as e:
        print(f"❌ NETCONF RPCエラーが発生しました: {e}")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False


def show_capabilities(verbose: bool = False):
    """
    NETCONFサーバのcapabilityを表示する

    Args:
        verbose: 詳細表示モード (デフォルト: False)

    Returns:
        bool: 成功時True、失敗時False
    """
    try:
        print(f"➡️ NETCONF接続を試行中: {TARGET_HOST}:{TARGET_PORT} (ユーザー: {TARGET_USER})")

        with manager.connect(
            host=TARGET_HOST,
            port=TARGET_PORT,
            username=TARGET_USER,
            password=TARGET_PASS,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=30
        ) as conn:

            print(f"✅ NETCONFセッションが確立されました。セッションID: {conn.session_id}")
            print(f"\n📋 サーバのCapabilities一覧 ({len(conn.server_capabilities)}件):\n")
            print("=" * 80)

            if verbose:
                # 詳細表示: 全Capability表示
                for i, capability in enumerate(sorted(conn.server_capabilities), start=1):
                    print(f"{i:3d}. {capability}")
            else:
                # 簡易表示: 主要なCapabilityのみ表示
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
                        # YANG モジュール
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

                # YANG Modules (重複排除して表示)
                if categories['YANG Modules']:
                    print(f"\n[YANG Modules] ({len(set(categories['YANG Modules']))}件)")
                    for module in sorted(set(categories['YANG Modules']))[:10]:
                        print(module)
                    if len(set(categories['YANG Modules'])) > 10:
                        print(f"  ... and {len(set(categories['YANG Modules'])) - 10} more modules")
                        print("  (--verbose オプションで全て表示)")

                # Operations
                if categories['Operations']:
                    print("\n[Operations]")
                    for cap in categories['Operations']:
                        print(f"  {cap}")

            print("\n" + "=" * 80)
            return True

    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
        return False
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
        return False
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return False


def main():

    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')

    # get コマンド
    get_parser = subparsers.add_parser('get', help='装置から設定を取得してファイルに保存')
    get_parser.add_argument(
        '-f', '--file',
        type=str,
        default=OUTPUT_FILE,
        help=f'保存先ファイルパス (デフォルト: {OUTPUT_FILE})'
    )

    # apply コマンド
    apply_parser = subparsers.add_parser('apply', help='ファイルから設定を読み込んで装置に反映')
    apply_parser.add_argument(
        '-f', '--file',
        type=str,
        default=OUTPUT_FILE,
        help=f'設定ファイルパス (デフォルト: {OUTPUT_FILE})'
    )

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
        return

    # get
    if args.command == 'get':
        success = get_xml_config(args.file)
        return 0 if success else 1

    # apply
    if args.command == 'apply':
        success = apply_xml_config(args.file)
        return 0 if success else 1

    # capability
    if args.command == 'capability':
        success = show_capabilities(args.verbose)
        return 0 if success else 1


if __name__ == "__main__":
    main()
