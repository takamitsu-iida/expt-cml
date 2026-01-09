#!/usr/bin/env python

"""
pygnmi を使った簡単なgNMIクライアント実装

【事前準備】
pip install pygnmi

"""

import argparse
import logging
import sys
from typing import Any

try:
    from pygnmi.client import gNMIclient, telemetryParser
except ImportError:
    print(f"pygnmiをインストールしてください")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定数定義
DEFAULT_PORT = 9339
DEFAULT_USERNAME = 'cisco'
DEFAULT_PASSWORD = 'cisco123'
SAMPLE_INTERVAL_NS = 30_000_000_000  # 30秒をナノ秒で表現
DEFAULT_SAMPLE_PATHS = [
    '/interfaces/interface[name=swp1]/state/counters/in-octets',
    '/interfaces/interface[name=swp1]/state/counters/out-octets'
]
DEFAULT_ON_CHANGE_PATHS = [
    '/interfaces/interface[name=swp1]/state/oper-status'
]


def create_subscription_list(sample_paths: list[str],
                              on_change_paths: list[str]) -> dict[str, Any]:
    """
    gNMI購読設定を生成する

    Args:
        sample_paths: SAMPLEモードで監視するパスのリスト
        on_change_paths: ON_CHANGEモードで監視するパスのリスト

    Returns:
        gNMI購読設定の辞書
    """
    subscriptions = []

    # SAMPLEモードのパスを追加
    for path in sample_paths:
        subscriptions.append({
            'path': path,
            'mode': 'sample',
            'sample_interval': SAMPLE_INTERVAL_NS
        })

    # ON_CHANGEモードのパスを追加
    for path in on_change_paths:
        subscriptions.append({
            'path': path,
            'mode': 'on_change'
        })

    return {
        'subscription': subscriptions,
        'use_aliases': False,
        'mode': 'stream',
        'encoding': 'proto'
    }


def process_telemetry_data(telemetry_entry: dict[str, Any]) -> None:
    """
    テレメトリデータを解析してログ出力する

    Args:
        telemetry_entry: pygnmiから受信したテレメトリデータ
    """
    parsed_data = telemetryParser(telemetry_entry)

    if 'update' not in parsed_data:
        return

    timestamp = parsed_data['update'].get('timestamp', 'N/A')

    for update in parsed_data['update'].get('update', []):
        path = update.get('path', 'N/A')
        value = update.get('val', 'N/A')
        logger.info(f"時刻: {timestamp}, パス: {path}, 値: {value}")


def main(host: str,
         port: int,
         username: str,
         password: str,
         sample_paths: list[str],
         on_change_paths: list[str]) -> None:
    """
    gNMIクライアントを起動してテレメトリデータを受信する

    Args:
        host: ルータのホスト名またはIPアドレス
        port: gNMIポート番号
        username: 認証ユーザ名
        password: 認証パスワード
        sample_paths: SAMPLEモードで監視するパスのリスト
        on_change_paths: ON_CHANGEモードで監視するパスのリスト
    """
    try:
        with gNMIclient(target=(host, port),
                        username=username,
                        password=password,
                        insecure=True) as gc:

            logger.info(f"✅ ルータ {host}:{port} への接続に成功しました")

            # サブスクリプション設定を生成
            subscribe = create_subscription_list(sample_paths, on_change_paths)

            logger.info(f"サブスクリプション開始 (Ctrl+Cで終了)")
            logger.info(f"  SAMPLE paths ({len(sample_paths)}件): {sample_paths}")
            logger.info(f"  ON_CHANGE paths ({len(on_change_paths)}件): {on_change_paths}")

            telemetry_stream = gc.subscribe(subscribe=subscribe)

            for telemetry_entry in telemetry_stream:
                process_telemetry_data(telemetry_entry)

    except KeyboardInterrupt:
        logger.info("\n🛑 ユーザーによって処理が中断されました (Ctrl+C)")
    except ConnectionError as e:
        logger.error(f"🚨 ルータへの接続に失敗しました: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"🚨 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("✅ プログラムを終了します")


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする"""

    epilog = \
"""
使用例:
  # 単一ルータへの接続
  %(prog)s --host 192.168.254.1 --username cisco --password cisco123

  # カスタムパス指定
  %(prog)s --host 192.168.254.1 --username cisco --password cisco123 \\
           --sample-path '/interfaces/interface[name=swp2]/state/counters/in-octets' \\
           --on-change-path '/interfaces/interface[name=swp2]/state/oper-status'
"""
    parser = argparse.ArgumentParser(
        description='gNMI テレメトリクライアント(pygnmi使用)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )

    parser.add_argument(
        '--host',
        nargs='+',
        required=True,
        help='ルータのホスト名またはIPアドレス'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help=f'gNMIポート番号(デフォルト: {DEFAULT_PORT})'
    )

    parser.add_argument(
        '--username',
        default=DEFAULT_USERNAME,
        help=f'認証ユーザ名(デフォルト: {DEFAULT_USERNAME})'
    )

    parser.add_argument(
        '--password',
        default=DEFAULT_PASSWORD,
        help=f'認証パスワード(デフォルト: {DEFAULT_PASSWORD})'
    )

    parser.add_argument(
        '--sample-path',
        action='append',
        dest='sample_paths',
        help='SAMPLEモードで監視するパス(複数指定可)'
    )

    parser.add_argument(
        '--on-change-path',
        action='append',
        dest='on_change_paths',
        help='ON_CHANGEモードで監視するパス(複数指定可)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='デバッグログを有効化'
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    # デバッグモード設定
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # SAMPLEモードのパス設定(指定がなければデフォルト値を設定)
    sample_paths = args.sample_paths or DEFAULT_SAMPLE_PATHS

    # ON_CHANGEモードのパス設定(指定がなければデフォルト値を設定)
    on_change_paths = args.on_change_paths or DEFAULT_ON_CHANGE_PATHS

    main(
        host=args.host[0],
        port=args.port,
        username=args.username,
        password=args.password,
        sample_paths=sample_paths,
        on_change_paths=on_change_paths
    )
