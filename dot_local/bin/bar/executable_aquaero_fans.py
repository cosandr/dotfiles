#!/usr/bin/env python3

import os
import sys

import requests

SHOW_DICT = {
    "fan1": "Front",
    "fan2": "Side",
    "fan3": "Top",
    "fan4": "Bottom",
    "aquastream1": "Pump",
}
RPM_SYM = os.getenv("RPM_SYM", "")
SEP = os.getenv("SEP", " - ")
URL = os.getenv("URL", "http://127.0.0.1:2782/api/status")


try:
    status = requests.get(URL).json()
    fans = status.get('rpm', {})
    print_entries = []
    for key, name in SHOW_DICT.items():
        val = fans.get(key)
        if val is not None:
            print_entries.append(f'{name}: {val:,d}{RPM_SYM}')
    if print_entries:
        print(SEP.join(print_entries))
except Exception as e:
    print('AQ ERR')
    print(e, file=sys.stderr)
