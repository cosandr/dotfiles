#!/usr/bin/env python3

import os
import sys

import requests

FONT = os.getenv("FONT", "icomoon-feather")

if FONT == "icomoon-feather":
    SHOW_DICT = {
        "sensor2": " ",   # feather house
        "sensor1": " ",   # feather droplet
    }

elif FONT == "nerd-font":
    SHOW_DICT = {
        "sensor2": "ﮟ ",    # nerd home outline
        "sensor1": " ",   # nerd drop
    }
elif FONT == "siji":
    SHOW_DICT = {
        "sensor2": " ",
        "sensor1": " ",
    }
else:
    SHOW_DICT = {
        "sensor2": "Ambient: ",
        "sensor1": "Water: ",
    }

DEGREES_SYM = os.getenv("DEGREES_SYM", "°C")
SEP = os.getenv("SEP", " ")
SIG_FIGS = int(os.getenv("SIG_FIGS", "1"))
URL = os.getenv("URL", "http://127.0.0.1:2782/api/status")


try:
    status = requests.get(URL).json()
    temps = status.get('temp', {})
    print_entries = []
    for key, name in SHOW_DICT.items():
        val = temps.get(key)
        if val is not None:
            print_entries.append(f'{name}{val:.{SIG_FIGS}f}{DEGREES_SYM}')
    if print_entries:
        print(SEP.join(print_entries))
except Exception as e:
    print('AQ ERR')
    print(e, file=sys.stderr)
