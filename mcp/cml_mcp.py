#!/usr/bin/env python

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = "Simple MCP Server for Cisco Modeling Labs (CML)"

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

    # Python SDKの場合
    # from mcp.server.fastmcp import FastMCP

    # FastMCPの場合
    from fastmcp import FastMCP
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


def get_lab_titles() -> list[str]:
    try:
        client = ClientLibrary(CML_ADDRESS, CML_USERNAME, CML_PASSWORD, ssl_verify=False)
    except Exception as e:
        logger.error(f"CMLへの接続に失敗しました: {e}")
        return []
    labs = client.all_labs()
    return [lab.title for lab in labs] if labs else []


def get_lab_by_title(lab_title: str) -> Lab | None:
    try:
        client = ClientLibrary(CML_ADDRESS, CML_USERNAME, CML_PASSWORD, ssl_verify=False)
    except Exception as e:
        logger.error(f"CMLへの接続に失敗しました: {e}")
        return None
    labs = client.find_labs_by_title(lab_title)
    lab = labs[0] if labs else None
    if not lab:
        logger.error(f"ラボ '{lab_title}' が見つかりません")
        return None
    return lab


def get_lab_status_by_title(lab_title: str) -> str:
    lab = get_lab_by_title(lab_title)
    if not lab:
        return "NOT FOUND"
    return lab.state()


def get_node_labels(lab_title: str) -> list[str]:
    lab = get_lab_by_title(lab_title)
    if not lab:
        return None

    nodes = lab.nodes()
    return [node.label for node in nodes] if nodes else []


def get_node_by_label(lab: Lab, node_label: str):
    if lab.state() != 'STARTED':
        logger.error(f"ラボ '{lab.title()}' は起動していません")
        return None

    try:
        node = lab.get_node_by_label(node_label)
    except Exception as e:
        logger.error(f"ノード '{node_label}' が見つかりません: {e}")
        return None

    return node


def run_command_on_device(lab_title: str, node_label: str, command: str) -> str | None:
    """Run a command on the device in exec mode.
    """
    lab = get_lab_by_title(lab_title)
    if not lab:
        return None

    node = get_node_by_label(lab, node_label)
    if not node:
        return None

    try:
        lab.pyats.sync_testbed(CML_USERNAME, CML_PASSWORD)
    except Exception as e:
        logger.error(f"pyATS testbedの同期に失敗しました: {e}")
        return None

    try:
        result = node.run_pyats_command(command)
    except Exception as e:
        logger.error(f"コマンドの実行に失敗しました: {e}")
        return None

    return result


def run_config_command_on_device(lab_title: str, node_label: str, command: str) -> str | None:
    """Run a command on the device in configure mode.
    """
    lab = get_lab_by_title(lab_title)
    if not lab:
        return None

    node = lab.get_node_by_label(node_label)
    if not node:
        return None

    try:
        lab.pyats.sync_testbed(CML_USERNAME, CML_PASSWORD)
    except Exception as e:
        logger.error(f"pyATS testbedの同期に失敗しました: {e}")
        return None

    try:
        result = node.run_pyats_config_command(command)
    except Exception as e:
        logger.error(f"コンフィグコマンドの実行に失敗しました: {e}")
        return None

    return result


if __name__ == "__main__":

    #
    # MCPサーバ初期化
    #
    mcp = FastMCP(SCRIPT_DESCRIPTION)

    # グローバルなスレッドプールを1つだけ用意
    thread_pool_executor = concurrent.futures.ThreadPoolExecutor()

    @mcp.tool()
    async def get_lab_titles_async() -> list[str]:
        """
        CMLに登録されているラボの一覧をタイトルのリストとして返却します。

        Returns:
            ラボのタイトルのリスト
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool_executor,
            get_lab_titles
        )


    @mcp.tool()
    async def get_node_labels_async(lab_title: str) -> list[str] | None:
        """
        引数で指定したタイトルのラボに含まれるノードの一覧をラベルのリストとして返却します。
        ラボが見つからない場合はNoneを返します。

        Args:
            lab_title: ラボのタイトル

        Returns:
            ノードのラベルのリスト（list）またはNone
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool_executor,
            get_node_labels,
            lab_title
        )


    @mcp.tool()
    async def get_lab_status_async(lab_title: str) -> str:
        """
        引数で指定したタイトルのラボの状態を取得して返却します。

        Args:
            lab_title: ラボのタイトル

        Returns:
            ラボの状態（str）
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool_executor,
            get_lab_status_by_title,
            lab_title
        )


    @mcp.tool()
    async def run_command_on_device_async(lab_title: str, node_label: str, command: str) -> str | None:
        """
        引数で指定したノードにおいて、コマンドを実行し、応答を返却します。設定を変更するコマンドは実行できません。

        Args:
            lab_title: ラボのタイトル
            node_label: ノードのラベル
            command: 実行するコマンド

        Returns:
            コマンドの実行結果（str）またはNone
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool_executor,
            run_command_on_device,
            lab_title,
            node_label,
            command
        )


    @mcp.tool()
    async def run_config_command_on_device_async(lab_title: str, node_label: str, command: str) -> str | None:
        """
        引数で指定したノードにおいて、コンフィグコマンドを実行し、実行結果を返します。

        Args:
            lab_title: ラボのタイトル
            node_label: ノードのラベル
            command: 実行するコンフィグコマンド

        Returns:
            コマンドの実行結果（str）またはNone
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool_executor,
            run_config_command_on_device,
            lab_title,
            node_label,
            command
        )


    def main() -> int:
        # 引数処理
        parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
        parser.add_argument("--run", nargs=3, metavar=("LAB", "DEVICE", "COMMAND"), help="指定デバイスでコマンドを実行")
        parser.add_argument("--titles", action='store_true', default=False, help="ラボタイトル一覧を表示")
        args = parser.parse_args()

        # テスト用　コマンドを実行
        if args.run:
            lab_title, node_label, command = args.run
            result = run_command_on_device(lab_title, node_label, command)
            print(result)
            sys.exit(0)

        # テスト用　ラボタイトル一覧を表示
        if args.titles:
            titles = get_lab_titles()
            print(titles)
            sys.exit(0)

        # MCPサーバ起動
        mcp.run(transport="stdio")


    # 実行
    main()