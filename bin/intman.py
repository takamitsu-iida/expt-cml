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
MAX_HOSTNAME_LENGTH = INTERFACE_START - HOSTNAME_START - 1
MAX_INTERFACE_NAME_LENGTH = RESULT_START - INTERFACE_START - 1


class IntfStat:
    def __init__(self, current_time: float, readpackets: int, writepackets: int, state: str):
        self.time = current_time
        self.readpackets = readpackets
        self.writepackets = writepackets
        self.state = state  # 'STARTED' or 'STOPPED'


def get_past_intfstat(current_time: float, stat_list: list, diff_seconds: float = 3.0):
    candidate = None
    for stat in stat_list:
        if current_time - stat.time < diff_seconds:
            candidate = stat
        else:
            break
    return candidate


class NodeTarget:
    def __init__(self, node) -> None:
        self.node = node

        self.name = node.label
        self.state = node.state
        self.cpu_usage = node.cpu_usage

        # インターフェイスごとに結果を保存する辞書型を初期化する
        self.intf = {}
        for i in node.interfaces():
            self.intf[i.label] = {
                'stat_list': [],
                'result_list': []
            }


    def update(self) -> None:
        try:
            # ノードの状態を更新する
            self.state = self.node.state
            self.cpu_usage = self.node.cpu_usage

            # 各インターフェースの情報を更新する
            for intf in self.node.interfaces():

                # Loopbackインターフェースは無視する
                if intf.label.startswith('Loop'):
                    continue

                # このインタフェース名に対応した辞書型を取り出す
                intf_data = self.intf.get(intf.label, None)
                if intf_data is None:
                    continue

                # 過去のデータが入ったリストを取り出す
                stat_list = intf_data.get('stat_list', None)
                if stat_list is None:
                    continue

                # 結果の履歴を保存するリストを取り出す
                result_list = intf_data.get('result_list', None)
                if result_list is None:
                    continue

                # 現在の値を取り出してIntfStatオブジェクトにする
                now = time.time()
                stat = IntfStat(now, intf.readpackets, intf.writepackets, intf.state)

                # リストの先頭に挿入
                stat_list.insert(0, stat)

                # 最大100件を保存
                while len(stat_list) > 100:
                    stat_list.pop()

                # Packet Per Secondを計算する

                # stat_listを探して古いデータを取得する
                past_stat = get_past_intfstat(now, stat_list, diff_seconds=5.0)
                if past_stat is None:
                    result_list.insert(0, '.')
                else:
                    diff_time = now - past_stat.time
                    if diff_time < 0.1:
                        result_list.insert(0, '.')
                    else:
                        pps = ((stat.readpackets - past_stat.readpackets) + (stat.writepackets - past_stat.writepackets)) / (now - past_stat.time)
                        # 取り出した値をもとに表示する文字を決定する
                        c = 'X' if stat.state == 'STOPPED' else self.get_result_char(pps)
                        result_list.insert(0, c)

                # 過去100件のみ保存（実際に表示されるのは画面の幅による）
                while len(result_list) > 100:
                    result_list.pop()

        except Exception as e:
            self.state = "ERROR"
            logging.error(f"Error updating node {self.name}: {e}")
            raise e


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


def draw_screen(stdscr: curses.window, targets: list[NodeTarget], index: int | None = None) -> None:
    # 画面をクリア
    stdscr.clear()

    # 画面サイズを取得
    _y, x = stdscr.getmaxyx()

    stdscr.addstr(0, 0, f"{TITLE_PROGNAME}", curses.A_BOLD)  # タイトルを太字で表示
    stdscr.addstr(1, 0, f"{HEADER_INFO}")
    stdscr.addstr(2, 0, f"{HEADER_COLS}")

    # 履歴表示の最大幅を計算
    max_result_len = max(0, x - RESULT_START - 1)

    row = 3
    for i, target in enumerate(targets):

        # 対象となるターゲットには矢印を表示する
        if index is not None and i == index:
            stdscr.addstr(row, 0, " > ", curses.A_BOLD)

        # ノード名を切り詰め
        name_disp = target.name[:MAX_HOSTNAME_LENGTH]

        # ノードの情報を表示
        stdscr.addstr(row, HOSTNAME_START, f"{name_disp} {target.state} {target.cpu_usage}%", curses.color_pair(UP_COLOR if target.state == "BOOTED" else DOWN_COLOR))

        # 次の行へ
        row += 1

        # 起動済みノードのみ、インタフェース情報を表示する
        if target.state == "BOOTED":

            # 各インターフェースの情報を表示
            for intf_name, intf_data in target.intf.items():
                result_list = intf_data.get('result_list', None)
                if not result_list:
                    continue

                intf_name_disp = intf_name[:MAX_INTERFACE_NAME_LENGTH]
                stdscr.addstr(row, INTERFACE_START, f"{intf_name_disp:20}", curses.color_pair(DOWN_COLOR if intf_data.get('state') == 'STOPPED' else UP_COLOR))

                # 履歴表示
                for n, c in enumerate(result_list[:max_result_len]):
                    stdscr.addstr(row, RESULT_START + n, c, curses.color_pair(DOWN_COLOR if c == "X" else UP_COLOR))

                # 次の行へ
                row += 1

    stdscr.refresh()



def run_curses(stdscr: curses.window, targets: list[NodeTarget]) -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(DEFAULT_COLOR, -1, -1)
    curses.init_pair(UP_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(DOWN_COLOR, curses.COLOR_RED, -1)
    curses.curs_set(0)  # カーソルを非表示にする

    try:
        while True:
            for index, target in enumerate(targets):
                target.update()
                draw_screen(stdscr, targets, index=index)
                time.sleep(NODE_INTERVAL)
            time.sleep(1)
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
