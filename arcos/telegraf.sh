#!/bin/bash

#
# Telegraf起動・状態確認スクリプト
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/telegraf.conf"
TELEGRAF_PROCESS_NAME="/usr/bin/telegraf"

usage() {
    echo "Usage: $0 {start|check|restart} [options]"
    echo ""
    echo "Commands:"
    echo "  start [telegraf_args]  - Start Telegraf"
    echo "  restart [telegraf_args] - Restart Telegraf"
    echo "  check                  - Check Telegraf connection status"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 check"
    echo "  $0 restart --debug"
    exit 1
}


start_telegraf() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Config file not found: $CONFIG_FILE"
        exit 1
    fi

    echo "Starting Telegraf with config: $CONFIG_FILE"
    ${TELEGRAF_PROCESS_NAME} --strict-env-handling --config "$CONFIG_FILE" "$@"
}


check_telegraf() {
    local ROUTER_IP="$1"

    echo "=================================================="
    echo " Telegraf Network Connection Check"
    echo "=================================================="
    echo ""

    echo "1. Telegraf Process Status ---"
    echo ""
    TELEGRAF_PIDS=$(pgrep -f "$TELEGRAF_PROCESS_NAME")

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

    echo "All Established TCP Connections by Telegraf (PID: $MAIN_TELEGRAF_PID)"
    echo ""
    ss -tnape | grep "pid=$MAIN_TELEGRAF_PID" | awk '{print $1, $2, $4, $5, $6}'
    if [ $? -ne 0 ]; then
        echo "No TCP connections found for Telegraf PID $MAIN_TELEGRAF_PID."
    fi
    echo ""

    # Telegrafプロセスが確立しているTCP接続の総数をカウント
    echo "Total ESTABLISHED TCP Connections by Telegraf (PID: $MAIN_TELEGRAF_PID) ---"
    echo ""
    ESTABLISHED_CONNECTIONS=$(ss -tnap state established | grep "pid=$MAIN_TELEGRAF_PID" | wc -l)
    echo "Total ESTABLISHED TCP connections: $ESTABLISHED_CONNECTIONS"
    echo ""


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
        kill -KILL "TELEGRAF_PIDS" || true
        sleep 2
        start_telegraf "$@"
        ;;
    *)
        echo "Error: Unknown command: $COMMAND"
        usage
        ;;
esac