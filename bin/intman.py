#!/usr/bin/env python3

#
# 標準ライブラリのインポート
#
import argparse
import json
import logging
import math
import os
import sys
import time

from pathlib import Path

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
    from virl2_client.models.node import Node
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# ログ設定
#

# このファイルへのPathオブジェクト
app_path = Path(__file__)

# このファイルの名前から拡張子を除いてプログラム名を得る
app_name = app_path.stem

# アプリケーションのホームディレクトリはこのファイルからみて一つ上
app_home = app_path.parent.joinpath('..').resolve()

# ログファイルの名前
log_file = app_path.with_suffix('.log').name

# ログファイルを置くディレクトリ
log_dir = app_home.joinpath('log')
log_dir.mkdir(exist_ok=True)

# ログファイルのパス
log_path = log_dir.joinpath(log_file)


# 独自にロガーを取得する
logger = logging.getLogger(__name__)

# ログレベル設定
# レベルはこの順で下にいくほど詳細になる
#   logging.CRITICAL
#   logging.ERROR
#   logging.WARNING --- 初期値はこのレベル
#   logging.INFO
#   logging.DEBUG
logger.setLevel(logging.INFO)

# フォーマット
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 標準出力には出力しない
# stdout_handler = logging.StreamHandler(sys.stdout)
# stdout_handler.setFormatter(formatter)
# stdout_handler.setLevel(logging.INFO)
# logger.addHandler(stdout_handler)

# ログファイルのハンドラ
file_handler = logging.FileHandler(log_path, 'a+')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

#
# CMLに接続するための情報を取得する
#

# 環境変数が設定されている場合はそれを使用し、設定されていない場合はローカルファイルから読み込む
CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL2_HOST")
CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

if not all([CML_ADDRESS, CML_USERNAME, CML_PASSWORD]):
    # ローカルファイルから読み込み
    try:
        from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD
    except ImportError as e:
        logging.critical("CML connection info not found")
        logging.critical("Please set environment variables or create cml_config.py")
        sys.exit(-1)

# ノードから情報を取得したあと、次のノードの情報を取得するまでの待ち時間（秒）
NODE_INTERVAL: float = 0.1

# 表示に使用する文字と色
DEFAULT_COLOR: int = 1
UP_COLOR:      int = 2
DOWN_COLOR:    int = 3

TITLE_PROGNAME: str = "CML Intman"
TITLE_VERSION: str = "[2025.09.24]"

# ヘッダ表示（タイトル）
HEADER_TITLE: str = f"{TITLE_PROGNAME} {TITLE_VERSION}"

# ヘッダ表示（列名）
#                     0         1         2         3         4         5         6         7
#                     01234567890123456789012345678901234567890123456789012345678901234567890
#                        |                |                    |
HEADER_COLS:  str = f"   HOSTNAME         INTERFACE            TX"

# ホスト名の長さ上限、インタフェース名の長さ上限
HOSTNAME_LEN : int = 16
INTERFACE_LEN: int = 20

# ホスト名の表示開始位置
HOSTNAME_START: int = 3

# インターフェース名の長さと表示開始位置
INTERFACE_START: int = HOSTNAME_START + HOSTNAME_LEN + 1

# 実行結果の表示開始位置（RXの開始位置は表示するときに計算する）
TX_START: int = INTERFACE_START + INTERFACE_LEN + 1

# インターフェースごとに保存する履歴の最大数
MAX_HISTORY: int = 100

# 最大数を超えた場合に古いデータを削除する関数
def limit_list_length(lst: list, max_length: int = MAX_HISTORY) -> None:
    while len(lst) > max_length:
        lst.pop()


class IntfStat:
    def __init__(self, current_time: float, readpackets: int, writepackets: int) -> None:
        # 採取した時間
        self.time = current_time
        # 読み込んだパケット数
        self.readpackets = readpackets

        # 書き込んだパケット数
        self.writepackets = writepackets


