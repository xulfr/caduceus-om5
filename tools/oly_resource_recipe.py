#!/usr/bin/env python3
"""Add image aliases or artwork IDs to a patch.json resource group and record the new record-0 LZ4 recipe.

    python3 tools/oly_resource_recipe.py firmware/om5ii --stock E148.BIN TARGET=SOURCE [...]
    python3 tools/oly_resource_recipe.py firmware/om5ii --stock E148.BIN --artwork ANCHOR=TARGET [...]
    python3 tools/oly_resource_recipe.py firmware/om5ii --stock E148.BIN --sprite TARGET=SOURCE:X0,Y0,X1,Y1 [...]
    python3 tools/oly_resource_recipe.py firmware/om5ii --stock E148.BIN --strips 'TARGET=[{"source": ...}, ...]'

TARGET=SOURCE points the placeholder TARGET at stock image SOURCE (resource_aliases). --artwork ANCHOR=TARGET
adds TARGET to the ids of the artwork sprite that already lists ANCHOR, so TARGET shows the same bitmap.
--sprite TARGET=SOURCE:X0,Y0,X1,Y1 adds a new artwork sprite for TARGET cropped from stock image SOURCE (appended
to record 37 like the other sprites). --strips TARGET=JSON does the same with a list of strips in the patch.json
artwork form (source, optional crop, width and pad_left), joined left to right, e.g. glyphs from several images.

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
from oly_resource import alias_images, _recipe, _append_artwork


def greedy(target, lo, hi, maxoff=65535, chain=64):
    """LZ4 sequences (literals, offset, match) for target[lo:hi]: greedy longest match with one-step lazy
    evaluation, matches reaching back up to maxoff bytes (also before lo). The last sequence may be a match;
    _recipe continues with the stock sequences after hi."""
    from collections import defaultdict
    heads = defaultdict(list)
    for i in range(max(0, lo - maxoff), lo):
        heads[target[i:i + 4]].append(i)

    def best(i):
        if i + 4 > hi:
            return 0, 0
        bn, bo = 0, 0
        for j in reversed(heads.get(target[i:i + 4], [])[-chain:]):
            if i - j > maxoff:
                break
            n = 0
            while i + n < hi and target[j + n] == target[i + n]:
                n += 1
            if n > bn:
                bn, bo = n, i - j
        return bn, bo
    out, start, i = [], lo, lo
    while i < hi:
        n, off = best(i)
        if n >= 4 and best(i + 1)[0] <= n + 1:
            out.append((i - start, off, n))
            for k in range(i, i + n):
                heads[target[k:k + 4]].append(k)
            i += n
            start = i
        else:
            heads[target[i:i + 4]].append(i)
            i += 1
    if start < hi:
        out.append((hi - start, 0, 0))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('patch'); p.add_argument('--stock', required=True); p.add_argument('alias', nargs='*')
    p.add_argument('--artwork', action='append', default=[], metavar='ANCHOR=TARGET')
    p.add_argument('--sprite', action='append', default=[], metavar='TARGET=SOURCE:X0,Y0,X1,Y1')
    p.add_argument('--strips', action='append', default=[], metavar='TARGET=JSON')
    a = p.parse_args()
    spec_path = Path(a.patch) / 'patch.json'
    spec = json.loads(spec_path.read_text())
    group = spec['resource_aliases'][0]
    stock = next(b for b in oly_patch.parse(Path(a.stock).read_bytes()) if b.kind == 0x101).payload
    aliases = [(int(t, 16), int(s, 16)) for t, s in group['aliases']]
    extra = [tuple(int(x, 16) for x in item.split('=')) for item in a.alias]
    art = [tuple(int(x, 16) for x in item.split('=')) for item in a.artwork]
    spr = []
    for item in a.sprite:
        target, rest = item.split('=')
        source, box = rest.split(':')
        spr.append((int(target, 16), [{'source': f'{int(source, 16):#x}', 'crop': [int(v) for v in box.split(',')]}]))
    for item in a.strips:
        target, rest = item.split('=', 1)
        strips = json.loads(rest)
        if not isinstance(strips, list) or not strips or any('source' not in st for st in strips):
            sys.exit('--strips needs a non-empty JSON list of strips with a source')
        spr.append((int(target, 16), strips))
    if not extra and not art and not spr:
        sys.exit('nothing to add')
    sprites = group.get('artwork', {}).get('sprites', [])
    listed = {int(i, 16) for sp in sprites for i in sp['ids']}
    new = [t for t, _ in extra] + [t for _, t in art] + [t for t, _ in spr]
    if len(set(new)) != len(new) or set(new) & ({t for t, _ in aliases} | listed):
        sys.exit('alias already present')
    import copy
    current = alias_images(stock, aliases, group['lz4_recipe'], copy.deepcopy(group.get('artwork')))
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
    if spr:
        group.setdefault('artwork', {}).setdefault('sprites', [])
        for target, strips in spr:
            if struct.unpack_from('<I', data, table + 4 * target)[0] != placeholder:
                sys.exit(f'{target:#x} is not a placeholder')
            group['artwork']['sprites'].append({'ids': [f'{target:#x}'], 'strips': strips})
        # The new sprites' pointers: build the whole block with the new artwork (record 37 re-encoded from the
        # stock stream) and read them back.
        free = copy.deepcopy(group['artwork'])
        del free['lz4_recipe']
        built = bytearray(stock)          # the artwork is appended to stock's record 37, as alias_images does
        first = struct.unpack_from('<I', built)[0]
        icons = _append_artwork(built, first - 2016, bytes(stock_decoded), load, table, free)
        built = bytes(built)
        for target, _ in spr:
            struct.pack_into('<I', data, table + 4 * target, icons[target])
        # Record 37's recipe: keep the current stream (stock sequences and the earlier artwork) and add the new
        # sprites' bytes, then take the window from the first sequence that differs from stock to the end.
        def rec37(payload):
            first = struct.unpack_from('<I', payload)[0]
            a37 = struct.unpack_from('<I', payload, 37 * 16)[0] - (first - 2016)
            n37, r37 = struct.unpack_from('<II', payload, a37 + 16)
            return _sequences(payload[a37 + 32:a37 + 32 + n37], r37)
        atlas = rec37(built)[0]
        cur_atlas, cur_rows37 = rec37(current)
        stock_rows37 = rec37(stock)[1]
        assert atlas[:len(cur_atlas)] == cur_atlas, 'new sprites must only append to the atlas'
        enc37 = _repack(cur_atlas, atlas, cur_rows37, split=True)
        if length_fault(len(enc37)):
            sys.exit(f'record 37 packed length {len(enc37)}: {length_fault(len(enc37))}')
        rows37 = _sequences(enc37, len(atlas))[1]
        h = 0
        while h < min(len(rows37), len(stock_rows37)) and rows37[h][:4] == stock_rows37[h][:4]:
            h += 1
        lo37 = rows37[h][3] - len(rows37[h][0])
        window37 = rows37[h:]
        rec = {'from': f'{lo37:#x}', 'to': f'{len(atlas):#x}',
               'sequences_le16': b''.join(struct.pack('<3H', len(r[0]), r[1], r[2]) for r in window37).hex()}
        if any(len(r[0]) > 0xffff or r[2] > 0xffff for r in window37):
            sys.exit('record 37: sequence too long for the le16 recipe form')
        if _recipe(atlas, stock_rows37, rec) != enc37:
            sys.exit('record 37 recipe does not reproduce the re-encoded stream')
        group['artwork']['lz4_recipe'] = rec
        print(json.dumps({'record37_packed': len(enc37), 'atlas': len(atlas), 'window': [rec['from'], rec['to']]}))
    encoded = _repack(decoded, bytes(data), rows, split=True)
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
    if len(encoded) + 32 > span:
        # Too long: encode the same window with a greedy LZ4 match search instead of OM's own sequences (stock
        # streams already use overlapping matches down to offset 1). Kept only if shorter; _recipe checks it.
        seqs = greedy(bytes(data), lo, hi)
        alt = {'from': recipe['from'], 'to': recipe['to'],
               'sequences_le16': b''.join(struct.pack('<3H', *q) for q in seqs).hex()}
        if any(q[0] > 0xffff or q[2] > 0xffff for q in seqs):
            sys.exit('greedy window: sequence too long for the le16 recipe form')
        alt_encoded = _recipe(bytes(data), stock_rows, alt)
        print(json.dumps({'split_packed': len(encoded), 'greedy_packed': len(alt_encoded)}))
        if len(alt_encoded) < len(encoded):
            recipe, encoded, window = alt, alt_encoded, seqs
    if length_fault(len(encoded)) or len(encoded) + 32 > span:
        sys.exit(f'packed length {len(encoded)}: {length_fault(len(encoded)) or "exceeds span"}')
    group['aliases'] = [[f'{t:#x}', f'{s:#x}'] for t, s in aliases + extra]
    group['lz4_recipe'] = recipe
    spec_path.write_text(json.dumps(spec, indent=2) + '\n')
    print(json.dumps({'packed': len(encoded), 'previous': packed, 'window': [recipe['from'], recipe['to']], 'sequences': len(window)}))


if __name__ == '__main__':
    main()
