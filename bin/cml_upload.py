#!/usr/bin/env python

#
# virl2_clientを使ってノード定義ファイル、イメージ定義ファイルをCMLにアップロードするスクリプトです
#
# 使い方の例:
# python3 bin/cml_upload.py \
#   --node-def ./data/node_definition.yaml \
#   --image-def ./data/image_definition.yaml \
#   --image-file ./data/image_file.tar.gz

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = 'create openfabric docker lab'

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
    import yaml  # PyYAML
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

    def is_exist_image_def(client: ClientLibrary, image_def_name: str) -> bool:
        image_defs = client.definitions.image_definitions()
        image_def_ids = [img['id'] for img in image_defs]
        if image_def_name not in image_def_ids:
            logger.error(f"Specified image definition '{image_def_name}' not found in CML.")
            return False
        return True

    def is_exist_node_def(client: ClientLibrary, node_def_name: str) -> bool:
        node_defs = client.definitions.node_definitions()
        node_def_ids = [node['id'] for node in node_defs]
        if node_def_name not in node_def_ids:
            logger.error(f"Specified node definition '{node_def_name}' not found in CML.")
            return False
        return True


    def main() -> int:

        # 引数処理
        parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
        parser.add_argument('--node-def', type=str, help='ノード定義ファイルのパス')
        parser.add_argument('--image-def', type=str, help='イメージ定義ファイルのパス')
        parser.add_argument('--image-file', type=str, help='イメージファイル（tar.gzなど）のパス')

        args = parser.parse_args()

        # 引数が一つも指定されていない場合はヘルプを表示して終了
        if not any([args.node_def, args.image_def, args.image_file]):
            parser.print_help()
            return 0

        # CMLに接続する
        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

        # 接続を待機する
        client.is_system_ready(wait=True)

        # ノード定義ファイルのアップロード
        if args.node_def:
            node_path = Path(args.node)
            if not node_path.exists():
                logger.error(f"ノード定義ファイルが見つかりません: {node_path}")
                return 1
            with open(node_path, "r", encoding="utf-8") as f:
                node_def_text = f.read()
            # YAMLに変換
            node_def = yaml.safe_load(node_def_text)

            need_update = is_exist_node_def(client, node_path.stem)

            logger.info(f"ノード定義ファイル {node_path} をアップロードします")
            client.definitions.upload_node_definition(node_def, update=need_update)
            logger.info(f"ノード定義ファイル {node_path} をアップロードしました")


        # イメージ定義ファイルのアップロード
        if args.image_def:
            image_def_path = Path(args.image_def)
            if not image_def_path.exists():
                logger.error(f"イメージ定義ファイルが見つかりません: {image_def_path}")
                return 1
            with open(image_def_path, "r", encoding="utf-8") as f:
                image_def = f.read()
            logger.info(f"イメージ定義ファイル {image_def_path} をアップロードします")
            client.definitions.upload_image_definition(image_def, update=False)
            logger.info(f"イメージ定義ファイル {image_def_path} をアップロードしました")

        # イメージファイル（tar.gzなど）のアップロード
        if args.image_file:
            image_file_path = Path(args.image_file)
            if not image_file_path.exists():
                logger.error(f"イメージファイルが見つかりません: {image_file_path}")
                return 1
            logger.info(f"イメージファイル {image_file_path} をアップロードします")
            client.definitions.upload_image_file(filename=image_file_path)
            logger.info(f"イメージファイル {image_file_path} をアップロードしました")

        return 0


    # 実行
    sys.exit(main())
