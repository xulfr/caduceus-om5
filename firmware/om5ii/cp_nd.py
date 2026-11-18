#!/usr/bin/env python3
"""Live ND32/ND64 in CP Button Settings, Color Profile Shading and Color Profile grain for OM-5 Mark II (E148 1.1):
data edits.

    cp_nd.py --spec STOCK.BIN      check stock and (re)write the three rows in patch.json

Stock (emulator and static evidence, 2026-11-16):
 * Menu page 0x16f (CP Button Settings) takes its item IDs from the page table entry at 0x611943a4
   {u32 page, u32 list, u32 count}: list 0x61193dc0, 10 IDs 2211..2216, 2224..2227. The item records at
   0x611d0c6c.. (stride 28) also hold 2217 "Live ND Shooting : ND32(5EV)" and 2218 "...ND64(6EV)", and the CP
   ND selector 0x60d1d7da / table 0x60f7cc00 already maps CP items 2..7 to ND steps 1..6.
 * Settings 2217 / 2218 have cells (they read 1) but no descriptor among the 1589 static ones at 0x6050dad4,
   so OM's writer drops a change. hsl.s cp_nd_link links the descriptors below into the RAM hash.
 * Color Profile Shading 912..914 (Color Profile 1..3) has no descriptor either, so the Picture Mode slider
   draws disabled (grey) and its dial changes are dropped (alpha9 camera report). Monochrome Shading 1017..1019
   has one (0x60512868: 11 values -5..5, table 0x6050cee0); 912..914 get copies of it. 2026-11-17.
Edits (all inside the 504/505 record copies that color_profiles.py frees, 0x604f24d8..0x604f25e0):
 1. cp_button_items  0x604f24d8: the stock list with 2217, 2218 after 2216 (12 IDs).
 2. cp_nd_descriptors 0x604f24f0: 2216's descriptor (0x60515630) twice, id 2217 and 2218, then 1017's
    descriptor (0x60512868) three times, id 912, 913 and 914 (5 x 20 bytes).
 3. cp_button_page   0x611943a8: page 0x16f's list pointer and count -> edit 1, 12.
 4. cp_item_values   0x604f2554: setting 2228's allowed values with 7, 8 (ND32, ND64) added:
    1..8, 14..17 (12 halfwords).
 5. cp_item_desc     0x60515694: 2228's static descriptor pointed at edit 4, length 24 bytes.
 v0.2.0 moves edit 4 to 0x604f2590 so that edit 2 can carry three more descriptors (Color Profile grain).

Color Profile grain (v0.2.0, emulator and static evidence, 2026-11-18):
 * The Picture Mode sidebar rows come from 0x60e376c3: Color Profile 1-4 use the list 0x6119a0f0 (6 row items:
   111, 0x14fe, 0x14ff, 0x1500, 7, 8), Monochrome Profiles 0x6119a0d0 (8 items, with grain 0x1501 and toning 0x83).
 * Row item 0x1501 resolves to its setting through 0x60e3d0f5 (dispatch 0x611a0a98, key 0x1501 - 6): the
   setting 111 value is looked up in {u32 mode, u32 id} table 0x611a02f8 with 4 entries 57..59, 65 -> 999..1002.
   A second copy of that lookup (0x60e4b32e, table 0x611b5ad0, 4 entries) serves the same IDs.
 * The grain value is stored in 907 / 911 / 915 (Color Profile 4's Sharpness, Contrast and Shading value cells;
   E148 has no Color Profile 4, no stock descriptor exists for them, and their part 1 (WB records) is separate).
   Each gets a copy of 999's descriptor (4 values, list 0x6050ced8). hsl.s writes effective 998 = 907 + 4p.
 6. cp_grain_table   0x604f25a8: 57..59, 65 -> 999..1002 as stock, then 54..56 -> 907, 911, 915 (7 x 8 bytes).
 7. cp_grain_rows    0x604ef064: the Color Profile row list with 0x1501 appended (7 x 4 bytes); in the tail of
    111's old record table that color_profiles.py frees and does not fill.
 8. cp_grain_lookup_a 0x60e3d10b / cp_grain_count_a 0x60e3d120, and _b 0x60e4b344 / 0x60e4b359: both lookups
    take table 6 with 7 entries.
 9. cp_grain_list    0x60e376c3 / cp_grain_list_count 0x60e376c9: the Color Profile case takes list 7, 7 items.
Setting 2228 is the CP button's current item (1 + the item index k of the CP table 0x60f7f57c; k 6, 7 are ND32,
ND64). Its stock allowed values are 1..6, 14..17 (list 0x6050da8e), and the CP carousel lists exactly the allowed
values (GUI 0x60e27d22 iterates them through the data model, count +24 / value +28), so ND32 and ND64 never appear
when the CP button is held, even when ticked (alpha9 camera report). The selector 0x60d1d7da, the item mapping
0x60d2211a / 0x60d22182 and the GUI case 0x60e27f92 already handle items 6 and 7. Same method as nd64.py's 1710
edit. The "any item ticked" test 0x60d2230f skipped items 6 and 7 (ND32 / ND64 alone, with every other CP
item unticked, was treated as nothing ticked); hsl.s cp_any_nd adds them once armed (items 8..12 are not on the
CP Button page and stay skipped). Static analysis: OM-Emu has no CP button for E148, and calling 0x60d2230f
from the lab task faults in its setting read. 2026-11-17.
"""
import hashlib, json, struct, sys
from pathlib import Path

