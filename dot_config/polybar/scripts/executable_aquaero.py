#!/usr/bin/env python3


SHOW_DICT = {
    "sensor1": " ",   # feather droplet
    "sensor2": " ",   # feather house
}

DEGREES_SYM = "°C"
SEP = " "


try:
    print_entries = []
    with open(f'/tmp/aquaero.txt', 'r') as f:
        lines = f.readlines()
    for line in lines:
        for entry in line.split('|'):
            e_name, e_val = entry.split('\t')
            name = SHOW_DICT.get(e_name)
            if name:
                temp = float(e_val)
                print_entries.append(f'{name}{temp:.1f}{DEGREES_SYM}')
    if print_entries:
        print(SEP.join(print_entries))
except:
    pass
