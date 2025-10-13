#!/usr/bin/env python

import httpx
from mcp.server.fastmcp import FastMCP

# MCPサーバ初期化
mcp = FastMCP("Weather MCP Server")

# NWS APIの基本情報
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

# NWS APIへリクエストを送る関数
async def fetch_json(url: str) -> dict | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

# アラート情報を整形する関数
def format_alert(feature: dict) -> str:
    props = feature.get("properties", {})
    return (
        f"Event: {props.get('event', 'Unknown')}\n"
        f"Area: {props.get('areaDesc', 'Unknown')}\n"
        f"Severity: {props.get('severity', 'Unknown')}\n"
        f"Description: {props.get('description', 'No description available')}\n"
        f"Instructions: {props.get('instruction', 'No specific instructions provided')}\n"
    )

# アラート取得ツール
@mcp.tool()
async def get_alerts(state: str) -> str:
    """指定した州の気象アラートを取得します（例: CA, NY）"""
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await fetch_json(url)
    if not data or "features" not in data or not data["features"]:
        return "アラート情報が取得できませんでした。"
    return "\n---\n".join(format_alert(f) for f in data["features"])

# 天気予報取得ツール
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """指定した緯度・経度の天気予報を取得します"""
    # まず予報URLを取得
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await fetch_json(points_url)
    if not points_data or "properties" not in points_data or "forecast" not in points_data["properties"]:
        return "予報情報が取得できませんでした。"
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await fetch_json(forecast_url)
    if not forecast_data or "properties" not in forecast_data or "periods" not in forecast_data["properties"]:
        return "詳細な予報情報が取得できませんでした。"
    periods = forecast_data["properties"]["periods"]
    # 直近5件だけ表示
    result = []
    for p in periods[:5]:
        result.append(
            f"{p['name']}:\n"
            f"  気温: {p['temperature']}°{p['temperatureUnit']}\n"
            f"  風: {p['windSpeed']} {p['windDirection']}\n"
            f"  予報: {p['detailedForecast']}\n"
        )
    return "\n---\n".join(result)

if __name__ == "__main__":
    mcp.run(transport='stdio')