class NodeTarget:
    def __init__(self, node: Node, conf: dict) -> None:
        self.node = node

        self.name = node.label
        self.state = node.state
        self.cpu_usage = node.cpu_usage

        # インターフェイスごとに結果を保存する辞書型を初期化する
        self.intf_dict = {}

        # すべてのインターフェースについて辞書型を初期化する
        self.intf_dict = {i.label: {'state': i.state, 'stat_list': [], 'rx_result_list': [], 'tx_result_list': []} for i in node.interfaces() if i.label in conf['interfaces']}

        """これと同じ
        for i in node.interfaces():
            if i.label in conf['interfaces]:
                self.intf_dict[i.label] = {
                    'state': i.state, # 'STARTED' or 'STOPPED' or 'DEFINED_ON_CORE' or None
                    'stat_list': [],
                    'rx_result_list': [],
                    'tx_result_list': []
                }
        """

        # PPS値に応じた7段階のキャラクタ
        self.chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]


    def calc_pps(self, stat_list: list[IntfStat], window_second: float = 5.0) -> tuple[float, float]:
        if stat_list is None or len(stat_list) < 2:
            return 0.0, 0.0

        # 最新のデータ
        newest = stat_list[0]

        # window_second秒以内のデータだけを取り出す
        window_stats = [stat for stat in stat_list if newest.time - stat.time < window_second]
        if len(window_stats) < 2:
            return 0.0, 0.0

        # window_second秒以内で一番古いデータ
        oldest = window_stats[-1]

        # 差分を計算
        diff_time = newest.time - oldest.time

        # PPSを計算
        # division by zeroを避けるためにdiff_timeが0.1秒以下の場合は0.0とする
        rx_pps = (newest.readpackets - oldest.readpackets) / diff_time if diff_time > 0.1 else 0.0
        tx_pps = (newest.writepackets - oldest.writepackets) / diff_time if diff_time > 0.1 else 0.0

        return rx_pps, tx_pps


    def update(self) -> None:
        try:
            # ノードの状態を更新する
            self.state = self.node.state
            self.cpu_usage = self.node.cpu_usage

            # 各インターフェースの情報を更新する
            # node.interfaces()を呼ぶことでvirl2_clientが最新情報を取得する
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

                # intf_dataの中のリストを取り出す
                stat_list, rx_result_list, tx_result_list = (
                    intf_data.get('stat_list'),
                    intf_data.get('rx_result_list'),
                    intf_data.get('tx_result_list')
                )

                # 現在の値を取り出してIntfStatオブジェクトにする
                now = time.time()
                stat = IntfStat(now, intf.readpackets, intf.writepackets)

                # IntfStatオブジェクトをリストの先頭に挿入
                stat_list.insert(0, stat)

                # Packet Per Secondを計算
                rx_pps, tx_pps = self.calc_pps(stat_list, window_second=5.0)

                # トラフィック量を文字に変換してリストの先頭に挿入
                if intf_data.get('state') is None:
                    rx_result_list.insert(0, 'X')
                    tx_result_list.insert(0, 'X')
                elif intf_data.get('state') !=  'STARTED':
                    rx_result_list.insert(0, 'X')
                    tx_result_list.insert(0, 'X')
                else:
                    rx_result_list.insert(0, self.get_result_char(rx_pps))
                    tx_result_list.insert(0, self.get_result_char(tx_pps))

                # リストの長さを制限する
                for lst in (stat_list, rx_result_list, tx_result_list):
                    limit_list_length(lst)

        except Exception as e:
            self.state = "ERROR"
            logging.error(f"Error updating node {self.name}: {e}")
            raise e


    def get_result_char(self, pps: float) -> str:
        # return self._get_result_char_by_log(pps)
        return self._get_result_char_by_exp(pps)


    def _get_result_char_by_log(self, pps: float) -> str:
        if pps <= 0:
            return self.chars[0]
        # ppsの対数をとってレベルを決定
        level = min(7, int(math.log10(pps + 1)))
        return self.chars[level]


    def _get_result_char_by_exp(self, pps: float) -> str:
        if pps <= 0:
            return self.chars[0]
        # base値と指数を調整（例: base=2, exp=0.6）
        base = 2.0
        exp = 0.6
        level = int((pps / base) ** exp)
        level = max(0, min(7, level))
        return self.chars[level]