B = 0x60021020
EXPANDED_SHA = '7ae7d4c60990cc859c070e0ceb6cbe612f9c5b260713f2f1256e51d137851c61'
PAGE, LIST, COUNT = 0x611943a4, 0x61193dc0, 10
ITEMS, DESC = 0x604f24d8, 0x604f24f0
FREE_LO, FREE_HI = 0x604f24d8, 0x604f25e0
DESC_2216, DESC_TABLE, DESC_N = 0x60515630, 0x6050dad4, 1589
DESC_1017, SHADING = 0x60512868, (912, 913, 914)
DESC_2228, VALUES_2228, NEW_VALUES = 0x60515694, 0x6050da8e, 0x604f2590
DESC_999, GRAIN = 0x605127f0, (907, 911, 915)
GRAIN_TABLE, ROWS = 0x604f25a8, 0x604ef064
ROWS_LO, ROWS_HI = 0x604ef064, 0x604ef120  # 111's old record table tail (color_profiles.py OLD_REC + 41 x 64)
CP_VALUES = (1, 2, 3, 4, 5, 6, 7, 8, 14, 15, 16, 17)


def edits(img):
    assert hashlib.sha256(img).hexdigest() == EXPANDED_SHA, 'not E148 1.1 expanded main'
    R = lambda a, n: img[a - B:a - B + n]
    assert struct.unpack('<III', R(PAGE, 12)) == (0x16f, LIST, COUNT)
    stock = list(struct.unpack('<10H', R(LIST, 20)))
    assert stock == [0x8a3, 0x8a4, 0x8a5, 0x8a6, 0x8a7, 0x8a8, 0x8b0, 0x8b1, 0x8b2, 0x8b3], stock
    ids = [struct.unpack('<H', R(DESC_TABLE + 20 * k, 2))[0] for k in range(DESC_N)]
    assert 0x8a8 in ids and 0x8a9 not in ids and 0x8aa not in ids
    assert 1017 in ids and not set(SHADING) & set(ids)
    assert 999 in ids and not set(GRAIN) & set(ids)
    assert DESC_TABLE + 20 * ids.index(999) == DESC_999
    d999 = R(DESC_999, 20)
    assert struct.unpack('<HHIIHHI', d999) == (999, 0x80, 0x6050ced8, 0, 4, 1, 0x200)
    assert R(0x6050ced8, 4) == bytes(range(4))
    assert DESC_TABLE + 20 * ids.index(1017) == DESC_1017
    d1017 = R(DESC_1017, 20)
    assert struct.unpack('<HHIIHHI', d1017) == (1017, 0x80, 0x6050cee0, 0, 11, 1, 0x200)
    assert R(0x6050cee0, 11) == bytes(range(0xfb, 0x100)) + bytes(range(6))
    assert DESC_TABLE + 20 * ids.index(0x8a8) == DESC_2216
    d2216 = R(DESC_2216, 20)
    assert struct.unpack('<HHIIHHI', d2216) == (0x8a8, 0x80, 0x6050da8c, 0, 2, 1, 0x100) and R(0x6050da8c, 2) == b'\0\1'
    items = stock[:6] + [0x8a9, 0x8aa] + stock[6:]
    out = {'cp_button_items': (ITEMS, struct.pack('<12H', *items)),
           'cp_nd_descriptors': (DESC, b''.join(struct.pack('<H', i) + d2216[2:] for i in (0x8a9, 0x8aa))
                                 + b''.join(struct.pack('<H', i) + d1017[2:] for i in SHADING)
                                 + b''.join(struct.pack('<H', i) + d999[2:] for i in GRAIN)),
           'cp_button_page': (PAGE + 4, struct.pack('<II', ITEMS, len(items)))}
    assert ITEMS + 24 == DESC and DESC + 160 == NEW_VALUES and NEW_VALUES + 2 * len(CP_VALUES) == GRAIN_TABLE
    d2228 = R(DESC_2228, 20)
    assert struct.unpack('<HHIIHHI', d2228) == (2228, 0x80, VALUES_2228, 0, 20, 2, 0x500)
    assert struct.unpack('<10h', R(VALUES_2228, 20)) == (1, 2, 3, 4, 5, 6, 14, 15, 16, 17)
    out['cp_item_values'] = (NEW_VALUES, struct.pack('<12H', *CP_VALUES))
    out['cp_item_desc'] = (DESC_2228, struct.pack('<HHIIHHI', 2228, 0x80, NEW_VALUES, 0, 2 * len(CP_VALUES), 2, 0x500))
    # Color Profile grain
    stock_grain = [(57, 999), (58, 1000), (59, 1001), (65, 1002)]
    for table in (0x611a02f8, 0x611b5ad0):
        assert list(struct.iter_unpack('<II', R(table, 32))) == stock_grain
    grain = stock_grain + list(zip((54, 55, 56), GRAIN))
    assert GRAIN_TABLE + 8 * len(grain) == FREE_HI
    out['cp_grain_table'] = (GRAIN_TABLE, b''.join(struct.pack('<II', *e) for e in grain))
    # mov imm32,a0 (fc dc) ... cmp 4,d2 (aa 04) in both lookups
    for name, mov, cmp, table in (('a', 0x60e3d10b, 0x60e3d120, 0x611a02f8), ('b', 0x60e4b344, 0x60e4b359, 0x611b5ad0)):
        assert R(mov, 6) == b'\xfc\xdc' + struct.pack('<I', table) and R(cmp, 2) == b'\xaa\x04'
        out['cp_grain_lookup_' + name] = (mov + 2, struct.pack('<I', GRAIN_TABLE))
        out['cp_grain_count_' + name] = (cmp + 1, bytes([len(grain)]))
    stock_rows = (0x6f, 0x14fe, 0x14ff, 0x1500, 7, 8)
    assert struct.unpack('<6I', R(0x6119a0f0, 24)) == stock_rows
    assert struct.unpack('<8I', R(0x6119a0d0, 32))[6] == 0x1501
    rows = stock_rows + (0x1501,)
    assert ROWS_LO <= ROWS and ROWS + 4 * len(rows) <= ROWS_HI
    out['cp_grain_rows'] = (ROWS, struct.pack('<7I', *rows))
    # mov imm32,a3 (fc df) then mov 6,d0 (80 06); the Monochrome case beside it is mov 8,d0
    assert R(0x60e376c3, 8) == b'\xfc\xdf' + struct.pack('<I', 0x6119a0f0) + b'\x80\x06'
    assert R(0x60e376b9, 8) == b'\xfc\xdf' + struct.pack('<I', 0x6119a0d0) + b'\x80\x08'
    out['cp_grain_list'] = (0x60e376c5, struct.pack('<I', ROWS))
    out['cp_grain_list_count'] = (0x60e376ca, bytes([len(rows)]))
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
        mine = e['name'] in ('cp_button_items', 'cp_nd_descriptors', 'cp_item_values', 'cp_grain_table', 'cp_grain_rows')
        for lo, hi in ((FREE_LO, FREE_HI), (ROWS_LO, ROWS_HI)):
            if not mine and a < hi and a + len(e['after']) // 2 > lo:
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
