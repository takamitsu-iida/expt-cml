#!/usr/bin/env python3

#
# 標準ライブラリのインポート
#
import logging
import sys
import curses
# import asyncio
import time
import argparse


#
# 外部ライブラリのインポート
#
try:
    from virl2_client import ClientLibrary
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# ローカルファイルからの読み込み
#
from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD

# CMLのラボの名前
LAB_NAME = "cml_lab1"

INTERVAL: float = 0.05

DEFAULT_COLOR: int = 1
UP_COLOR:      int = 2
DOWN_COLOR:    int = 3

TITLE_PROGNAME: str = "CML Intman"
TITLE_VERSION: str = "[2025.09.24]"

PPS_SCALE: int = 10

# ヘッダ表示（タイトル）
HEADER_TITLE: str = f"{TITLE_PROGNAME} {TITLE_VERSION}"

# ヘッダ表示（情報）
HEADER_INFO:  str = f"   PPS Scale {PPS_SCALE}"

# ヘッダ表示（列名）
#                     0         1         2         3         4         5         6         7
#                     01234567890123456789012345678901234567890123456789012345678901234567890
HEADER_COLS:  str = f"   HOSTNAME        INTERFACE            RESULT"

# 実行結果の表示開始位置
RESULT_START: int = 40

# ホスト名の表示開始位置
HOSTNAME_START: int = 3

# インターフェースの表示開始位置
INTERFACE_START: int = 19

# 最大ホスト名長（超える部分は切り詰め）
MAX_HOSTNAME_LENGTH = HOSTNAME_START - INTERFACE_START - 1



class NodeTarget:
    def __init__(self, node) -> None:
        self.node = node
        self.results = []

        # インターフェイスごとの結果を保存する
        self.intf_results = []


    def update(self) -> None:
        try:
            infos = self.getinfo()
        except Exception as e:
            self.result = "ERR"
            logging.error(f"Error updating node {self.hostname}: {e}")

        self.results.append("◆")

        # 履歴データは過去100件保存するが、実際に表示されるのは画面の幅による
        while len(self.results) > 100:
            self.results.pop()


    def getinfo(self):
        logging.debug(f"Getting info for node {self.node.cpu_usage}")
        return self.node.cpu_usage



def draw_screen(stdscr: curses.window, targets: list[NodeTarget], arrow_idx: int | None = None) -> None:
    stdscr.clear()
    _y, x = stdscr.getmaxyx()
    stdscr.addstr(0, 0, f"{TITLE_PROGNAME}", curses.A_BOLD)  # タイトルを太字で表示
    stdscr.addstr(1, 0, f"{HEADER_INFO}")
    stdscr.addstr(2, 0, f"{HEADER_COLS}")

    # 履歴表示の最大幅を計算
    max_result_len = max(0, x - RESULT_START - 1)

    for index, target in enumerate(targets, start=3):

        # 矢印表示
        if arrow_idx is not None and index == arrow_idx:
            stdscr.addstr(index, 0, " > ", curses.A_BOLD)

        # ホスト名とアドレスの切り詰め
        name_disp = target.name[:MAX_HOSTNAME_LENGTH]

        # 各ターゲットの情報表示
        stdscr.addstr(index, HOSTNAME_START, f"{name_disp:15}", curses.color_pair(UP_COLOR if target.state else DOWN_COLOR))

        # 履歴表示
        for n, c in enumerate(target.result[:max_result_len]):
            stdscr.addstr(index, RESULT_START + n, c, curses.color_pair(UP_COLOR if c != "X" else DOWN_COLOR))

    stdscr.refresh()



def main(stdscr: curses.window, client: ClientLibrary) -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(DEFAULT_COLOR, -1, -1)
    curses.init_pair(UP_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(DOWN_COLOR, curses.COLOR_RED, -1)
    curses.curs_set(0)  # カーソルを非表示にする

    lab = client.find_labs_by_title(LAB_NAME)
    if not lab:
        stdscr.addstr(0, 0, f"Error: ラボ '{LAB_NAME}' が見つかりません", curses.A_BOLD | curses.color_pair(DOWN_COLOR))
        stdscr.refresh()
        stdscr.getch()
        return

    lab = lab[0]

    targets = [NodeTarget(node) for node in lab.nodes()]

    while True:
        for index, target in enumerate(targets):
            draw_screen(stdscr, targets, arrow_idx=index+3)
            target.update()
            time.sleep(INTERVAL)


def run_curses(stdscr: curses.window, client: ClientLibrary) -> None:

    try:
        # asyncio.run(main(stdscr, client))
        main(stdscr, client)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scale", type=int, default=10, help="scale of ping RTT bar gap, default 10 (ms)")
    parser.add_argument("configfile", help="config file for deadman")
    args = parser.parse_args()

    RTT_SCALE = args.scale

    try:
        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)
    except Exception as e:
        logging.critical(str(e))
        sys.exit(-1)

    # 接続を待機する
    client.is_system_ready(wait=True)

    curses.wrapper(lambda stdscr: run_curses(stdscr, client))
