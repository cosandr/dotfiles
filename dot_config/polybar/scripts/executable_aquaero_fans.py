#!/usr/bin/env python3

import re

SHOW_DICT = {
    "fan1": "DDC",
    "fan3": "D5",
    "fan2": "Internal",
    "fan4": "External",
}
RPM_SYM = ""
SEP = " - "


try:
    print_entries = []
    re_fans = re.compile(r'\|?(?P<name>fan\d+)\t(?P<val>\d+)\|?')
    with open(f'/tmp/aquaero.txt', 'r') as f:
        content = f.read()
    avail_dict = {m.group('name'): int(m.group('val')) for m in re_fans.finditer(content)}
    for key, name in SHOW_DICT.items():
        val = avail_dict.get(key)
        if val:
            print_entries.append(f'{name}: {val:,d}{RPM_SYM}')
    if print_entries:
        print(SEP.join(print_entries))
except:
    pass
