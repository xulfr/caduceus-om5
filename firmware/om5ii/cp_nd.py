#!/usr/bin/env python3
"""Live ND32/ND64 in CP Button Settings and Color Profile Shading for OM-5 Mark II (E148 1.1): data edits.

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
Setting 2228 is the CP button's current item (1 + the item index k of the CP table 0x60f7f57c; k 6, 7 are ND32,
ND64). Its stock allowed values are 1..6, 14..17 (list 0x6050da8e), and the CP carousel lists exactly the allowed
values (GUI 0x60e27d22 iterates them through the data model, count +24 / value +28), so ND32 and ND64 never appear
when the CP button is held, even when ticked (alpha9 camera report). The selector 0x60d1d7da, the item mapping
0x60d2211a / 0x60d22182 and the GUI case 0x60e27f92 already handle items 6 and 7. Same method as nd64.py's 1710
edit. Not changed: the "any item ticked" test 0x60d2230f still skips items 6..12 (ND32 / ND64 alone, with every
other CP item unticked, is still treated as nothing ticked). 2026-11-17.
 6. mono_filter_word 0x610d9738: the Monochrome colour filter page's word image (layout record of view
    0x610d9b20, the only reference is its widget list at 0x610d9988) 0x107e "Vivid" -> 0xffff (no image).
    The word beside the level "+n" is "Level" on the OM-3 (E147 1.1, OM-Emu); hsl.s paint_filter draws it.
    The page is shown only when armed (pages_hook). 2026-11-17.
 7. mono_filter_icon 0x610d97be, mono_filter_value 0x610d979e: the same page's widget rectangles {x, y, w, h}
    for its two layouts (x + 80 in the second). Drawn in font 1, "Level" is about 66 px wide and the stock
    gap between the rear-dial icon (widget 0x3d8) and the "+n" value (widget 0x3e2) is 58 px, so the icon
    moves 10 left and the value 10 right. Each rectangle has one reference (its widget descriptor).
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
DESC_2228, VALUES_2228, NEW_VALUES = 0x60515694, 0x6050da8e, 0x604f2554
MONO_WORD = 0x610d972c          # filter page layout record {0xffff, 7, 7, image}
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
                                 + b''.join(struct.pack('<H', i) + d1017[2:] for i in SHADING)),
           'cp_button_page': (PAGE + 4, struct.pack('<II', ITEMS, len(items)))}
    assert ITEMS + 24 == DESC and DESC + 100 == NEW_VALUES and NEW_VALUES + 2 * len(CP_VALUES) <= FREE_HI
    d2228 = R(DESC_2228, 20)
    assert struct.unpack('<HHIIHHI', d2228) == (2228, 0x80, VALUES_2228, 0, 20, 2, 0x500)
    assert struct.unpack('<10h', R(VALUES_2228, 20)) == (1, 2, 3, 4, 5, 6, 14, 15, 16, 17)
    out['cp_item_values'] = (NEW_VALUES, struct.pack('<12H', *CP_VALUES))
    out['cp_item_desc'] = (DESC_2228, struct.pack('<HHIIHHI', 2228, 0x80, NEW_VALUES, 0, 2 * len(CP_VALUES), 2, 0x500))
    assert struct.unpack('<5I', R(MONO_WORD, 20)) == (0xffff, 7, 7, 0x107e, 0)
    assert img.count(struct.pack('<I', MONO_WORD)) == 1 and struct.unpack('<I', R(0x610d9988, 4))[0] == MONO_WORD
    out['mono_filter_word'] = (MONO_WORD + 12, struct.pack('<I', 0xffff))
    for name, rect, ref, stock_xy, dx in (('mono_filter_icon', 0x610d97be, 0x610d98a4, (537, 461, 36, 24), -10),
                                          ('mono_filter_value', 0x610d979e, 0x610d9834, (647, 458, 29, 30), 10)):
        x, y, w, h = stock_xy
        assert struct.unpack('<8h', R(rect, 16)) == (x, y, w, h, x + 80, y, w, h), name
        assert img.count(struct.pack('<I', rect)) == 1 and struct.unpack('<I', R(ref, 4))[0] == rect, name
        out[name] = (rect, struct.pack('<8h', x + dx, y, w, h, x + 80 + dx, y, w, h))
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
        if e['name'] not in ('cp_button_items', 'cp_nd_descriptors', 'cp_item_values') and a < FREE_HI and a + len(e['after']) // 2 > FREE_LO:
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
