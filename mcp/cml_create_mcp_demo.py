#!/usr/bin/env python

#
# virl2_clientを使ってMCPの動作テスト用のラボを作成します
#

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = 'create lab to test MCP'

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_NAME = "mcp demo"

###########################################################

r1_config = """
!
hostname R1
!
no ip domain lookup
!
interface Loopback0
 ip address 192.168.255.1 255.255.255.255
 ip router isis 1
!
interface Ethernet0/0
 ip unnumbered Loopback0
 ip router isis 1
 isis network point-to-point
!
interface Ethernet0/1
 ip unnumbered Loopback0
 ip router isis 1
 isis network point-to-point
!
router isis 1
 net 49.0000.0000.0000.0001.00
 router-id Loopback0
 metric-style wide
!
""".strip()

r2_config = """
!
hostname R2
!
no ip domain lookup
!
interface Loopback0
 ip address 192.168.255.2 255.255.255.255
 ip router isis 1
!
interface Ethernet0/0
 ip unnumbered Loopback0
 ip router isis 1
 isis network point-to-point
!
interface Ethernet0/1
 ip unnumbered Loopback0
 ip router isis 1
 isis network point-to-point
!
router isis 1
 net 49.0000.0000.0000.0002.00
 router-id Loopback0
 metric-style wide
!
""".strip()

###########################################################

#
# 標準ライブラリのインポート
#
import argparse
import logging
import os
import sys
from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from dotenv import load_dotenv

    # SSL Verification disabled のログが鬱陶しいので、ERRORのみに抑制
    logging.getLogger("virl2_client.virl2_client").setLevel(logging.ERROR)
    from virl2_client import ClientLibrary
    from virl2_client.models.lab import Lab
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

# このファイルへのPathオブジェクト
app_path = Path(__file__)

# このファイルがあるディレクトリ
app_dir = app_path.parent

# このファイルの名前から拡張子を除いてプログラム名を得る
app_name = app_path.stem

# アプリケーションのホームディレクトリはこのファイルからみて一つ上
app_home = app_path.parent.joinpath('..').resolve()

#
# CMLに接続するための情報を取得する
#

# まず環境変数を取得
CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL_HOST")
CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

# 環境変数が未設定ならcml_envファイルから読み取る
if not all([CML_ADDRESS, CML_USERNAME, CML_PASSWORD]):
    env_path = app_dir.joinpath('cml_env')
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL_HOST")
        CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
        CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

# 接続情報を得られなかったら終了
if not all([CML_ADDRESS, CML_USERNAME, CML_PASSWORD]):
    logging.critical("CML connection info not found in environment variables or cml_env file")
    sys.exit(-1)

#
# ログ設定
#

# ログファイルの名前
log_file = app_path.with_suffix('.log').name

# ログファイルを置くディレクトリ
log_dir = app_home.joinpath('log')
log_dir.mkdir(exist_ok=True)

# ログファイルのパス
log_path = log_dir.joinpath(log_file)

# ロギングの設定
# レベルはこの順で下にいくほど詳細になる
#   logging.CRITICAL
#   logging.ERROR
#   logging.WARNING --- 初期値はこのレベル
#   logging.INFO
#   logging.DEBUG
#
# ログの出力方法
# logger.debug('debugレベルのログメッセージ')
# logger.info('infoレベルのログメッセージ')
# logger.warning('warningレベルのログメッセージ')

# 独自にロガーを取得するか、もしくはルートロガーを設定する

# ルートロガーを設定する場合
# logging.basicConfig()

# 独自にロガーを取得する場合
logger = logging.getLogger(__name__)

# 参考
# ロガーに特定の名前を付けておけば、後からその名前でロガーを取得できる
# logging.getLogger("main.py").setLevel(logging.INFO)

# ログレベル設定
logger.setLevel(logging.INFO)

# フォーマット
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 標準出力へのハンドラ
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

# ログファイルのハンドラ
file_handler = logging.FileHandler(log_path, 'a+')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

