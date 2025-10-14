#!/usr/bin/env python

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = "Simple pyATS MCP Server"

#
# 標準ライブラリのインポート
#
import argparse
import asyncio
import concurrent.futures
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
    from mcp.server.fastmcp import FastMCP
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

# 同じ場所に 'cml_env' ファイルがあればそれを優先する
env_path = app_dir.joinpath('cml_env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL_HOST")
CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

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

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimpleMCPServer")


def get_lab_by_title(client: ClientLibrary, title: str) -> Lab | None:
    labs = client.find_labs_by_title(title)
    return labs[0] if labs else None


def run_command_on_cml(lab_title: str, node_label: str, command: str) -> str | None:
    """Run a command on the device in exec mode"""

    try:
        client = ClientLibrary(CML_ADDRESS, CML_USERNAME, CML_PASSWORD, ssl_verify=False)
    except Exception as e:
        logger.error(f"CMLへの接続に失敗しました: {e}")
        return None

    lab = get_lab_by_title(client, lab_title)
    if not lab:
        logger.error(f"ラボ '{lab_title}' が見つかりません")
        return None

    state = lab.state()
    if state != 'STARTED':
        logger.error(f"ラボ '{lab_title}' は起動していません")
        return None

    try:
        node = lab.get_node_by_label(node_label)
    except Exception as e:
        logger.error(f"ノード '{node_label}' が見つかりません: {e}")
        return None

    lab.pyats.sync_testbed(CML_USERNAME, CML_PASSWORD)

    result = node.run_pyats_command(command)

    return result


def run_config_command_on_cml(lab_title: str, node_label: str, command: str) -> str | None:
    """Run a command on the device in configure mode"""
    try:
        client = ClientLibrary(CML_ADDRESS, CML_USERNAME, CML_PASSWORD, ssl_verify=False)
    except Exception as e:
        logging.error(f"CMLへの接続に失敗しました: {e}")
        return None

    lab = get_lab_by_title(client, lab_title)
    if not lab:
        logger.error(f"ラボ '{lab_title}' が見つかりません")
        return None

    state = lab.state()
    if state != 'STARTED':
        logger.error(f"ラボ '{lab_title}' は起動していません")
        return None

    try:
        node = lab.get_node_by_label(node_label)
    except Exception as e:
        logger.error(f"ノード '{node_label}' が見つかりません: {e}")
        return None

    lab.pyats.sync_testbed(CML_USERNAME, CML_PASSWORD)

    result = node.run_pyats_config_commands(command)

    return result


if __name__ == "__main__":

    #
    # MCPサーバ初期化
    #
    mcp = FastMCP(SCRIPT_DESCRIPTION)

    # グローバルなスレッドプールを1つだけ用意
    thread_pool_executor = concurrent.futures.ThreadPoolExecutor()

    @mcp.tool()
    async def run_command_on_cml_async(lab_name: str, node_name: str, command: str) -> str | None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool_executor,
            run_command_on_cml,
            lab_name,
            node_name,
            command
        )

    def main() -> int:
        # 引数処理
        parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
        parser.add_argument("--show", nargs=3, metavar=("LAB", "DEVICE", "COMMAND"), help="指定デバイスでshowコマンド実行")
        args = parser.parse_args()

        # テスト用
        if args.show:
            lab_name, device_name, command = args.show
            result = run_command_on_cml(lab_name, device_name, command)
            print(result)
            sys.exit(0)

        logger.info("MCPサーバを起動します")
        mcp.run(transport="stdio")


    # 実行
    main()