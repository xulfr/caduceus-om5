#!/usr/bin/env python3
"""Live ND32/ND64 in CP Button Settings for OM-5 Mark II (E148 1.1): build and check the data edits.

    cp_nd.py --spec STOCK.BIN      check stock and (re)write the three rows in patch.json

Stock (emulator and static evidence, 2026-11-16):
 * Menu page 0x16f (CP Button Settings) takes its item IDs from the page table entry at 0x611943a4
   {u32 page, u32 list, u32 count}: list 0x61193dc0, 10 IDs 2211..2216, 2224..2227. The item records at
   0x611d0c6c.. (stride 28) also hold 2217 "Live ND Shooting : ND32(5EV)" and 2218 "...ND64(6EV)", and the CP
   ND selector 0x60d1d7da / table 0x60f7cc00 already maps CP items 2..7 to ND steps 1..6.
 * Settings 2217 / 2218 have cells (they read 1) but no descriptor among the 1589 static ones at 0x6050dad4,
   so OM's writer drops a change. hsl.s cp_nd_link links the two descriptors below into the RAM hash.
Edits (all inside the 504/505 record copies that color_profiles.py frees, 0x604f24d8..0x604f25e0):
 1. cp_button_items  0x604f24d8: the stock list with 2217, 2218 after 2216 (12 IDs).
 2. cp_nd_descriptors 0x604f24f0: 2216's descriptor (0x60515630) twice, id 2217 and 2218.
 3. cp_button_page   0x611943a8: page 0x16f's list pointer and count -> edit 1, 12.
"""
import hashlib, json, struct, sys
from pathlib import Path

B = 0x60021020
EXPANDED_SHA = '7ae7d4c60990cc859c070e0ceb6cbe612f9c5b260713f2f1256e51d137851c61'
PAGE, LIST, COUNT = 0x611943a4, 0x61193dc0, 10
ITEMS, DESC = 0x604f24d8, 0x604f24f0
FREE_LO, FREE_HI = 0x604f24d8, 0x604f25e0
DESC_2216, DESC_TABLE, DESC_N = 0x60515630, 0x6050dad4, 1589


def edits(img):
    assert hashlib.sha256(img).hexdigest() == EXPANDED_SHA, 'not E148 1.1 expanded main'
    R = lambda a, n: img[a - B:a - B + n]
    assert struct.unpack('<III', R(PAGE, 12)) == (0x16f, LIST, COUNT)
    stock = list(struct.unpack('<10H', R(LIST, 20)))
    assert stock == [0x8a3, 0x8a4, 0x8a5, 0x8a6, 0x8a7, 0x8a8, 0x8b0, 0x8b1, 0x8b2, 0x8b3], stock
    ids = [struct.unpack('<H', R(DESC_TABLE + 20 * k, 2))[0] for k in range(DESC_N)]
    assert 0x8a8 in ids and 0x8a9 not in ids and 0x8aa not in ids
    assert DESC_TABLE + 20 * ids.index(0x8a8) == DESC_2216
    d2216 = R(DESC_2216, 20)
    assert struct.unpack('<HHIIHHI', d2216) == (0x8a8, 0x80, 0x6050da8c, 0, 2, 1, 0x100) and R(0x6050da8c, 2) == b'\0\1'
    items = stock[:6] + [0x8a9, 0x8aa] + stock[6:]
    out = {'cp_button_items': (ITEMS, struct.pack('<12H', *items)),
           'cp_nd_descriptors': (DESC, b''.join(struct.pack('<H', i) + d2216[2:] for i in (0x8a9, 0x8aa))),
           'cp_button_page': (PAGE + 4, struct.pack('<II', ITEMS, len(items)))}
    assert ITEMS + 24 == DESC and DESC + 40 <= FREE_HI
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
    # the free region must not be claimed by another edit
    for e in spec['data_edits']:
        a = int(e['address'], 16)
        if e['name'] not in ('cp_button_items', 'cp_nd_descriptors') and a < FREE_HI and a + len(e['after']) // 2 > FREE_LO:
            sys.exit(f'{e["name"]} overlaps the free region')
    for name, (address, data) in edits(stock).items():
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
