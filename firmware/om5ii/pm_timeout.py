#!/usr/bin/env python3
"""Picture Mode stays open 30 s after the last input instead of 8 s, OM-5 Mark II (E148 1.1): data edits.

    pm_timeout.py --spec STOCK.BIN      check stock and (re)write the rows in patch.json

Stock (static and OM-Emu evidence, 2026-11-19):
 * 0x60f10fd2 arms a software timer, d0 = event id, d1 = duration in ms (the OM-3 project's 0x612970e8; atlas
   reference.om3-1100.timer-start). Menus arm event 500 at 8000 ms from 106 sites, each `mov 500,d0`
   (2c f4 01), `mov 8000,d1` (2d 40 1f), `call 0x60f10fd2`.
 * OM-Emu (tools/dev/trace.mjs on 0x60f10fd2, d0 = 500), Picture Mode (GUI state 0x0418,
   ID_ST_DIRECT_PICTUREMODE_ART): opening it arms at 0x60e3c4f8, up 0x60e3c567, down 0x60e3c5ea, left
   0x60e3c6df, right 0x60e3c7db, the dials 0x60e3c8de and 0x60e3c9d6. These also serve the tone page and the
   colour wheel (same screen). 0x60e3ca98 is the same handler's case for the sidebar row items 5029, 0x14fd..0x14ff.
   A tap (touch message 0x9755, OM-3's 0x611c3b20) arms at 0x60e3daca (OM-Emu tap:40,220 on the sidebar).
   The super control panel (event 510), the direct WB screen (0x60e3dda3..) and menus keep 8 s.
 * Without the edit, OM-Emu closes Picture Mode after 9 s idle.
Edit: the nine `mov 8000,d1` become `mov 30000,d1` (2d 30 75; a signed 16-bit immediate, so 32767 ms at most).
The OM-3 also needed a hook on a shared touch re-arm (0x612a8db3); E148's (0x60f22bcc) did not run for a
Picture Mode tap in OM-Emu.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

B = 0x60021020
SITES = (0x60e3c4f8, 0x60e3c567, 0x60e3c5ea, 0x60e3c6df, 0x60e3c7db, 0x60e3c8de, 0x60e3c9d6, 0x60e3ca98, 0x60e3daca)
TIMER = 0x60f10fd2
MS = 30000


def edits(stock):
    out = {}
    for n, site in enumerate(SITES):
        at = site - B
        assert stock[at - 3:at] == b'\x2c\xf4\x01', hex(site)          # mov 500,d0
        assert stock[at:at + 3] == b'\x2d\x40\x1f', hex(site)          # mov 8000,d1
        assert stock[at + 3] == 0xdd and site + 3 + struct.unpack('<i', stock[at + 4:at + 8])[0] == TIMER, hex(site)
        out['pm_timeout_%d' % n] = (site, b'\x2d' + struct.pack('<h', MS))
    return out


def main():
    if len(sys.argv) != 3 or sys.argv[1] != '--spec':
        sys.exit(__doc__)
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here.parents[1] / 'tools'))
    from oly_container import parse
    from oly_compress import expand_image
    stock = expand_image(next(b for b in parse(Path(sys.argv[2]).read_bytes()) if b.kind == 0x100).payload)
    sha = lambda b: hashlib.sha256(b).hexdigest()
    spec_path = here / 'patch.json'
    spec = json.loads(spec_path.read_text())
    for name, (address, data) in edits(stock).items():
        for e in spec['data_edits']:
            a = int(e['address'], 16)
            if e['name'] != name and a < address + len(data) and a + len(e['after']) // 2 > address:
                sys.exit(f'{name} overlaps {e["name"]}')
        at = address - B
        row = {'component': '0x100', 'name': name, 'address': hex(address), 'bytes': len(data),
               'before_sha256': sha(stock[at:at + len(data)]), 'after_sha256': sha(data)}
        spec['ranges'] = [r for r in spec['ranges'] if r['name'] != name] + [row]
        spec['data_edits'] = [e for e in spec['data_edits'] if e['name'] != name] + [
            {'component': '0x100', 'name': name, 'address': hex(address), 'after': data.hex()}]
        print(name, hex(address), data.hex())
    spec_path.write_text(json.dumps(spec, indent=2) + '\n')


if __name__ == '__main__':
    main()
