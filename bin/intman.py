#!/usr/bin/env python3

#
# 標準ライブラリのインポート
#
import argparse
import logging
import os
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
# CMLに接続するための情報を取得する
#

# 環境変数が設定されている場合はそれを使用し、設定されていない場合はローカルファイルから読み込む
CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL2_HOST")
CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

if not all([CML_ADDRESS, CML_USERNAME, CML_PASSWORD]):
    # ローカルファイルからの読み込み
    try:
        from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD
    except ImportError as e:
        logging.critical("CML connection info not found")
        logging.critical("Please set environment variables or create cml_config.py")
        sys.exit(-1)

# CMLのラボの名前
LAB_NAME = "cml_lab1"

# ノードから情報を取得したあと、次のノードの情報を取得するまでの待ち時間（秒）
NODE_INTERVAL: float = 0.1

# 表示に使用する文字と色
DEFAULT_COLOR: int = 1
UP_COLOR:      int = 2
DOWN_COLOR:    int = 3

TITLE_PROGNAME: str = "CML Intman"
TITLE_VERSION: str = "[2025.09.24]"

# PPSのスケール（10にすると10pps～70ppsの7段階）
SCALE: int = 10

# ヘッダ表示（タイトル）
HEADER_TITLE: str = f"{TITLE_PROGNAME} {TITLE_VERSION}"

# ヘッダ表示（情報）
HEADER_INFO:  str = f"   PPS Scale {SCALE}"

# ヘッダ表示（列名）
#                     0         1         2         3         4         5         6         7
#                     01234567890123456789012345678901234567890123456789012345678901234567890
HEADER_COLS:  str = f"   HOSTNAME         INTERFACE               RX           TX"
#                        |                |                       |
#                        3                20                       +-- 7段階の棒グラフ


# ホスト名の表示開始位置
HOSTNAME_START: int = 3
HOSTNAME_LEN : int = 15

# インターフェース名の長さと表示開始位置と
INTERFACE_START: int = HOSTNAME_START + HOSTNAME_LEN + 1
INTERFACE_LEN: int = 15

# 実行結果の表示開始位置
RX_START: int = INTERFACE_START + INTERFACE_LEN + 1

def get_rx_len(terminal_width: int):
    return (terminal_width - RX_START - 1) // 2


class IntfStat:
    def __init__(self, current_time: float, readpackets: int, writepackets: int):
        self.time = current_time
        self.readpackets = readpackets
        self.writepackets = writepackets


