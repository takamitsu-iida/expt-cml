#!/usr/bin/env python

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = "Simple pyATS MCP Server"

#
# 標準ライブラリのインポート
#
import argparse
import asyncio
import json
import logging
import sys

from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from dotenv import load_dotenv
    from virl2_client import ClientLibrary
    from virl2_client.models.lab import Lab
    from pyats.topology import loader
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

# このファイルへのPathオブジェクト
app_path = Path(__file__)

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


# デバイス取得
def get_device(device_name):
    testbed = loader.load(TESTBED_PATH)
    device = testbed.devices.get(device_name)
    if not device:
        raise ValueError(f"デバイスが見つかりません: {device_name}")
    if not device.is_connected():
        device.connect()
    return device


# showコマンド実行（非同期版）
async def run_show_command_async(device_name, command):
    loop = asyncio.get_event_loop()
    try:
        device = await loop.run_in_executor(None, get_device, device_name)
        output = await loop.run_in_executor(None, device.execute, command)
        await loop.run_in_executor(None, device.disconnect)
        return {"status": "success", "output": output}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# コンフィグ投入（非同期版）
async def configure_device_async(device_name, config_commands):
    loop = asyncio.get_event_loop()
    try:
        device = await loop.run_in_executor(None, get_device, device_name)
        output = await loop.run_in_executor(None, device.configure, config_commands)
        await loop.run_in_executor(None, device.disconnect)
        return {"status": "success", "output": output}
    except Exception as e:
        return {"status": "error", "error": str(e)}

#
# MCPサーバ初期化
#
mcp = FastMCP(SCRIPT_DESCRIPTION)

@mcp.tool()
async def pyats_run_show_command(device_name: str, command: str) -> str:
    """指定したデバイスでshowコマンドを非同期実行"""
    result = await run_show_command_async(device_name, command)
    return json.dumps(result, indent=2)


@mcp.tool()
async def pyats_configure_device(device_name: str, config_commands: str) -> str:
    """指定したデバイスにコンフィグを非同期投入"""
    result = await configure_device_async(device_name, config_commands)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
    parser.add_argument("--show", nargs=3, metavar=("DEVICE", "COMMAND"), help="指定デバイスでshowコマンド実行")
    parser.add_argument("--config", nargs=2, metavar=("DEVICE", "CONFIG"), help="指定デバイスにコンフィグ投入")
    args = parser.parse_args()

    load_dotenv('env')

    if args.show:
        device_name, command = args.show
        result = asyncio.run(run_show_command_async(device_name, command))
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if args.config:
        device_name, config_commands = args.config
        result = asyncio.run(configure_device_async(device_name, config_commands))
        print(json.dumps(result, indent=2))
        sys.exit(0)

    logger.info("MCPサーバを起動します")
    mcp.run(transport="stdio")
