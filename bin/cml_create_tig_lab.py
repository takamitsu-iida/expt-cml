#!/usr/bin/env python

#
# virl2_clientを使ってラボを作成するスクリプトです
# TIG(Docker)ノードを一つ作成します
#

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_NAME = "tig"

# ノード定義
NODE_DEFINITION = "tig"

# イメージ定義
IMAGE_DEFINITION = "tig"

# ノードにつけるタグ
NODE_TAG = "serial:7000"

# TIG(Docker)イメージに設定するboot.sh
BOOT_SH = """
# eth0 --- bridge1
ip address add dev eth0 192.168.0.110/24
ip link set dev eth0 up
# eth1
ip address add dev eth1 192.168.254.110/24
ip link set dev eth1 up
ip route add default via 192.168.254.1 dev eth1
#
# keep the next line to indicate that the machine is ready
echo "READY" >/dev/console
exit 0
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
    from virl2_client import ClientLibrary
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# CMLに接続するための情報を取得する
#

# 環境変数が設定されている場合はそれを使用し、設定されていない場合はローカルファイルから読み込む
CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL2_HOST")
CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

if not all([CML_ADDRESS, CML_USERNAME, CML_PASSWORD]):
    # ローカルファイルから読み込み
    try:
        from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD
    except ImportError as e:
        logging.critical("CML connection info not found")
        logging.critical("Please set environment variables or create cml_config.py")
        sys.exit(-1)


# このファイルへのPathオブジェクト
app_path = Path(__file__)

# このファイルの名前から拡張子を除いてプログラム名を得る
app_name = app_path.stem

# アプリケーションのホームディレクトリはこのファイルからみて一つ上
app_home = app_path.parent.joinpath('..').resolve()

# データ用ディレクトリ
data_dir = app_home.joinpath('data')

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

    def main():

        # 引数処理
        parser = argparse.ArgumentParser(description='create lab')
        parser.add_argument('-d', '--delete', action='store_true', default=False, help='Delete lab')
        args = parser.parse_args()

        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 同タイトルのラボを消す
        for lab in client.find_labs_by_title(LAB_NAME):
            lab.stop(wait=True)
            lab.wipe()
            logger.info(f"Deleting existing lab: {lab.title}")
            client.remove_lab(lab)

        # -d で起動していたらここで処理終了
        if args.delete:
            return 0

        # 指定されたimage_definitionが存在するか確認して、なければ終了する
        image_defs = client.definitions.image_definitions()
        image_def_ids = [img['id'] for img in image_defs]
        if IMAGE_DEFINITION not in image_def_ids:
            logger.error(f"Specified image definition '{IMAGE_DEFINITION}' not found in CML.")
            return 1

        # ラボを新規作成
        lab = client.create_lab(title=LAB_NAME)

        # 外部接続用のブリッジを作る
        ext_conn_node = lab.create_node("bridge1", "external_connector", x=0, y=0)

        # デフォルトはNATとして動作するので、これを"bridge1"に変更する
        # bridge1は追加したブリッジで、インターネット接続はない
        # このLANに足を出せば、母艦のWindows11の他、別のラボの仮想マシンであっても通信できる
        ext_conn_node.configuration = "bridge1"

        # tigのインスタンスを作る
        tig_node = lab.create_node(label="tig", node_definition="tig", x=0, y=200)

        # 起動イメージを指定する
        tig_node.image_definition = IMAGE_DEFINITION

        # インタフェースを作成する
        for _ in range(2):
            tig_node.create_interface(_, wait=True)

        # ブリッジとtigを接続する
        lab.connect_two_nodes(ext_conn_node, tig_node)

        # 設定ファイル一式
        tig_configurations = [
            {
                'name': 'boot.sh',
                'content': BOOT_SH
            }
        ]

        # 設定を適用する
        tig_node.configuration = tig_configurations

        # タグを設定する
        tig_node.add_tag(tag=NODE_TAG)

        #
        # IOLを作成する
        #
















        #
        # アノテーションを作成する
        #
        lab.create_annotation('rectangle', **{
            'border_color': '#808080FF',
            'border_radius': 0,
            'border_style': '',
            'color': '#FFFFFFFF',
            'rotation': 0,
            'thickness': 1,
            'x1': -40.0,
            'y1': -40.0,
            'x2': 80.0,
            'y2': 40.0,
            'z_index': 1
        })

        text_content = "Hyper-Vホスト\n192.168.0.198"
        lab.create_annotation('text', **{
            'border_color': '#00000000',
            'border_style': '',
            'rotation': 0,
            'text_bold': False,
            'text_content': text_content,
            'text_font': 'monospace',
            'text_italic': False,
            'text_size': 12,
            'text_unit': 'pt',
            'thickness': 1,
            'x1': -40.0,
            'y1': -90.0,
            'z_index': 0
        })

        text_content = "192.168.0.110/24"
        lab.create_annotation('text', **{
            'border_color': '#00000000',
            'border_style': '',
            'rotation': 0,
            'text_bold': False,
            'text_content': text_content,
            'text_font': 'monospace',
            'text_italic': False,
            'text_size': 12,
            'text_unit': 'pt',
            'thickness': 1,
            'x1': 40.0,
            'y1': 140.0,
            'z_index': 0
        })

        text_content = "InfluxDB http://192.168.0.110:8086\nGrafana http://192.16.0.110:3000"
        lab.create_annotation('text', **{
            'border_color': '#00000000',
            'border_style': '',
            'rotation': 0,
            'text_bold': False,
            'text_content': text_content,
            'text_font': 'monospace',
            'text_italic': False,
            'text_size': 12,
            'text_unit': 'pt',
            'thickness': 1,
            'x1': 40.0,
            'y1': 180.0,
            'z_index': 0
        })



        # start the lab
        # lab.start(wait=True)

        return 0

    # 実行
    sys.exit(main())