class NodeTarget:
    def __init__(self, node) -> None:
        self.node = node

        self.name = node.label
        self.state = node.state
        self.cpu_usage = node.cpu_usage

        # インターフェイスごとに結果を保存する辞書型を初期化する
        self.intf_dict = {}
        for i in node.interfaces():
            self.intf_dict[i.label] = {
                'state': i.state, # 'STARTED' or 'STOPPED' or 'DEFINED_ON_CORE' or None
                'stat_list': [],
                'rx_result_list': [],
                'tx_result_list': []
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
                intf_data = self.intf_dict.get(intf.label, None)
                if intf_data is None:
                    continue

                # 現在のインタフェースの状態を記録
                intf_data['state'] = intf.state

                # 過去のデータが入ったリストを取り出す
                stat_list = intf_data.get('stat_list')

                # 結果の履歴を保存するリストを取り出す
                rx_result_list = intf_data.get('rx_result_list')
                tx_result_list = intf_data.get('tx_result_list')

                # 現在の値を取り出してIntfStatオブジェクトにする
                now = time.time()
                stat = IntfStat(now, intf.readpackets, intf.writepackets)

                # IntfStatオブジェクトをリストの先頭に挿入
                stat_list.insert(0, stat)

                # 最大100件を保存
                while len(stat_list) > 100:
                    stat_list.pop()

                # Packet Per Secondを計算するために3秒前のデータを取得する
                candidate_list = [stat for stat in stat_list if now - stat.time < 3.0]
                past_stat = None
                if len(candidate_list) > 0:
                    past_stat = candidate_list[-1]

                # トラフィック履歴
                if intf_data.get('state') is None:
                    rx_result_list.insert(0, 'X')
                    tx_result_list.insert(0, 'X')
                elif intf_data.get('state') ==  'DEFINED_ON_CORE':
                    rx_result_list.insert(0, 'X')
                    tx_result_list.insert(0, 'X')
                elif intf_data.get('state') == 'STOPPED':
                    rx_result_list.insert(0, 'X')
                    tx_result_list.insert(0, 'X')
                elif past_stat is None:
                    rx_result_list.insert(0, '.')
                    tx_result_list.insert(0, '.')
                else:
                    diff_time = now - past_stat.time
                    if diff_time < 0.1:
                        rx_result_list.insert(0, '.')
                        tx_result_list.insert(0, '.')
                    else:
                        rx_pps = (stat.readpackets - past_stat.readpackets) / diff_time
                        rx_result_list.insert(0, self.get_result_char(rx_pps))
                        tx_pps = (stat.writepackets - past_stat.writepackets) / diff_time
                        tx_result_list.insert(0, self.get_result_char(tx_pps))

                # 過去100件のみ保存（実際に表示されるのは画面の幅による）
                while len(rx_result_list) > 100:
                    rx_result_list.pop()
                while len(tx_result_list) > 100:
                    tx_result_list.pop()

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
    y, x = stdscr.getmaxyx()

    # RXの表示可能な長さを計算
    rx_len = tx_len = get_rx_len(x)
    tx_start = RX_START + rx_len + 1

    # 0行目
    stdscr.addstr(0, 0, f"{TITLE_PROGNAME}", curses.A_BOLD)  # タイトルを太字で表示
    # 1行目
    stdscr.addstr(1, 0, f"{HEADER_INFO}")
    # 2行目
    stdscr.addstr(2, 0, f"{HEADER_COLS}")

    # 3行目以降で各ノードの情報を表示
    row = 3
    for i, target in enumerate(targets):

        # updateしたターゲットには矢印を表示する
        if index is not None and i == index:
            stdscr.addstr(row, 0, " > ", curses.A_BOLD)

        # ノード名を切り詰め
        name_disp = target.name[:HOSTNAME_LEN]

        # ノードの情報を表示
        stdscr.addstr(row, HOSTNAME_START, f"{name_disp} ({target.state} {target.cpu_usage}%)", curses.color_pair(UP_COLOR if target.state == "BOOTED" else DOWN_COLOR))

        # 次の行へ
        row += 1
        # 画面の行が足りなくて表示できない場合はそこで中止
        if row == y:
            stdscr.refresh()
            return

        # 各インターフェースの情報を表示
        for intf_name, intf_data in target.intf_dict.items():
            rx_result_list = intf_data.get('rx_result_list')
            if not rx_result_list:
                continue

            tx_result_list = intf_data.get('tx_result_list')
            if not tx_result_list:
                continue

            #if intf_data.get('state') != 'STARTED':
            #    print(intf_data.state)
            #    continue

            # インタフェース名
            intf_name_disp = intf_name[:INTERFACE_LEN]
            stdscr.addstr(row, INTERFACE_START, f"{intf_name_disp:INTERFACE_LEN+1}", curses.color_pair(DEFAULT_COLOR))

            # RX表示
            for n, c in enumerate(rx_result_list[:rx_len]):
                stdscr.addstr(row, RX_START + n, c, curses.color_pair(DOWN_COLOR if c == "X" else UP_COLOR))

            # TX表示
            for n, c in enumerate(tx_result_list[:tx_len]):
                stdscr.addstr(row, tx_start + n, c, curses.color_pair(DOWN_COLOR if c == "X" else UP_COLOR))

            # 次の行へ
            row += 1
            if row == y:
                stdscr.refresh()
                return

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
    parser.add_argument("-s", "--scale", type=int, default=10, help="scale of PPS bar gap, default 10 (10pps to 70pps)")
    parser.add_argument("configfile", help="config file for CML Intman")
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