def draw_screen(stdscr: curses.window, targets: list[NodeTarget], active_index: int | None = None) -> None:
    # 画面をクリア
    stdscr.clear()

    # 画面サイズを取得
    y, x = stdscr.getmaxyx()

    # RXとTXの表示幅を調整
    tx_len = rx_len = max(3, (x - TX_START) // 2 - 1)

    # 表示幅が足りない場合は何も表示せずに終了
    if tx_len <= 3:
        stdscr.refresh()
        return

    # RXの表示開始位置
    rx_start = TX_START + tx_len + 1

    # 画面の行位置
    row = 0

    # 0行目
    stdscr.addstr(row, 0, f"{TITLE_PROGNAME}", curses.A_BOLD)  # タイトルを太字で表示
    row += 1

    # 1行目
    stdscr.addstr(row, 0, f"{HEADER_COLS:<{TX_START + tx_len}} RX")
    row += 1

    # 2行目以降で各ノードの情報を表示
    for i, target in enumerate(targets):

        # updateしたターゲットには矢印を表示する
        if active_index is not None and i == active_index:
            stdscr.addstr(row, 0, " > ", curses.A_BOLD)

        # ノード名を切り詰め
        name_disp = target.name[:HOSTNAME_LEN]

        # ノードの情報を表示
        stdscr.addstr(row, HOSTNAME_START, f"{name_disp} ({target.state} {target.cpu_usage}%)", curses.color_pair(UP_COLOR if target.state == "BOOTED" else DOWN_COLOR))

        # 次の行へ
        row += 1
        # 画面の行が足りなくて表示できない場合はそこで中止
        if row >= y:
            stdscr.refresh()
            return

        # 各インターフェースの情報を表示
        for intf_name, intf_data in target.intf_dict.items():
            rx_result_list = intf_data.get('rx_result_list')
            tx_result_list = intf_data.get('tx_result_list')
            if not rx_result_list or not tx_result_list:
                continue

            #if intf_data.get('state') != 'STARTED':
            #    print(intf_data.state)
            #    continue

            # インタフェース名
            intf_name_disp = f"{intf_name[:INTERFACE_LEN]:<{INTERFACE_LEN + 1}}"
            stdscr.addstr(row, INTERFACE_START, f"{intf_name_disp}", curses.color_pair(DEFAULT_COLOR))

            # TX表示
            for n, c in enumerate(tx_result_list[:tx_len]):
                stdscr.addstr(row, TX_START + n, c, curses.color_pair(DOWN_COLOR if c == "X" else UP_COLOR))

            # RX表示
            for n, c in enumerate(rx_result_list[:rx_len]):
                stdscr.addstr(row, rx_start + n, c, curses.color_pair(DOWN_COLOR if c == "X" else UP_COLOR))

            # 次の行へ
            row += 1
            if row >= y:
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
                draw_screen(stdscr, targets, active_index=index)
                # targetが最後のノードでなければ少し待つ
                if index < len(targets) - 1:
                    time.sleep(NODE_INTERVAL)

            # 待機
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass


def dump_lab(client: ClientLibrary) -> None:
    labs_info = []
    for lab in client.all_labs():
        lab_dict = {
            "title": lab.title,
            "id": lab.id,
            "nodes": []
        }
        for node in lab.nodes():
            if node.node_definition in ['external_connector', 'unmanaged_switch']:
                continue

            node_dict = {
                "node_def": node.node_definition,
                "name": node.label,
                "interfaces": [intf.label for intf in node.interfaces()]
            }
            lab_dict["nodes"].append(node_dict)
        labs_info.append(lab_dict)

    for info in labs_info:
        print_text = json.dumps(info, indent=2, ensure_ascii=False)
        print(print_text)
        print('')


def parse_config(configfile: str) -> dict:
    with open(configfile, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dump", action='store_true', default=False, help="dump lab node and interface")
    parser.add_argument("configfile", nargs='?', default=None, help="config file for CML Intman")
    args = parser.parse_args()

    try:
        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)
        # 接続を待機する
        client.is_system_ready(wait=True)
        client.get_lab_list
    except Exception as e:
        logging.critical(str(e))

    if args.dump:
        dump_lab(client)
        sys.exit(0)

    # 以降の処理は configfile の指定が必要
    if args.configfile is None:
        logging.error("Error: configfileの指定が必要です")
        sys.exit(-1)

    conf_dict = parse_config(args.configfile)
    print(json.dumps(conf_dict, indent=2))
    title = conf_dict.get('title', None)
    if title is None:
        logging.error("title is required")
        sys.exit(-1)


    # 対象のラボを探す
    lab = client.find_labs_by_title(title)
    if not lab:
        logging.error(f"Error: ラボ '{title}' が見つかりません")
        sys.exit(-1)
    lab = lab[0]

    # 対象ノードを探す
    nodes = []
    for node in lab.nodes():
        for d in conf_dict['nodes']:
            if node.label == d.get('name'):
                nodes.append([node, d])
                break
    if not nodes:
        logging.error(f"Error: ターゲットノードがありません")
        sys.exit(-1)

    # NodeTargetのリストに変換
    targets = [NodeTarget(n, d) for n, d in nodes]

    # cursesアプリケーションとして実行
    curses.wrapper(lambda stdscr: run_curses(stdscr, targets))
