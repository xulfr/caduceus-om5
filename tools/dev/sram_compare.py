#!/usr/bin/env python3
"""Compare every access to the on-chip SRAM window 0x8ff00000..0x8ff00fff between two expanded main programs.
Accesses are paired by the 16 bytes of code around the address; a pair whose address differs is listed.
    sram_compare.py A_main.bin B_main.bin [OUT.json]
Static analysis only."""
import collections
import json
import re
import sys

BASE = 0x60021020


def sites(d):
    out = []
    for m in re.finditer(rb'\x8f', d):
        o = m.start() - 3
        if o >= 2 and d[o - 2] in (0xfa, 0xfb, 0xfc, 0xfd, 0xfe) and 0x8ff00000 <= int.from_bytes(d[o:o + 4], 'little') < 0x8ff01000:
            out.append((o - 2, int.from_bytes(d[o:o + 4], 'little')))
    return out


def main():
    a, b = open(sys.argv[1], 'rb').read(), open(sys.argv[2], 'rb').read()
    key = lambda d, o: bytes(d[o + 6:o + 16]) + bytes(d[o - 6:o])
    sa, sb = sites(a), sites(b)
    index = collections.defaultdict(list)
    for o, v in sb:
        index[key(b, o)].append((o, v))
    same, moved, unpaired = 0, [], 0
    for o, v in sa:
        c = index.get(key(a, o), [])
        if len(c) != 1:
            unpaired += 1
        elif c[0][1] == v:
            same += 1
        else:
            moved.append({'a': hex(BASE + o), 'b': hex(BASE + c[0][0]), 'a_value': hex(v), 'b_value': hex(c[0][1])})
    only = lambda x, y: sorted(hex(v) for v in {v for _, v in x} - {v for _, v in y})
    out = {'a_accesses': len(sa), 'b_accesses': len(sb), 'paired_same': same, 'paired_moved': moved,
           'unpaired_a': unpaired, 'addresses_only_in_a': only(sa, sb), 'addresses_only_in_b': only(sb, sa)}
    text = json.dumps(out, indent=1)
    if len(sys.argv) > 3:
        open(sys.argv[3], 'w').write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
