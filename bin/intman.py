#!/usr/bin/env python3

#
# 標準ライブラリのインポート
#
import argparse
import logging
import sys
import time

try:
    # WindowsのWVSでUbuntuを実行している場合はcursesは動作しないかもしれません
    # dpkg -l | grep ncurses
    # でncursesがインストールされているか確認して、もし入っていなければ以下を実行してください
    #
    # sudo apt update
    # sudo apt install libncurses5-dev libncursesw5-dev
    #
    # これで動かなければPythonの再インストールが必要です。
    #
    # pyenvでPythonをインストールする場合、モジュール不足でエラーが大量にでるかもしれません。
    # おおむね次のようなモジュールを入れておけばPythonのインストールは大丈夫だと思います。
    # sudo apt update
    # sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev
    #
    # cd ~/.pyenv
    # git pull
    # pyenv install 3.13.7
    #
    import curses
except ModuleNotFoundError:
    logging.error("curses not found")
    logging.error("Please install the required packages.")
    logging.error("  sudo apt update")
    logging.error("  sudo apt install libncurses5-dev libncursesw5-dev")
    logging.error("  and then, install Python again")
    sys.exit(-1)

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

INTERVAL: float = 1.0

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
        self.name = node.label
        self.state = node.state
        self.cpu_usage = node.cpu_usage

        # インターフェイスごとの結果を保存
        # { 'eth0': [PingResult, PingResult, ...], 'eth1': [...], ... }
        self.intf = {}


    def update(self) -> None:
        try:
            self.state = self.node.state
            self.cpu_usage = self.node.cpu_usage
            for intf in self.node.interfaces():
                if intf.label.startswith('Loop'):
                    continue

                # このインタフェース名をキーとした辞書型を取り出す
                intf_data = self.intf.setdefault(intf.label, {})

                # 保存されている前回の値を取り出す
                last_date = intf_data.get('date', None)
                last_readpackets = intf_data.get('readpackets', None)
                last_writepackets = intf_data.get('writepackets', None)

                # 現在の値を取り出す
                now_date = time.time()
                now_readpackets = intf.readpackets
                now_writepackets = intf.writepackets

                # 取り出した値を保存する
                intf_data['date'] = now_date
                intf_data['readpackets'] = now_readpackets
                intf_data['writepackets'] = now_writepackets

                if not last_date:
                    # 初回起動時は値を保存するだけでよい
                    continue

                pps = ((now_readpackets - last_readpackets) + (now_writepackets - last_writepackets)) / (now_date - last_date)

                # インタフェースの状態を取り出す
                now_state = intf.state  # 'STARTED' or 'STOPPED'

                c = ' '
                if now_state == 'STOPPED':
                    c = 'X'
                else:
                    c = self.get_result_char(pps)

                results = intf_data.setdefault('results', [])
                results.insert(0, c)

                # 履歴データは過去100件保存するが、実際に表示されるのは画面の幅による
                while len(results) > 100:
                    results.pop()


        except Exception as e:
            self.result = "ERR"
            logging.error(f"Error updating node {self.hostname}: {e}")



    def get_result_char(self, pps: float) -> str:
        if pps < SCALE * 1:
            return "▁"
        if pps < SCALE * 2:
            return "▂"
        if pps < SCALE * 3:
            return "▃"
        if pps < SCALE * 4:
            return "▄"
        if pps < SCALE * 5:
            return "▅"
        if pps < SCALE * 6:
            return "▆"
        if pps < SCALE * 7:
            return "▇"
        return "█"


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



def main(stdscr: curses.window, lab) -> None:

    while True:
        for index, target in enumerate(targets):
            #draw_screen(stdscr, targets, arrow_idx=index+3)
            target.update()

            #print(f"{target.name} {target.cpu_usage}")
            gig1 = target.intf.get('GigabitEthernet1', {})
            results = gig1.get('results', [])
            print(results)


            time.sleep(INTERVAL)


def run_curses(stdscr: curses.window, lab) -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(DEFAULT_COLOR, -1, -1)
    curses.init_pair(UP_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(DOWN_COLOR, curses.COLOR_RED, -1)
    curses.curs_set(0)  # カーソルを非表示にする

    try:
        main(stdscr, lab)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scale", type=int, default=10, help="scale of ping RTT bar gap, default 10 (ms)")
    parser.add_argument("configfile", help="config file for intman")
    args = parser.parse_args()

    SCALE = args.scale

    try:
        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)
    except Exception as e:
        logging.critical(str(e))
        sys.exit(-1)

    # 接続を待機する
    client.is_system_ready(wait=True)

    lab = client.find_labs_by_title(LAB_NAME)

    if not lab:
        logging.error(f"Error: ラボ '{LAB_NAME}' が見つかりません")
        sys.exit(-1)

    lab = lab[0]

    targets = [NodeTarget(node) for node in lab.nodes()]

    if not targets:
        logging.error(f"Error: ターゲットノードがありません")
        sys.exit(-1)

    main(None, None)
    # curses.wrapper(lambda stdscr: run_curses(stdscr, lab))
