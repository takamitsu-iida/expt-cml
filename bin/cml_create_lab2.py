#!/usr/bin/env python

#
# virl2_clientを使ってラボを作成するスクリプトです
# FRR(Docker)ノードを一つ作成します
#

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = 'create sample lab'

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_NAME = "cml_create_lab2"

# ノード定義
NODE_DEFINITION = "frr"

# イメージ定義 CML2.9に同梱のFRR(Docker)イメージ
IMAGE_DEFINITION = "frr-10-2-1-r1"

# ノードにつけるタグ
NODE_TAG = "serial:6000"

# FRR(Docker)イメージに設定するnode.cfgのJinja2テンプレート
FRR_NODE_CFG = """
! FRR Config generated on 2025-01-22 17:55
! just an example -- You need to need to change it
!
hostname frr-0
!
interface lo
    ip address 10.0.0.1/32
    ip ospf passive
!
interface eth0
    description to eth0.frr-1
    ip address 172.16.128.2/30
    no shutdown
interface eth1
    description to eth0.frr-2
    ip address 172.16.128.9/30
    no shutdown
interface eth2
    description not connected
    !no ip address
    shutdown
interface eth3
    description not connected
    !no ip address
    shutdown
!
router ospf
    ospf router-id 10.0.0.1
    network 10.0.0.1/32 area 10
    network 172.16.128.0/30 area 10
    network 172.16.128.8/30 area 10
!
end
"""

FRR_PROTOCOLS = """
# enable / disable needed routing protocols by adding / removing
# the hashmark in front of the lines below
#
bgpd
ospfd
ospf6d
ripd
ripngd
isisd
pimd
pim6d
ldpd
nhrpd
eigrpd
babeld
sharpd
pbrd
bfdd
fabricd
vrrpd
pathd
"""

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
        if state == 'STOPPED' or state == 'DEFINED_ON_CORE':
            logger.info(f"Starting lab '{LAB_NAME}'")
            lab.start(wait=True)
            logger.info(f"Lab '{LAB_NAME}' started")
        else:
            logger.info(f"Lab '{LAB_NAME}' is already running")


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

        # 指定されたimage_definitionが存在するか確認して、なければ終了する
        image_defs = client.definitions.image_definitions()
        image_def_ids = [img['id'] for img in image_defs]
        if IMAGE_DEFINITION not in image_def_ids:
            logger.error(f"Specified image definition '{IMAGE_DEFINITION}' not found in CML.")
            return

        # ラボを新規作成
        lab = client.create_lab(title=LAB_NAME)

        # 外部接続用のNATを作る
        ext_conn_node = lab.create_node(label="ext-conn-0", node_definition="external_connector", x=0, y=0)

        # frrのインスタンスを作る
        frr_node = lab.create_node(label="frr-0", node_definition="frr", x=0, y=200)

        # 起動イメージを指定する
        frr_node.image_definition = IMAGE_DEFINITION

        # NATとfrrを接続する
        lab.connect_two_nodes(ext_conn_node, frr_node)

        # FRRに設定するファイル一式
        frr_configurations = [
            {
                'name': 'node.cfg',
                'content': FRR_NODE_CFG
            },
            {
                'name': 'protocols',
                'content': FRR_PROTOCOLS
            }
        ]

        # FRRノードに設定を適用する
        frr_node.configuration = frr_configurations

        # タグを設定する
        # "serial:6000"
        frr_node.add_tag(tag=NODE_TAG)


    def main():

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
