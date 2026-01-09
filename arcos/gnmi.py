#!/usr/bin/env python

"""
pygnmi を使った簡単なgNMIクライアント実装

【事前準備】
pip install pygnmi

"""

import argparse
import logging
import sys

try:
    from pygnmi.client import gNMIclient, telemetryParser
except ImportError:
    print(f"pygnmiをインストールしてください")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(host: str,
         port: int,
         username: str,
         password: str,
         sample_paths: list[str],
         on_change_paths: list[str]):

    try:
        with gNMIclient(target=(host, port),
                        username=username,
                        password=password,
                        insecure=True) as gc:

            logger.info(f"✅ ルータ {host}:{port} への接続に成功しました")

            # サブスクリプションリストを動的に生成
            subscriptions = []

            # SAMPLEモードのパスを追加
            for path in sample_paths:
                subscriptions.append({
                    'path': path,
                    'mode': 'sample',
                    'sample_interval': 30_000_000_000  # 30秒（ナノ秒）
                })

            # ON_CHANGEモードのパスを追加
            for path in on_change_paths:
                subscriptions.append({
                    'path': path,
                    'mode': 'on_change'
                })

            subscribe = {
                'subscription': subscriptions,
                'use_aliases': False,
                'mode': 'stream',
                'encoding': 'proto'
            }

            logger.info(f"サブスクリプション開始 (Ctrl+Cで終了)")
            logger.info(f"  SAMPLE paths: {sample_paths}")
            logger.info(f"  ON_CHANGE paths: {on_change_paths}")

            telemetry_stream = gc.subscribe(subscribe=subscribe)

            for telemetry_entry in telemetry_stream:
                parsed_data = telemetryParser(telemetry_entry)

                if 'update' in parsed_data:
                    timestamp = parsed_data['update'].get('timestamp', 'N/A')

                    for update in parsed_data['update'].get('update', []):
                        path = update.get('path', 'N/A')
                        value = update.get('val', 'N/A')

                        logger.info(f"時刻: {timestamp}, パス: {path}, 値: {value}")

    except KeyboardInterrupt:
        logger.info("\n🛑 ユーザーによって処理が中断されました (Ctrl+C)")
    except Exception as e:
        logger.error(f"🚨 接続またはデータ取得中にエラーが発生しました: {e}")
    finally:
        logger.info("✅ プログラムを終了します")


def parse_args():
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
        description='gNMI テレメトリクライアント（pygnmi使用）',
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
        default=9339,
        help='gNMIポート番号（デフォルト: 9339）'
    )

    parser.add_argument(
        '--username',
        default='cisco',
        help='認証ユーザ名（デフォルト: cisco）'
    )

    parser.add_argument(
        '--password',
        default='cisco123',
        help='認証パスワード（デフォルト: cisco123）'
    )

    parser.add_argument(
        '--sample-path',
        action='append',
        dest='sample_paths',
        help='SAMPLEモードで監視するパス（複数指定可）'
    )

    parser.add_argument(
        '--on-change-path',
        action='append',
        dest='on_change_paths',
        help='ON_CHANGEモードで監視するパス（複数指定可）'
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
    sample_paths = args.sample_paths or [
        '/interfaces/interface[name=swp1]/state/counters/in-octets',
        '/interfaces/interface[name=swp1]/state/counters/out-octets'
    ]

    # ON_CHANGEモードのパス設定(指定がなければデフォルト値を設定)
    on_change_paths = args.on_change_paths or [
        '/interfaces/interface[name=swp1]/state/oper-status'
    ]

    main(
        host=args.host[0],
        port=args.port,
        username=args.username,
        password=args.password,
        sample_paths=sample_paths,
        on_change_paths=on_change_paths
    )
