# -*- coding: utf-8 -*-

from os import uname
from socket import gethostname
from time import monotonic
import subprocess
import re


def parse_output(pattern, args):
    try:
        out_str = subprocess.check_output(args)
        if isinstance(out_str, bytes):
            out_str = out_str.decode()
    except Exception:
        out_str = ''

    match = re.search(pattern, out_str)
    return match.group(1) if match else None


def cpu_temp():
    t_str = parse_output(r'temp=(\S*)\'C', ['vcgencmd', 'measure_temp'])
    return float(t_str) if t_str else None


def ip_address():
    return parse_output(r'(\S*)', ['hostname', '-I'])


def host_name():
    return gethostname()


def os_name():
    return " ".join(uname())

def uptime_human():
    secs = monotonic()
    mins = secs // 60
    hours = mins // 60
    days = hours // 24
    secs -= mins * 60
    mins -= hours * 60
    hours -= days * 24
    return '{0:.0f} days {1:.0f}:{2:.0f}:{3:.0f}'.format(days, hours,mins, secs)
