#!/usr/bin/env python


###########################################################

#
# 作成するラボの情報
#

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_NAME = "cml_create_lab1"

# ノード定義
NODE_DEFINITION = "ubuntu"

# イメージ定義
IMAGE_DEFINITION = "ubuntu-24-04-20250503"

# ノードにつけるタグ
NODE_TAG = "serial:6000"

# Ubuntuノードに与える初期設定のテンプレート
UBUNTU_CONFIG_FILENAME = "ubuntu_config.yaml.j2"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うホスト名
UBUNTU_HOSTNAME = "ubuntu-0"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うユーザ名
UBUNTU_USERNAME = "cisco"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うパスワード
UBUNTU_PASSWORD = "cisco"

###########################################################

#
# 標準ライブラリのインポート
#
import argparse
import logging
import sys
from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from jinja2 import Template
    from virl2_client import ClientLibrary
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# ローカルファイルからの読み込み
#
from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD

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

    def read_template_config(filename='') -> str:
        p = data_dir.joinpath(filename)
        try:
            with p.open() as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"{filename} not found")
            sys.exit(1)

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
            lab.stop()
            lab.wipe()
            lab.remove()

        # -d で起動していたらここで処理終了
        if args.delete:
            return 0

        # ラボを新規作成
        lab = client.create_lab(title=LAB_NAME)

        # 外部接続用のNATを作る
        ext_conn_node = lab.create_node(label="ext-conn-0", node_definition="external_connector", x=0, y=0)

        # ubuntuのインスタンスを作る
        ubuntu_node = lab.create_node(label=UBUNTU_HOSTNAME, node_definition="ubuntu", x=0, y=200)

        # 起動イメージを指定する
        ubuntu_node.image_definition = IMAGE_DEFINITION

        # 初期状態はインタフェースが存在しないので、追加する
        # Ubuntuのslot番号の範囲は0-7
        # slot番号はインタフェース名ではない
        # ens2-ens9が作られる
        for i in range(8):
            ubuntu_node.create_interface(i, wait=True)

        # NATとubuntuを接続する
        lab.connect_two_nodes(ext_conn_node, ubuntu_node)

        # Ubuntuに設定するcloud-init.yamlのJinja2テンプレートを取り出す
        template_config = read_template_config(filename=UBUNTU_CONFIG_FILENAME)

        # Jinja2のTemplateをインスタンス化する
        template = Template(template_config)

        # templateに渡すコンテキストオブジェクト
        context = {
            "HOSTNAME": UBUNTU_HOSTNAME,
            "USERNAME": UBUNTU_USERNAME,
            "PASSWORD": UBUNTU_PASSWORD,
        }

        # Ubuntuに設定するcloud-init.yamlのテキストを作る
        config_text = template.render(context)

        # ノードのconfigにcloud-init.yamlのテキストを設定する
        ubuntu_node.configuration = config_text

        # タグを設定する
        # "serial:6000"
        ubuntu_node.add_tag(tag=NODE_TAG)

        # start the lab
        lab.start()

        return 0

    # 実行
    sys.exit(main())
