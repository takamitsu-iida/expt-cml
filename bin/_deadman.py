#!/usr/bin/env python3
#

import curses
import socket
import re
import sys
import asyncio
from subprocess import DEVNULL, PIPE, getoutput
from shutil import which

import os
import time
import datetime
import signal
import argparse
import _thread


TITLE_PROGNAME = "Dead Man"
TITLE_VERSION = "[ver 22.02.10]"
TITLE_VERTIC_LENGTH = 4

hostname = socket.gethostname()

try:
    TITLE_HOSTINFO = "From: %s (%s)" % (hostname, socket.gethostbyname(hostname))
except:
    TITLE_HOSTINFO = "From: %s" % hostname

ARROW = " > "

PING_INTERVAL = 0.05
PING_ALLTARGET_INTERVAL = 1
RTT_SCALE = 10

MAX_HOSTNAME_LENGTH = 20
MAX_ADDRESS_LENGTH = 40
RESULT_STR_LENGTH = 10

DEFAULT_COLOR = 1
UP_COLOR = 2
DOWN_COLOR = 3

OSNAME = getoutput("uname -s")

PING_SUCCESS      = 0
PING_FAILED       = -1

LOGDIR = ""


class PingResult:

    def __init__(self, success = False, errcode = PING_FAILED, rtt = 0.0, ttl = 0):
        self.success = success
        self.errcode = errcode
        self.rtt = rtt
        self.ttl = ttl
        return


class PingTarget:

    def __init__(self, name, addr):
        self.name = name
        self.addr = addr

        self.ping = Ping(self.addr)
        self.result = []

        self.state = False
        self.loss = 0
        self.lossrate = 0.0
        self.rtt = 0 # current RTT
        self.tot = 0 # total of all RTT
        self.avg = 0 # average of all RTT
        self.snt = 0 # number of sent ping
        self.ttl = 0 # last ttl

        return

    def __str__(self):
        s = [self.name, self.addr]
        return ':'.join(s)

    def __eq__(self, other):
        return str(self) == str(other)

    def send(self):
        asyncio.run(self.async_send())

    async def async_send(self):
        res = await self.ping.async_send()
        self.snt += 1
        self.consume_ping_result(res)

    def consume_ping_result(self, res):
        if res.success:
            # Ping Success
            self.state = True
            self.rtt = res.rtt
            self.tot += res.rtt
            self.avg = (self.tot) / self.snt
            self.ttl = res.ttl
        else:
            # Ping Failed
            self.loss += 1
            self.state = False

        self.lossrate = float(self.loss) / float(self.snt) * 100.0
        self.result.insert(0, self.get_result_char(res))

        while len(self.result) > RESULT_STR_LENGTH:
            self.result.pop()

        return

    def get_result_char(self, res):

        if res.errcode == PING_FAILED:
            # ping timeout
            return "X"

        if res.rtt < RTT_SCALE * 1: return "▁"
        if res.rtt < RTT_SCALE * 2: return "▂"
        if res.rtt < RTT_SCALE * 3: return "▃"
        if res.rtt < RTT_SCALE * 4: return "▄"
        if res.rtt < RTT_SCALE * 5: return "▅"
        if res.rtt < RTT_SCALE * 6: return "▆"
        if res.rtt < RTT_SCALE * 7: return "▇"

        return "█"


    def refresh(self):
        self.state = None
        self.lossrate = 0.0
        self.loss = 0
        self.rtt = 0
        self.tot = 0
        self.avg = 0
        self.snt = 0
        self.ttl = 0
        self.result = []

        return

class Separator:
    pass

SEPARATOR = Separator()

