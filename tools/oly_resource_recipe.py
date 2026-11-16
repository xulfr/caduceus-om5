#!/usr/bin/env python3
"""Add image aliases or artwork IDs to a patch.json resource group and record the new record-0 LZ4 recipe.

    python3 tools/oly_resource_recipe.py firmware/om5ii --stock E148.BIN TARGET=SOURCE [...]
    python3 tools/oly_resource_recipe.py firmware/om5ii --stock E148.BIN --artwork ANCHOR=TARGET [...]

TARGET=SOURCE points the placeholder TARGET at stock image SOURCE (resource_aliases). --artwork ANCHOR=TARGET
adds TARGET to the ids of the artwork sprite that already lists ANCHOR, so TARGET shows the same bitmap.

The record-0 stream is re-encoded from the current recipe's own stream (oly_compress._repack with split
matches), so only the sequences around each changed pointer word differ. The recipe window is the span of
sequences that differ from the stock stream; it must start and end on stock sequence boundaries, and the
packed length must pass the loader's length rule (length_fault). Run tools/oly_patch_record.py afterwards to
re-record the hashes, and review the diff. No firmware is written or sent anywhere."""
import argparse, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import oly_patch
from oly_compress import _sequences, _repack, length_fault
from oly_resource import alias_images, _recipe


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('patch'); p.add_argument('--stock', required=True); p.add_argument('alias', nargs='*')
    p.add_argument('--artwork', action='append', default=[], metavar='ANCHOR=TARGET')
    a = p.parse_args()
    spec_path = Path(a.patch) / 'patch.json'
    spec = json.loads(spec_path.read_text())
    group = spec['resource_aliases'][0]
    stock = next(b for b in oly_patch.parse(Path(a.stock).read_bytes()) if b.kind == 0x101).payload
    aliases = [(int(t, 16), int(s, 16)) for t, s in group['aliases']]
    extra = [tuple(int(x, 16) for x in item.split('=')) for item in a.alias]
    art = [tuple(int(x, 16) for x in item.split('=')) for item in a.artwork]
    if not extra and not art:
        sys.exit('nothing to add')
    sprites = group.get('artwork', {}).get('sprites', [])
    listed = {int(i, 16) for sp in sprites for i in sp['ids']}
    new = [t for t, _ in extra] + [t for _, t in art]
    if len(set(new)) != len(new) or set(new) & ({t for t, _ in aliases} | listed):
        sys.exit('alias already present')
    current = alias_images(stock, aliases, group['lz4_recipe'], group.get('artwork'))
    at = 2016
    span = struct.unpack_from('<I', current, 4)[0]
    packed, raw = struct.unpack_from('<II', current, at + 16)
    decoded, rows = _sequences(current[at + 32:at + 32 + packed], raw)
    stock_packed = struct.unpack_from('<I', stock, at + 16)[0]
    stock_decoded, stock_rows = _sequences(stock[at + 32:at + 32 + stock_packed], raw)
    data = bytearray(decoded)
    load = struct.unpack_from('<I', data)[0] - 8
    table = struct.unpack_from('<I', data, 4)[0] - load
    placeholder = load + table - 20
    for target, source in extra:
        if struct.unpack_from('<I', data, table + 4 * target)[0] != placeholder:
            sys.exit(f'{target:#x} is not a placeholder')
        struct.pack_into('<I', data, table + 4 * target, struct.unpack_from('<I', stock_decoded, table + 4 * source)[0])
    for anchor, target in art:
        sprite = next((sp for sp in sprites if f'{anchor:#x}' in sp['ids']), None)
        if sprite is None:
            sys.exit(f'{anchor:#x} is not an artwork id')
        if struct.unpack_from('<I', data, table + 4 * target)[0] != placeholder:
            sys.exit(f'{target:#x} is not a placeholder')
        struct.pack_into('<I', data, table + 4 * target, struct.unpack_from('<I', data, table + 4 * anchor)[0])
        sprite['ids'].append(f'{target:#x}')
    encoded = _repack(decoded, bytes(data), rows, split=True)
    if length_fault(len(encoded)) or len(encoded) + 32 > span:
        sys.exit(f'packed length {len(encoded)}: {length_fault(len(encoded)) or "exceeds span"}')
    new_rows = _sequences(encoded, raw)[1]
    key = lambda r: (r[0], r[1], r[2], r[3])
    head = 0
    while head < min(len(new_rows), len(stock_rows)) and key(new_rows[head]) == key(stock_rows[head]):
        head += 1
    tail = 0
    while (tail < min(len(new_rows), len(stock_rows)) - head
           and key(new_rows[-1 - tail]) == key(stock_rows[-1 - tail])):
        tail += 1
    begin = lambda r: r[3] - len(r[0])
    lo = begin(new_rows[head])
    hi = begin(new_rows[len(new_rows) - tail]) if tail else raw
    window = new_rows[head:len(new_rows) - tail]
    recipe = {'from': f'{lo:#x}', 'to': f'{hi:#x}',
              'sequences_le16': b''.join(struct.pack('<3H', len(r[0]), r[1], r[2]) for r in window).hex()}
    if any(len(r[0]) > 0xffff or r[2] > 0xffff for r in window):
        sys.exit('sequence too long for the le16 recipe form')
    if _recipe(bytes(data), stock_rows, recipe) != encoded:
        sys.exit('recipe does not reproduce the re-encoded stream')
    group['aliases'] = [[f'{t:#x}', f'{s:#x}'] for t, s in aliases + extra]
    group['lz4_recipe'] = recipe
    spec_path.write_text(json.dumps(spec, indent=2) + '\n')
    print(json.dumps({'packed': len(encoded), 'previous': packed, 'window': [recipe['from'], recipe['to']], 'sequences': len(window)}))


if __name__ == '__main__':
    main()
