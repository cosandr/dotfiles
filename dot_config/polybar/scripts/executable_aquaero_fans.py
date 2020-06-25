#!/usr/bin/env python3

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
    with open(f'/tmp/aquaero.txt', 'r') as f:
        lines = f.readlines()
    for line in lines:
        for entry in line.split('|'):
            e_name, e_val = entry.split('\t')
            name = SHOW_DICT.get(e_name)
            if name:
                rpm = int(e_val)
                print_entries.append(f'{name}: {rpm:,d}{RPM_SYM}')
    if print_entries:
        print(SEP.join(print_entries))
except:
    pass
