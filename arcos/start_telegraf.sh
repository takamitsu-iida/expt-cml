#!/bin/bash

#
# Telegraf起動・状態確認スクリプト
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/telegraf.conf"
TELEGRAF_PROCESS_NAME="telegraf"

usage() {
    echo "Usage: $0 {start|check|restart} [options]"
    echo ""
    echo "Commands:"
    echo "  start [telegraf_args]  - Start Telegraf"
    echo "  check [router_ip]      - Check Telegraf connection status"
    echo "  restart [telegraf_args] - Restart Telegraf"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 check"
    echo "  $0 check 192.168.1.1"
    echo "  $0 restart --debug"
    exit 1
}

start_telegraf() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Config file not found: $CONFIG_FILE"
        exit 1
    fi

    echo "Starting Telegraf with config: $CONFIG_FILE"
    telegraf --config "$CONFIG_FILE" "$@"
}

check_telegraf() {
    local ROUTER_IP="$1"

    echo "=================================================="
    echo "         Telegraf Network Connection Check"
    echo "=================================================="
    echo ""

    # 1. Telegrafプロセスの確認
    echo "--- 1. Telegraf Process Status ---"
    TELEGRAF_PIDS=$(pgrep -d ',' "$TELEGRAF_PROCESS_NAME")

    if [ -z "$TELEGRAF_PIDS" ]; then
        echo "Warning: No Telegraf process found named '$TELEGRAF_PROCESS_NAME'. Exiting."
        exit 1
    fi

    echo "Telegraf PIDs found: $(echo "$TELEGRAF_PIDS" | tr ',' ' ')"
    ps aux | grep "$TELEGRAF_PROCESS_NAME" | grep -v "grep"
    echo ""

    MAIN_TELEGRAF_PID=$(echo "$TELEGRAF_PIDS" | cut -d',' -f1)
    echo "Using main Telegraf PID: $MAIN_TELEGRAF_PID for connection checks."
    echo ""

    # 2. Telegrafプロセスが確立しているすべてのTCP接続を表示
    echo "--- 2. All Established TCP Connections by Telegraf (PID: $MAIN_TELEGRAF_PID) ---"
    ss -tnape | grep "pid=$MAIN_TELEGRAF_PID" | awk '{print $1, $2, $4, $5, $6}'
    if [ $? -ne 0 ]; then
        echo "No TCP connections found for Telegraf PID $MAIN_TELEGRAF_PID."
    fi
    echo ""

    # 3. Telegrafプロセスが確立しているTCP接続の総数をカウント
    echo "--- 3. Total ESTABLISHED TCP Connections by Telegraf (PID: $MAIN_TELEGRAF_PID) ---"
    ESTABLISHED_CONNECTIONS=$(ss -tnap state established | grep "pid=$MAIN_TELEGRAF_PID" | wc -l)
    echo "Total ESTABLISHED TCP connections: $ESTABLISHED_CONNECTIONS"
    echo ""

    # 4. （オプション）特定のルータIPアドレスへの接続数をカウント
    echo "--- 4. (Optional) Check Connections to a Specific Router IP ---"
    if [ -n "$ROUTER_IP" ]; then
        echo "Checking connections to router IP: $ROUTER_IP"
        ROUTER_CONNECTIONS=$(ss -tnap state established | grep "pid=$MAIN_TELEGRAF_PID" | grep "$ROUTER_IP" | wc -l)
        echo "ESTABLISHED TCP connections to $ROUTER_IP: $ROUTER_CONNECTIONS"
        echo ""
    else
        echo "No router IP specified. Use: $0 check <router_ip>"
        echo ""
    fi

    echo "=================================================="
    echo "            Check Complete"
    echo "=================================================="
}

# メイン処理
if [ $# -lt 1 ]; then
    usage
fi

COMMAND="$1"
shift

case "$COMMAND" in
    start)
        start_telegraf "$@"
        ;;
    check)
        check_telegraf "$@"
        ;;
    restart)
        echo "Stopping Telegraf..."
        pkill "$TELEGRAF_PROCESS_NAME" || true
        sleep 2
        start_telegraf "$@"
        ;;
    *)
        echo "Error: Unknown command: $COMMAND"
        usage
        ;;
esac