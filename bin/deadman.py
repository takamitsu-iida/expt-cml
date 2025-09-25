#!/usr/bin/env python3

#
# Yet Another Deadman
# Deadman(https://github.com/upa/deadman)をシンプルに再実装したものです
# 余分な機能を削除し、基本的な機能に焦点を当てています
#

#
# 標準ライブラリのインポート
#
import argparse
import asyncio
import logging
import re
import socket
import sys
from subprocess import DEVNULL, PIPE
from shutil import which

try:
    # WindowsのWVSでUbuntuを実行している場合はcursesは動作しないかもしれません
    # sudo apt update
    # sudo apt install libncurses5-dev libncursesw5-dev
    import curses
except ModuleNotFoundError:
    logging.error("curses not found")
    sys.exit(-1)

TITLE_PROGNAME: str = "Yet Another Deadman"
TITLE_VERSION: str = "[2025.09.24]"

PING_INTERVAL: float = 0.05

RTT_SCALE: int = 10

DEFAULT_COLOR: int = 1
UP_COLOR:      int = 2
DOWN_COLOR:    int = 3

# ヘッダ表示（タイトル）
HEADER_TITLE: str = f"{TITLE_PROGNAME} {TITLE_VERSION}"

# ヘッダ表示（情報）
HEADER_INFO:  str = f"   RTT Scale {RTT_SCALE}ms."

# ヘッダ表示（列名）
#                     0         1         2         3         4         5         6         7
#                     01234567890123456789012345678901234567890123456789012345678901234567890
HEADER_COLS:  str = f"   HOSTNAME        ADDRESS               LOSS  RTT  AVG  SNT  RESULT"

# ホスト名の表示開始位置
HOSTNAME_START: int = 3

# アドレスの表示開始位置
ADDRESS_START: int = 19

# 各種値の表示開始位置
VALUES_START: int = 41

# 実行結果の表示開始位置
RESULT_START: int = 62

# セパレータ行のキャラクタ
SEPARATOR = "-"

# 最大ホスト名長（超える部分は切り詰め）
MAX_HOSTNAME_LENGTH = ADDRESS_START - HOSTNAME_START - 1

# 最大アドレス長（超える部分は切り詰め）
MAX_ADDRESS_LENGTH = VALUES_START - ADDRESS_START - 1


class PingResult:
    def __init__(self, success: bool = False, rtt: float = 0.0, ttl: int = 0, errcode: int = -1) -> None:
        self.success = success
        self.rtt = rtt
        self.ttl = ttl
        self.errcode = errcode


class PingTarget:
    def __init__(self, name: str, addr: str) -> None:
        self.name = name
        self.addr = addr
        self.ping = Ping(addr)
        self.state = False
        self.rtt = 0.0
        self.avg = 0.0
        self.snt = 0
        self.loss = 0
        self.lossrate = 0.0
        self.tot = 0.0
        self.ttl = 0
        self.result = []


    async def update(self):
        res = await self.ping.async_send()
        self.snt += 1
        if res.success:
            self.state = True
            self.rtt = res.rtt
            self.tot += res.rtt
            self.avg = self.tot / self.snt
            self.ttl = res.ttl
        else:
            self.state = False
            self.loss += 1
        self.lossrate = float(self.loss) / float(self.snt) * \
            100.0 if self.snt else 0.0
        self.result.insert(0, self.get_result_char(res))

        # 履歴データは過去100件保存するが、実際に表示されるのは画面の幅による
        while len(self.result) > 100:
            self.result.pop()


    def get_result_char(self, res: PingResult) -> str:
        if not res.success:
            return "X"
        if res.rtt < RTT_SCALE * 1:
            return "▁"
        if res.rtt < RTT_SCALE * 2:
            return "▂"
        if res.rtt < RTT_SCALE * 3:
            return "▃"
        if res.rtt < RTT_SCALE * 4:
            return "▄"
        if res.rtt < RTT_SCALE * 5:
            return "▅"
        if res.rtt < RTT_SCALE * 6:
            return "▆"
        if res.rtt < RTT_SCALE * 7:
            return "▇"
        return "█"


