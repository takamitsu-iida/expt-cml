#!/usr/bin/env python

# MCPサーバの動作テスト用のクライアントスクリプトです

# テストするMCPサーバのスクリプトファイル名
MCP_SERVER_SCRIPT_NAME = "cml_mcp.py"

#
# 標準ライブラリのインポート
#

import asyncio
import logging
import sys

from pathlib import Path

#
# 外部ライブラリのインポート
#

try:
    from fastmcp import Client  #, FastMCP
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

try:
    from pyats.topology.loader.base import TestbedFileLoader as _PyatsTFLoader
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


# ローカルのPythonスクリプトを指定してクライアントを作成
client = Client(app_dir.joinpath(MCP_SERVER_SCRIPT_NAME))


async def main():
    # ここで接続が確立
    # コンテキスト内でMCP呼び出しを行う
    async with client:
        # Basic server interaction
        await client.ping()
        print(f"Client connected: {client.is_connected()}")

        tools = await client.list_tools()
        if tools:
            print("Available tools")
            for tool in tools:
                print(f"  name: {tool.name}")
        else:
            print(" No tools available")
            return

        if any(tool.name == "get_lab_titles_async" for tool in tools):
            result = await client.call_tool("get_lab_titles_async", {})
            print("Lab titles:")
            labs = result.structured_content.get('result', [])
            for lab in labs:
                print(f"  {lab}")

        if labs and any(tool.name == "get_node_labels_async" for tool in tools):
            print("Nodes in lab:")
            for lab_title in labs:
                result = await client.call_tool("get_node_labels_async", {"lab_title": lab_title})
                node_labels = result.structured_content.get('result', [])
                print(f"  '{lab_title}': {node_labels}")

        lab_title = "Docker FRR SRv6"
        tool_name = "run_ping_on_device_async"
        ce_routers = ["CE101", "CE102"]
        ping_results = {}
        if any(lab == lab_title for lab in labs) and any(tool.name == tool_name for tool in tools):
            print("Running ping tests...")
            for src in ce_routers:
                result = await client.call_tool(tool_name, {
                    "lab_title": lab_title,
                    "node_label": src,
                    "target": "10.0.14.104",
                    "repeat": 5
                })
                ping_output = result.structured_content.get('result', '')
                ping_results[src] = ping_output
                print(f"Ping from {src}: {ping_output}")

            print("Ping tests completed.")


    # ここで接続は自動的にクローズ
    print(f"Client connected: {client.is_connected()}")

if __name__ == "__main__":

    # 実行
    asyncio.run(main())
