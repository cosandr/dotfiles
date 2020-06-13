#!/usr/bin/env python3

import subprocess


DEGREES_SYM = "°C"


try:
    s = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,clocks.gr,power.draw,temperature.gpu", "--format=csv,noheader,nounits"],
                       text=True, capture_output=True, check=True)
    out = s.stdout.split(',')
    usage = int(out[0])
    clock = int(out[1])
    pwr = float(out[2])
    temp = int(out[3])
    print(f' {usage:d}%, {clock:.0f}MHz, {pwr:.0f}W, {temp:d}{DEGREES_SYM}')
except:
    print(' N/A')