class Ping:
    def __init__(self, addr: str, timeout: float = 1.0) -> None:
        self.addr = addr
        self.timeout = timeout
        self.ipversion = whichipversion(self.addr)
        if not self.ipversion:
            raise RuntimeError("invalid IP address '%s'" % self.addr)
        self.pingcmd = pingcmd(self.ipversion)


    async def async_send(self) -> PingResult:
        cmd = self.pingcmd + [self.addr]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=DEVNULL)
        try:
            await asyncio.wait_for(proc.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            pass
        try:
            proc.terminate()
        except ProcessLookupError:
            pass
        await proc.wait()
        out, _ = await proc.communicate()
        result = out.decode()
        rttm = re.search(r'time=(\d+\.\d+)', result)
        if not rttm:
            rttm = re.search(r'time=(\d+)', result)
        ttlm = re.search(r'ttl=(\d+)', result)
        if not ttlm:
            ttlm = re.search(r'hlim=(\d+)', result)
        res = PingResult()
        if rttm:
            res.success = True
            res.errcode = 0
            res.rtt = float(rttm.group(1))
            res.ttl = int(ttlm.group(1)) if ttlm else -1
        else:
            res.success = False
            res.errcode = -1
        return res


def whichipversion(addr: str) -> int | bool:
    try:
        family = socket.getaddrinfo(addr, None)[0][0]
    except Exception:
        return False
    if family == socket.AF_INET:
        return 4
    elif family == socket.AF_INET6:
        return 6
    return False


def pingcmd(ipv: int) -> list[str] | None:
    if ipv == 4:
        return ["ping", "-c", "1"]
    if ipv == 6:
        if which('ping6'):
            return ["ping6", "-c", "1"]
        else:
            return ["ping", "-c", "1"]
    return None


def parse_config(filename: str) -> list[PingTarget | str]:
    targets = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if re.fullmatch(r'-+', line):
                targets.append(SEPARATOR)
            else:
                parts = line.split()
                if len(parts) >= 2:
                    targets.append(PingTarget(parts[0], parts[1]))
    return targets


def draw_screen(stdscr: curses.window, targets: list[PingTarget | str], arrow_idx: int | None = None) -> None:
    stdscr.clear()
    _y, x = stdscr.getmaxyx()
    stdscr.addstr(0, 0, f"{TITLE_PROGNAME}", curses.A_BOLD)  # タイトルを太字で表示
    stdscr.addstr(1, 0, f"{HEADER_INFO}")
    stdscr.addstr(2, 0, f"{HEADER_COLS}")

    # 履歴表示の最大幅を計算
    max_result_len = max(0, x - RESULT_START - 1)

    for index, target in enumerate(targets, start=3):
        if target == SEPARATOR:
            # セパレータ表示
            stdscr.addstr(index, HOSTNAME_START, SEPARATOR * (x - HOSTNAME_START))
            continue

        # 矢印表示
        if arrow_idx is not None and index == arrow_idx:
            stdscr.addstr(index, 0, " > ", curses.A_BOLD)

        # ホスト名とアドレスの切り詰め
        name_disp = target.name[:MAX_HOSTNAME_LENGTH]
        addr_disp = target.addr[:MAX_ADDRESS_LENGTH]

        # 各ターゲットの情報表示
        values_str = f"{int(target.lossrate):3d}% {int(target.rtt):4d} {int(target.avg):4d} {target.snt:4d}  "
        stdscr.addstr(index, HOSTNAME_START, f"{name_disp:15} {addr_disp:20} {values_str}", curses.color_pair(UP_COLOR if target.state else DOWN_COLOR))

        # 履歴表示
        for n, c in enumerate(target.result[:max_result_len]):
            stdscr.addstr(index, RESULT_START + n, c, curses.color_pair(UP_COLOR if c != "X" else DOWN_COLOR))

    stdscr.refresh()


async def main(stdscr: curses.window, targets: list[PingTarget]) -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(DEFAULT_COLOR, -1, -1)
    curses.init_pair(UP_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(DOWN_COLOR, curses.COLOR_RED, -1)
    curses.curs_set(0)  # カーソルを非表示にする

    while True:
        for index, target in enumerate(targets):
            draw_screen(stdscr, targets, arrow_idx=index+3)
            if target != SEPARATOR:
                await target.update()
                await asyncio.sleep(PING_INTERVAL)



def run_curses(stdscr: curses.window, configfile: str) -> None:
    try:
        targets = parse_config(configfile)
    except Exception as e:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Error: ターゲットの読み込みに失敗しました\n{e}", curses.A_BOLD | curses.color_pair(DOWN_COLOR))
        stdscr.refresh()
        stdscr.getch()
        return

    try:
        asyncio.run(main(stdscr, targets))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scale", type=int, default=10, help="scale of ping RTT bar gap, default 10 (ms)")
    parser.add_argument("configfile", help="config file for deadman")
    args = parser.parse_args()

    RTT_SCALE = args.scale

    curses.wrapper(lambda stdscr: run_curses(stdscr, args.configfile))
