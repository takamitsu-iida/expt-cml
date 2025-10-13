#!/usr/bin/env python

import os
import sys
import logging
import json
from pyats.topology import loader
from mcp.server.fastmcp import FastMCP

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimpleMCPServer")

# テストベッドファイルのパス
TESTBED_PATH = "testbed.yaml"

if not os.path.exists(TESTBED_PATH):
    logger.critical(f"テストベッドファイルが見つかりません: {TESTBED_PATH}")
    sys.exit(1)

# デバイス取得
def get_device(device_name):
    testbed = loader.load(TESTBED_PATH)
    device = testbed.devices.get(device_name)
    if not device:
        raise ValueError(f"デバイスが見つかりません: {device_name}")
    if not device.is_connected():
        device.connect()
    return device

# showコマンド実行
def run_show_command(device_name, command):
    try:
        device = get_device(device_name)
        output = device.execute(command)
        device.disconnect()
        return {"status": "success", "output": output}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# コンフィグ投入
def configure_device(device_name, config_commands):
    try:
        device = get_device(device_name)
        output = device.configure(config_commands)
        device.disconnect()
        return {"status": "success", "output": output}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# MCPサーバ初期化
mcp = FastMCP("Simple pyATS MCP Server")

@mcp.tool()
def pyats_run_show_command(device_name: str, command: str) -> str:
    """指定したデバイスでshowコマンドを実行"""
    result = run_show_command(device_name, command)
    return json.dumps(result, indent=2)

@mcp.tool()
def pyats_configure_device(device_name: str, config_commands: str) -> str:
    """指定したデバイスにコンフィグを投入"""
    result = configure_device(device_name, config_commands)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    logger.info("MCPサーバを起動します")
    mcp.run()