class Ping:

    def __init__(self, addr, timeout=1.0):
        self.addr = addr
        self.timeout = timeout

        self.ipversion = whichipversion(self.addr)
        if not self.ipversion:
            raise RuntimeError("invalid IP address '%s'" % self.addr)
        self.pingcmd = pingcmd(self.ipversion)


    async def async_send(self):

        # Build 'ping' command arguments
        cmd = []
        cmd += self.pingcmd
        cmd += [self.addr]

        env = dict(os.environ)
        env["LC_ALL"] = "C"
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=DEVNULL, env=env)

        try:
            await asyncio.wait_for(proc.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            pass
        try:
            proc.terminate()
        except ProcessLookupError:
            pass

        await proc.wait()

        (out, _err) = await proc.communicate()
        result = out.decode("utf-8")

        rttm = re.search(r'time=(\d+\.\d+)', result)
        if not rttm:
            rttm = re.search(r'time=(\d+)', result)

        ttlm = re.search(r'ttl=(\d+)', result)
        if not ttlm:
            ttlm = re.search(r'hlim=(\d+)', result)

        res = PingResult()

        if rttm:
            res.success = True
            res.errcode = PING_SUCCESS
            res.rtt = float(rttm.group(1))
            if ttlm:
                res.ttl = int(ttlm.group(1))
            else:
                res.ttl = -1

        if not rttm:
            res.success = False
            if "ping" in result:
                res.errcode = PING_FAILED
            if "No route to host" in result:
                res.errcode = PING_FAILED

            res.errcode = PING_FAILED

        return res


class CursesCtrl():

    def __init__(self, stdscr):
        self.stdscr = stdscr
        return

    def key_thread(self, *args):

        while True:
            ch = self.stdscr.getch()

            if ch == ord('r'):
                for idx, target in enumerate(args, 1):
                    if target == SEPARATOR:
                        continue

                    target.refresh()
                    self.erase_pingtarget(idx)
                    self.print_pingtarget(target, idx)


    def update_info(self, targets):

        # update start point and string length
        self.y, self.x = self.stdscr.getmaxyx()

        # update arrow
        self.start_arrow = 0
        self.length_arrow = len(ARROW)

        # update hostname
        hlen = len("HOSTNAME ")
        for target in targets:
            if target == SEPARATOR: continue
            if hlen < len(target.name): hlen = len(target.name)
        if hlen > MAX_HOSTNAME_LENGTH: hlen = MAX_HOSTNAME_LENGTH

        self.start_hostname = self.start_arrow + self.length_arrow
        self.length_hostname = hlen

        # update address
        alen = len("ADDRESS ")
        for target in targets:
            if target == SEPARATOR: continue
            if alen < len(target.addr): alen = len(target.addr)
        if alen > MAX_ADDRESS_LENGTH: alen = MAX_ADDRESS_LENGTH
        else: alen += 5

        self.start_address = self.start_hostname + self.length_hostname + 1
        self.length_address = alen

        # update reference
        self.ref_start = self.start_address + self.length_address + 1
        self.ref_length = len(" LOSS  RTT  AVG  SNT")

        # update result
        self.res_start = self.ref_start + self.ref_length + 2
        self.res_length = self.x - (self.ref_start + self.ref_length + 2)

        # reverse
        if self.res_length < 10:
            rev = 10 - self.res_length + len(ARROW)
            self.ref_start -= rev
            self.res_start -= rev
            self.res_length = 10

        global RESULT_STR_LENGTH
        RESULT_STR_LENGTH = self.res_length

        return

    def reinit(self):
        curses.endwin()
        self.stdscr = curses.initscr()
        self.stdscr.clear()

    def refresh(self):
        self.stdscr.refresh()

    def waddstr(self, *args):

        # wrapper for stdscr.addstr

        try:
            if len(args) == 3:
                self.stdscr.addstr(args[0], args[1], args[2])
            if len(args) > 3:
                self.stdscr.addstr(args[0], args[1], args[2], args[3])
        except curses.error:
            pass


    def print_title(self):

        # Print Program name on center of top line
        spacelen = int((self.x - len(TITLE_PROGNAME)) / 2)
        self.waddstr(0, spacelen, TITLE_PROGNAME, curses.A_BOLD)

        # Print hostname and version number
        hostinfo = TITLE_HOSTINFO
        self.waddstr(1, self.start_hostname, hostinfo, curses.A_BOLD)

        spacelen = self.x - (len(ARROW) + len(TITLE_VERSION))
        self.waddstr(1, spacelen, TITLE_VERSION, curses.A_BOLD)
        self.waddstr(2, len(ARROW), "RTT Scale %dms. Keys: (r)efresh" % RTT_SCALE)
        self.stdscr.move(0, 0)
        self.stdscr.refresh()
        return

    def erase_title(self):
        space = ""
        for x in range(self.x):
            space += " "
        self.waddstr(0, 0, space)
        self.waddstr(1, 0, space)
        self.waddstr(2, 0, space)
        return

    def print_reference(self):
        hostname_str = "HOSTNAME"
        address_str = "ADDRESS"
        values_str = " LOSS  RTT  AVG  SNT  RESULT"

        # Print reference hostname and address
        self.waddstr(TITLE_VERTIC_LENGTH, len(ARROW), hostname_str, curses.A_BOLD)
        self.waddstr(TITLE_VERTIC_LENGTH, self.start_address, address_str, curses.A_BOLD)

        # Print references of values
        self.waddstr(TITLE_VERTIC_LENGTH, self.ref_start, values_str, curses.A_BOLD)

        self.stdscr.move(0, 0)
        self.stdscr.refresh()
        return

    def erase_reference(self):
        self.waddstr(TITLE_VERTIC_LENGTH, 0, " " * self.x)
        return

    def print_separator(self, number):
        linenum = number + TITLE_VERTIC_LENGTH
        self.waddstr(linenum, self.start_hostname, "-" * (self.x - self.start_hostname - len(ARROW)))
        self.stdscr.move(0, 0)
        self.stdscr.refresh()
        return

    def print_pingtarget(self, target, number):
        if target.state:
            line_color = curses.color_pair(DEFAULT_COLOR)
        else:
            line_color = curses.A_BOLD

        linenum = number + TITLE_VERTIC_LENGTH

        # Print values
        values_str = " %3d%% %4d %4d %4d  " % (int(target.lossrate), target.rtt, target.avg, target.snt)

        # Print ping line
        self.waddstr(linenum, self.start_hostname, target.name[0:self.length_hostname], line_color)
        self.waddstr(linenum, self.start_address, target.addr[0:self.length_address], line_color)
        self.waddstr(linenum, self.ref_start, values_str, line_color)

        for n in range(len(target.result)):
            if not target.result[n] in ("X", "t", "s"):
                color = curses.color_pair(UP_COLOR)
            else:
                color = curses.color_pair(DOWN_COLOR)

            y, x = self.stdscr.getmaxyx()
            if self.res_start + n > x:
                continue
            self.waddstr(linenum, self.res_start + n, target.result[n], color)

        y, x = self.stdscr.getmaxyx()

        if LOGDIR:
            filepath = LOGDIR + "/" + target.name
            if os.path.isdir(LOGDIR) == False:
                os.makedirs(LOGDIR)
            f = open(filepath, 'a')
            fline = (str(datetime.datetime.now()) + " " +
                     str(target.rtt) + " " +
                     str(target.avg) + " " +
                     str(target.snt) + "\n")
            f.write(fline)
            f.close()
        else:
            pass

        self.stdscr.move(0, 0)
        self.stdscr.refresh()

        return

    def print_arrow(self, number):
        linenum = number + TITLE_VERTIC_LENGTH
        self.waddstr(linenum, self.start_arrow, ARROW)
        self.stdscr.move(0, 0)
        self.stdscr.refresh()
        return

    def erase_arrow(self, number):
        linenum = number + TITLE_VERTIC_LENGTH
        self.waddstr(linenum, self.start_arrow, " " * len(ARROW))
        self.stdscr.move(0, 0)
        self.stdscr.refresh()
        return

    def erase_pingtarget(self, number):
        linenum = number + TITLE_VERTIC_LENGTH
        self.waddstr(linenum, 2, " " * self.x)
        return


class Deadman:

    def __init__(self, stdscr, configfile):

        self.curs = CursesCtrl(stdscr)
        self.configfile = configfile
        self.targets = []

        self.addtargets()

        signal.signal(signal.SIGWINCH, self.refresh_window)
        signal.signal(signal.SIGHUP, self.updatetargets)

        self.curs.print_title()

        return


    def addtargets(self):
        newtargets = []
        self.targetlist = self.gettargetlist(self.configfile)

        for name, addr in self.targetlist:

            if re.fullmatch(r'-+', name):
                pt = SEPARATOR
            else:
                pt = PingTarget(name, addr)
            idx = -1
            if pt in self.targets:
                idx = self.targets.index(pt)
                newtargets.append(self.targets[idx])
            else:
                newtargets.append(pt)

        self.targets = newtargets
        self.curs.update_info(self.targets)



    def main(self):

        _thread.start_new_thread(self.curs.key_thread, tuple(self.targets))

        # print blank line
        for idx, target in enumerate(self.targets, 1):
            if target == SEPARATOR:
                self.curs.print_separator(idx)
            else:
                self.curs.print_pingtarget(target, idx)

        while True:

            self.curs.update_info(self.targets)
            self.curs.erase_title()
            self.curs.print_title()
            self.curs.erase_reference()
            self.curs.print_reference()

            for idx, target in enumerate(self.targets, 1):
                if target == SEPARATOR:
                    continue

                self.curs.print_arrow(idx)
                target.send()
                self.curs.erase_pingtarget(idx)
                self.curs.print_pingtarget(target, idx)
                time.sleep(PING_INTERVAL)
                self.curs.erase_arrow(idx)

            self.curs.print_arrow(idx)
            time.sleep(PING_ALLTARGET_INTERVAL)
            self.curs.erase_arrow(idx)
            self.curs.erase_pingtarget(idx + 1)



    def refresh_window(self, signum, frame):
        self.curs.reinit()
        self.curs.update_info(self.targets)
        self.curs.print_title()
        self.curs.print_reference()

        for idx, target in enumerate(self.targets, 1):
            if target == SEPARATOR:
                self.curs.print_separator(idx)
            else:
                self.curs.print_pingtarget(target, idx)


    def updatetargets(self, signum, frame):
        self.addtargets()
        self.curs.refresh()


    def gettargetlist(self, configfile):

        targetlist = []

        for line in configfile:

            line = re.sub(r'\t', ' ', line)
            line = re.sub(r'\s+', ' ', line)
            line = re.sub(r'^#.*', '', line)
            line = re.sub(r';\s*#', '', line)
            line = line.strip()

            if line == "":
                continue

            ss = line.split(' ')
            name = ss.pop(0)
            addr = ss.pop(0) if ss else None

            targetlist.append([name, addr])

        configfile.close()

        return targetlist



# mics
def whichipversion(addr):

    try:
        # use the first addrinfo if addr is domain name
        (family, _, _, _, saddr) = socket.getaddrinfo(addr, None)[0]
    except:
        return False

    if family == socket.AF_INET:
        return 4
    elif family == socket.AF_INET6:
        return 6

    return False



def pingcmd(ipv):

    """
    XXX: add new osname (uname -s) to support new OS.

    Timeout is controlled by asyncio.wait_for.
    As a result, there is no difference :0 I need cleanup.
    """
    if ipv == 4:
        return ["ping", "-c", "1"]
    if ipv == 6:
        if which('ping6'):
            return ["ping6", "-c", "1"]
        else:
            return ["ping", "-c", "1"]

    return None



def main(stdscr, configfile):

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(DEFAULT_COLOR, -1, -1)
    curses.init_pair(UP_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(DOWN_COLOR, curses.COLOR_RED, -1)

    """
    XXX: parse and validating config file shoud be done before curses.wrapper.
    """

    deadman = Deadman(stdscr, configfile)
    deadman.main()

    return



if __name__ == '__main__':

    if not pingcmd(4):
        print("%s is not supported" % OSNAME)
        sys.exit(0)

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scale", type = int, default = 10, help = "scale of ping RTT bar gap, default 10 (ms)")
    parser.add_argument("-l", "--logging", default = None, dest = "logdir", help = "directory for log files")
    parser.add_argument("configfile", type = argparse.FileType("r"), help = "config file for deadman")

    args = parser.parse_args()

    RTT_SCALE = args.scale

    LOGDIR = args.logdir


    try:
        curses.wrapper(main, args.configfile)
    except KeyboardInterrupt:
        sys.exit(0)