#!/usr/bin/env python

import asyncio
import json
import logging
import os
import sys

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


# MCPサーバ初期化
mcp = FastMCP("Simple pyATS MCP Server")

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
    logger.info("MCPサーバを起動します")
    mcp.run(transport="stdio")