#
# ここからスクリプト
#
if __name__ == '__main__':

    def get_lab_by_title(client: ClientLibrary, title: str) -> Lab | None:
        labs = client.find_labs_by_title(title)
        return labs[0] if labs else None


    def start_lab(lab: Lab) -> None:
        state = lab.state()  # STARTED / STOPPED / DEFINED_ON_CORE
        if state == 'STARTED':
            logger.info(f"Lab '{LAB_NAME}' is already running")
            return
        else:
            logger.info(f"Starting lab '{LAB_NAME}'")
            lab.start(wait=True)
            logger.info(f"Lab '{LAB_NAME}' started")


    def stop_lab(lab: Lab) -> None:
        state = lab.state()  # STARTED / STOPPED / DEFINED_ON_CORE
        if state == 'STARTED':
            logger.info(f"Stopping lab '{LAB_NAME}'")
            lab.stop(wait=True)
            logger.info(f"Lab '{LAB_NAME}' stopped")
        else:
            logger.info(f"Lab '{LAB_NAME}' is not running")


    def delete_lab(lab: Lab) -> None:
        logger.info(f"Deleting lab '{LAB_NAME}'")
        stop_lab(lab)
        lab.wipe()
        lab.remove()
        logger.info(f"Lab '{LAB_NAME}' deleted")


    def create_lab(client: ClientLibrary) -> None:

        # ラボを新規作成
        lab = client.create_lab(title=LAB_NAME)

        # R1とR2を作成する
        r1_node = lab.create_node(label="R1", node_definition="iol-xe", x=-560, y=-40)
        r2_node = lab.create_node(label="R2", node_definition="iol-xe", x=-360, y=-40)

        # IOLの場合はイメージ定義は存在しない
        r1_node.image_definition = None
        r2_node.image_definition = None

        # インタフェースを作る
        for i in range(4):
            r1_node.create_interface(i, wait=True)
            r2_node.create_interface(i, wait=True)

        # ルータ間を接続する
        lab.connect_two_nodes(r1_node, r2_node)
        lab.connect_two_nodes(r1_node, r2_node)

        # ルータ設定
        r1_node.configuration = [
            {
                'name': "ios_config.txt",
                'content': r1_config
            }
        ]
        r2_node.configuration = [
            {
                'name': "ios_config.txt",
                'content': r2_config
            }
        ]

        # タグをつける
        r1_node.add_tag("serial:5001")
        r2_node.add_tag("serial:5002")


    def main() -> None:

        # 引数処理
        parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
        parser.add_argument('--create', action='store_true', default=False, help='Create lab')
        parser.add_argument('--delete', action='store_true', default=False, help='Delete lab')
        parser.add_argument('--stop', action='store_true', default=False, help='Stop lab')
        parser.add_argument('--start', action='store_true', default=False, help='Start lab')
        parser.add_argument('--testbed', action='store_true', default=False, help='Show pyATS testbed')  # --- IGNORE ---
        args = parser.parse_args()

        # 引数が何も指定されていない場合はhelpを表示して終了
        if not any(vars(args).values()):
            parser.print_help()
            return

        # CMLを操作するvirl2_clientをインスタンス化
        try:
            client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)
        except Exception as e:
            logger.critical(f"Failed to connect to CML at {CML_ADDRESS}")
            logger.critical(str(e))
            return

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 既存のラボがあれば取得する
        lab = get_lab_by_title(client, LAB_NAME)

        if args.start:
            start_lab(lab) if lab else logger.error(f"Lab '{LAB_NAME}' not found")
            return

        if args.stop:
            stop_lab(lab) if lab else logger.error(f"Lab '{LAB_NAME}' not found")
            return

        if args.delete:
            delete_lab(lab) if lab else logger.error(f"Lab '{LAB_NAME}' not found")
            return

        if args.testbed:
            print(lab.get_pyats_testbed()) if lab else logger.error(f"Lab '{LAB_NAME}' not found")
            return

        if args.create:
            # 既存のラボがあれば削除する
            if lab:
                logger.info(f"Lab '{LAB_NAME}' already exists")
                delete_lab(lab)
            create_lab(client)

    #
    # 実行
    #
    main()
