#!/usr/bin/env python

# MCPサーバのスクリプト
MCP_SERVER_SCRIPT = "cml_mcp.py"

#
# 標準ライブラリのインポート
#

import asyncio
import asyncio
import logging
import sys

from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from mcp.server.fastmcp import Client
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



client = Client(MCP_SERVER_SCRIPT)

async def main():
    # ここで接続が確立
    async with client:
        print(f"Client connected: {client.is_connected()}")

        # コンテキスト内でMCP呼び出しを行う
        tools = await client.list_tools()
        print(f"Available tools: {tools}")

        if any(tool.name == "get_lab_titles_async" for tool in tools):
            labs = await client.call_tool("get_lab_titles_async", {})
            print(f"Get lab titles result: {labs}")

        if labs and any(tool.name == "get_node_labels_async" for tool in tools):
            for lab_title in labs:
                node_labels = await client.call_tool("get_node_labels_async", {"lab_title": lab_title})
                print(f"Node labels in lab '{lab_title}': {node_labels}")

    # ここで接続は自動的にクローズ
    print(f"Client connected: {client.is_connected()}")


if __name__ == "__main__":

    # 実行
    asyncio.run(main())
