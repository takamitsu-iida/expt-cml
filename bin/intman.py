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

NODE_INTERVAL: float = 0.1

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

        # インターフェイスごとに結果を保存する辞書型
        self.intf = {}


    def update(self) -> None:
        try:
            # ノードの状態を更新する
            self.state = self.node.state

            print(self.state)

            self.cpu_usage = self.node.cpu_usage

            # 各インターフェースの情報を更新する
            for intf in self.node.interfaces():

                # Loopbackインターフェースは無視する
                if intf.label.startswith('Loop'):
                    continue

                # このインタフェース名に対応した辞書型を取り出す
                intf_data = self.intf.setdefault(intf.label, {})

                # 前回の値を取り出す
                before_date = intf_data.get('date', None)
                before_readpackets = intf_data.get('readpackets', None)
                before_writepackets = intf_data.get('writepackets', None)

                # 現在の値を取り出す
                now_date = time.time()
                now_readpackets = intf.readpackets
                now_writepackets = intf.writepackets

                # 現在の値を保存する
                intf_data['date'] = now_date
                intf_data['readpackets'] = now_readpackets
                intf_data['writepackets'] = now_writepackets

                # 初回起動時は値を保存するだけでよい
                if not before_date:
                    continue

                # Packet Per Secondを計算する
                pps = ((now_readpackets - before_readpackets) + (now_writepackets - before_writepackets)) / (now_date - before_date)

                # インタフェースの状態を調べる
                now_state = intf.state  # 'STARTED' or 'STOPPED'

                # 取り出した値をもとに表示する文字を決定する
                c = 'X' if now_state == 'STOPPED' else self.get_result_char(pps)

                # 文字を保存する
                results = intf_data.setdefault('results', [])
                results.insert(0, c)

                # 過去100件のみ保存（実際に表示されるのは画面の幅による）
                while len(results) > 100:
                    results.pop()

        except Exception as e:
            self.state = "ERROR"
            logging.error(f"Error updating node {self.name}: {e}")


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

    # 3行目から表示開始
    row = 3
    for target in targets:

        # 矢印表示
        if arrow_idx is not None and row == arrow_idx:
            stdscr.addstr(row, 0, " > ", curses.A_BOLD)

        # ノード名を切り詰め
        name_disp = target.name[:MAX_HOSTNAME_LENGTH]

        # ノードの情報を表示
        stdscr.addstr(row, HOSTNAME_START, f"{name_disp:15} {target.cpu_usage}", curses.color_pair(UP_COLOR if target.state else DOWN_COLOR))

        # 各インターフェースの情報を表示
        for intf_label, intf_data in target.intf.items():
            intf_results = intf_data.get('results', [])
            if not intf_results:
                continue

            stdscr.addstr(row, INTERFACE_START, f"{intf_label:20}", curses.color_pair(UP_COLOR if target.state else DOWN_COLOR))

            # インターフェースの実行結果を取り出す
            # datas = self.intf_results.get(intf.label, None)
            datas = intf_results

            # 履歴表示
            for n, c in enumerate(datas[:max_result_len]):
                stdscr.addstr(row, RESULT_START + n, c, curses.color_pair(UP_COLOR if c != "X" else DOWN_COLOR))

            row += 1  # 次の行へ

    stdscr.refresh()



def main(stdscr: curses.window, targets: list[NodeTarget]) -> None:
    while True:
        for index, target in enumerate(targets):
            target.update()
            draw_screen(stdscr, targets, arrow_idx=index+3)
            time.sleep(NODE_INTERVAL)
        time.sleep(1)


def run_curses(stdscr: curses.window, targets: list[NodeTarget]) -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(DEFAULT_COLOR, -1, -1)
    curses.init_pair(UP_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(DOWN_COLOR, curses.COLOR_RED, -1)
    curses.curs_set(0)  # カーソルを非表示にする

    try:
        main(stdscr, targets)
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

    # 対象のラボを探す
    lab = client.find_labs_by_title(LAB_NAME)
    if not lab:
        logging.error(f"Error: ラボ '{LAB_NAME}' が見つかりません")
        sys.exit(-1)
    lab = lab[0]

    # 対象ノードを探す
    targets = [NodeTarget(node) for node in lab.nodes()]
    if not targets:
        logging.error(f"Error: ターゲットノードがありません")
        sys.exit(-1)

    # cursesアプリケーションとして実行
    curses.wrapper(lambda stdscr: run_curses(stdscr, targets))
