#!/usr/bin/env python3

import curses
import socket
import re
import asyncio
import argparse

from subprocess import DEVNULL, PIPE
from shutil import which

TITLE_PROGNAME = "Dead Man"
TITLE_VERSION = "[ver 22.02.10]"

PING_INTERVAL = 0.05
RTT_SCALE = 10

DEFAULT_COLOR = 1
UP_COLOR = 2
DOWN_COLOR = 3


class Separator:
    pass


SEPARATOR = Separator()


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
    except:
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


def parse_config(filename: str) -> list[PingTarget | Separator]:
    targets = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # セパレータ行（例: ---）はSeparatorとして扱う
            if re.fullmatch(r'-+', line):
                targets.append(SEPARATOR)
            else:
                parts = line.split()
                if len(parts) >= 2:
                    targets.append(PingTarget(parts[0], parts[1]))
    return targets


def draw_screen(stdscr: curses.window, targets: list[PingTarget | Separator], arrow_idx: int | None = None) -> None:
    stdscr.clear()
    _y, x = stdscr.getmaxyx()
    stdscr.addstr(0, 0, TITLE_PROGNAME, curses.A_BOLD)
    stdscr.addstr(1, 0, f"   RTT Scale {RTT_SCALE}ms. Keys: (r)efresh")
    stdscr.addstr(2, 0, "   HOSTNAME        ADDRESS               LOSS  RTT  AVG  SNT  RESULT")

    # ホスト名などの表示開始位置を矢印の右（例: 3列目）に変更
    host_start = 3

    # 画面の幅から表示できる結果の数を計算
    result_start = 62
    max_result_len = max(0, x - result_start - 1)

    for i, t in enumerate(targets, 3):
        if t == SEPARATOR:
            # セパレータ行の表示
            stdscr.addstr(i, host_start, "-" * (x - host_start))
            continue

        # 矢印表示
        if arrow_idx is not None and i == arrow_idx:
            stdscr.addstr(i, 0, " > ", curses.A_BOLD)

        values_str = f"{int(t.lossrate):3d}% {int(t.rtt):4d} {int(t.avg):4d} {t.snt:4d}  "
        stdscr.addstr(i, host_start, f"{t.name:15} {t.addr:20} {values_str}", curses.color_pair(UP_COLOR if t.state else DOWN_COLOR))

        for n, c in enumerate(t.result[:max_result_len]):
            stdscr.addstr(i, result_start + n, c, curses.color_pair(UP_COLOR if c != "X" else DOWN_COLOR))

    # カーソルが邪魔なので左上に移動
    stdscr.move(0, 0)
    stdscr.refresh()


async def main(stdscr: curses.window, configfile: str) -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(DEFAULT_COLOR, -1, -1)
    curses.init_pair(UP_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(DOWN_COLOR, curses.COLOR_RED, -1)
    curses.curs_set(0)  # カーソルを非表示にする

    targets = parse_config(configfile)
    while True:
        for idx, t in enumerate(targets):
            draw_screen(stdscr, targets, arrow_idx=idx+3)
            if t != SEPARATOR:
                await t.update()
            await asyncio.sleep(PING_INTERVAL)
        draw_screen(stdscr, targets)
        await asyncio.sleep(PING_INTERVAL)


def run_curses(stdscr: curses.window, configfile: str) -> None:
    try:
        asyncio.run(main(stdscr, configfile))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scale", type=int, default=10, help="scale of ping RTT bar gap, default 10 (ms)")
    parser.add_argument("configfile", help="config file for deadman")
    args = parser.parse_args()

    RTT_SCALE = args.scale

    curses.wrapper(lambda stdscr: run_curses(stdscr, args.configfile))
