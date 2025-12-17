#!/usr/bin/env python
# -*- coding: utf-8 -*-

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = 'netconfで装置から設定を取得・反映するツール'

import argparse
import os
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom
import time # timeモジュールを追加

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

# --- 新しい定数 ---
# confirm-timeout のデフォルト値 (秒)
# この時間内に次のコミットがない場合にロールバックされます
COMMIT_CONFIRM_TIMEOUT = 120 # 2分

def connect_netconf():
    """NETCONF接続を確立するヘルパー関数"""
    print(f"➡️ NETCONF接続を試行中: {TARGET_HOST}:{TARGET_PORT} (ユーザー: {TARGET_USER})")
    try:
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
        return conn
    except AuthenticationError:
        print("❌ 認証エラー: ユーザー名またはパスワードが正しくありません。")
        return None
    except TransportError as e:
        print(f"❌ 接続/トランスポートエラーが発生しました: {e}")
        return None
    except Exception as e:
        print(f"❌ 致命的なエラーが発生しました: {e}")
        return None


def get_xml_config(config_file: str = OUTPUT_FILE):
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
                # ルート要素でラップしてprettifyし、その後ルート要素を削除する
                wrapped_config = f'<root>{''.join(config_elements)}</root>'
                dom_formatted = xml.dom.minidom.parseString(wrapped_config)
                xml_formatted = dom_formatted.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
                # XML宣言と <root> タグを削除
                lines = xml_formatted.split('\n')[1:]  # XML宣言削除
                lines = [line for line in lines if not line.strip().startswith('<root') and not line.strip().startswith('</root')]
                xml_formatted = '\n'.join(lines).strip()
            else:
                # <data>要素が空の場合、そのまま空の文字列をセット
                xml_formatted = ""

        except Exception as e:
            print(f"⚠️ XMLフォーマット失敗、元の形式で保存します: {e}")
            xml_formatted = xml_output

        # XMLをファイルに保存
        os.makedirs(os.path.dirname(config_file) or '.', exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(xml_formatted)

        print(f"✅ XML設定を保存しました: {config_file}")

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


def apply_xml_config_confirmed(config_file: str = OUTPUT_FILE):
    """
    保存したXML設定ファイルをNETCONFで装置に反映させる (confirmed commitを使用)

    Args:
        config_file: 反映させるXML設定ファイルのパス

    Returns:
        bool: 成功時True、失敗時False
    """
    conn = connect_netconf()
    if not conn:
        return False

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

        # --- 設定を装置に反映 (<edit-config> を実行) ---
        print(f"\n➡️ <edit-config> RPCを送信中...")
        print(f"   設定ファイル: {config_file}")
        conn.edit_config(
            target='candidate',
            config=xml_config
        )
        print(f"✅ <edit-config>が成功しました (target=candidate)")

        # --- 変更内容を confirmed コミット ---
        print(f"\n➡️ <commit confirmed> RPCを送信中 (timeout: {COMMIT_CONFIRM_TIMEOUT}秒)...")
        conn.commit(confirmed=True, confirm_timeout=COMMIT_CONFIRM_TIMEOUT)
        print(f"✅ <commit confirmed>が成功しました。")
        print(f"⚠️ 設定は一時的に適用されました。{COMMIT_CONFIRM_TIMEOUT}秒以内に再度 'commit' コマンドを実行して変更を永続化してください。")
        print(f"   時間内に 'commit' が行われない場合、変更は自動的にロールバックされます。")
        print(f"   手動でロールバックするには 'cancel' コマンドを実行してください。")
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

def confirm_commit():
    """
    commit confirmedで保留中の変更を永続化する
    """
    conn = connect_netconf()
    if not conn:
        return False

    try:
        print(f"\n➡️ 保留中の変更を確定するため <commit> RPC を送信中...")
        conn.commit()
        print(f"✅ <commit>が成功しました。保留中の変更が永続化されました。")
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

def cancel_commit():
    """
    commit confirmedで保留中の変更をキャンセルする
    """
    conn = connect_netconf()
    if not conn:
        return False

    try:
        print(f"\n➡️ 保留中の変更をキャンセルするため <cancel-commit> RPC を送信中...")
        conn.cancel_commit()
        print(f"✅ <cancel-commit>が成功しました。保留中の変更はロールバックされました。")
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

    args = parser.parse_args()

    # 引数がなければhelpを表示
    if not args.command:
        parser.print_help()
        return 1 # エラーコード

    return_code = 0

    # get
    if args.command == 'get':
        success = get_xml_config(args.file)
        return_code = 0 if success else 1
    # apply-confirmed
    elif args.command == 'apply-confirmed':
        # グローバルのタイムアウト値を更新
        global COMMIT_CONFIRM_TIMEOUT
        COMMIT_CONFIRM_TIMEOUT = args.timeout
        success = apply_xml_config_confirmed(args.file)
        return_code = 0 if success else 1
    # confirm
    elif args.command == 'confirm':
        success = confirm_commit()
        return_code = 0 if success else 1
    # cancel
    elif args.command == 'cancel':
        success = cancel_commit()
        return_code = 0 if success else 1
    else:
        parser.print_help()
        return_code = 1

    return return_code


if __name__ == "__main__":
    sys.exit(main())
