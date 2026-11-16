#!/usr/bin/env python3
"""Audit an E148 decoded build against stock and an optional predecessor. No camera access."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import patch
from om5ii_boot_audit import audit_ranges, loader_regions, BASE


def resource_delta(current, previous, spec):
    """Image IDs whose record-0 pointer word differs from the previous build. Anything else that differs is
    refused: other records (bitmaps, language, fonts) byte for byte, and every decoded record-0 byte apart from
    the pointer words of aliases and artwork sprite IDs declared in patch.json."""
    from oly_compress import _sequences
    if current == previous:
        return []
    assert len(current) == len(previous)
    span = struct.unpack_from('<I', current, 4)[0]
    assert struct.unpack_from('<4I', current)[:2] == struct.unpack_from('<4I', previous)[:2], 'resource index changed'
    at = 2016
    # Record 37 (E148's last bitmap record) holds the appended artwork. It and its index span may differ from the
    # previous build only when the whole block equals an independent rebuild from stock and patch.json (checked
    # by the caller, rebuild_resources); everything else outside record 0 must be byte-identical.
    first = struct.unpack_from('<I', current)[0]
    a37 = struct.unpack_from('<I', current, 37 * 16)[0] - (first - at)
    assert a37 == struct.unpack_from('<I', previous, 37 * 16)[0] - (first - at)
    end37 = a37 + max(struct.unpack_from('<I', current, 37 * 16 + 4)[0], struct.unpack_from('<I', previous, 37 * 16 + 4)[0])
    index_ok = all(current[k] == previous[k] or 37 * 16 + 4 <= k < 37 * 16 + 8 for k in range(at))
    assert index_ok and current[at + span:a37] == previous[at + span:a37] and current[end37:] == previous[end37:], \
        'resource outside records 0 and 37 changed'
    def decode(blob):
        packed, raw = struct.unpack_from('<II', blob, at + 16)
        return _sequences(blob[at + 32:at + 32 + packed], raw)[0]
    new, old = decode(current), decode(previous)
    assert len(new) == len(old)
    load = struct.unpack_from('<I', new)[0] - 8
    table = struct.unpack_from('<I', new, 4)[0] - load
    declared = {int(t, 16) for g in spec.get('resource_aliases', []) for t, _ in g['aliases']}
    # Artwork sprite IDs are declared too, but every ID of one sprite must point at the same bitmap.
    word = lambda i: struct.unpack_from('<I', new, table + 4 * i)[0]
    for g in spec.get('resource_aliases', []):
        for sprite in g.get('artwork', {}).get('sprites', []):
            ids = [int(i, 16) for i in sprite['ids']]
            assert len({word(i) for i in ids}) == 1, f'artwork sprite {sprite["ids"][0]} IDs point at different bitmaps'
            declared.update(ids)
    words = sorted({(i - table) // 4 for i in range(len(new)) if new[i] != old[i]})
    for w in words:
        assert w >= 0 and w in declared, f'undeclared record-0 change at image ID {w:#x}'
    assert all(new[i] == old[i] or (i >= table and (i - table) // 4 in declared) for i in range(len(new)))
    return [hex(w) for w in words]


def rebuild_resources(resources, stock_payload, spec):
    """The build's resource block must equal one rebuilt here from stock and patch.json's aliases, recipe and
    artwork (oly_resource.alias_images), independently of the builder."""
    from oly_resource import alias_images
    for g in spec.get('resource_aliases', []):
        stock_payload = alias_images(stock_payload, [(int(t, 16), int(s, 16)) for t, s in g['aliases']],
                                     g.get('lz4_recipe'), g.get('artwork'))
    assert stock_payload == resources, 'resource block differs from a rebuild from stock and patch.json'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'stock', 'out'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--previous', type=Path, help='decoded predecessor build (default: stock)')
    a = ap.parse_args()
    spec = json.loads((ROOT / 'firmware/om5ii/patch.json').read_text())
    stock = a.stock.read_bytes()
    assert patch.sha256(stock) == spec['stock']['sha256']
    blocks = {b.kind: b for b in patch.parse(stock)}
    original = patch.expand_image(blocks[0x100].payload)
    current = (a.build / 'decoded/0100.bin').read_bytes()
    previous = (a.previous / 'decoded/0100.bin').read_bytes() if a.previous else original
    report = json.loads((a.build / 'build.json').read_text())
    assert len(original) == len(current) == len(previous)
    assert patch.sha256(current) == spec['components']['0x100']['after_sha256']
    assert patch.sha256(current) == report['components']['0x100']['expanded_sha256']
    resources = (a.build / 'decoded/0101.bin').read_bytes()
    assert patch.sha256(resources) == spec['components']['0x101']['after_sha256']
    rebuild_resources(resources, blocks[0x101].payload, spec)
    previous_resources = (a.previous / 'decoded/0101.bin').read_bytes() if a.previous else blocks[0x101].payload
    resource_change = resource_delta(resources, previous_resources, spec)
    regions = loader_regions(original)
    owners = audit_ranges(original, spec['ranges'], spec.get('data_edits', []))
    edits = [r for r in spec['ranges'] if r['component'] == '0x100' and 'address' in r]
    covered = bytearray(len(current))
    changed = {}
    for r in edits:
        start = int(r['address'], 16) - BASE
        end = start + r['bytes']
        assert patch.sha256(original[start:end]) == r['before_sha256'], r['name']
        assert patch.sha256(current[start:end]) == r['after_sha256'], r['name']
        assert not any(covered[start:end]), ('overlapping ranges', r['name'])
        covered[start:end] = b'\1' * r['bytes']
        n = sum(x != y for x, y in zip(previous[start:end], current[start:end]))
        if n:
            changed[r['name']] = {'bytes': n, 'section': owners[r['name']]}
    # Outside the declared ranges the build must equal stock. Bytes the previous build patched there and this one
    # leaves as stock (a section that got shorter) are counted, not refused.
    assert all(covered[i] or x == z for i, (x, z) in enumerate(zip(original, current))), 'unexplained edit'
    back_to_stock = sum(1 for i, (y, z) in enumerate(zip(previous, current)) if not covered[i] and y != z)
    # Native compressed-section descriptors and every end-selector instruction
    # must remain stock, independently of the patch manifest's declarations.
    start = 0x600284fc - BASE
    assert current[start:start + 120] == original[start:start + 120]
    start = 0x60047868 - BASE
    assert current[start:start + 40] == original[start:start + 40]
    for i in range(10):
        address, = struct.unpack_from('<I', original, start + 4*i)
        offset = address - BASE
        assert current[offset:offset + 6] == original[offset:offset + 6]
    module = importlib.util.spec_from_file_location('nd64', ROOT / 'firmware/om5ii/nd64.py')
    nd = importlib.util.module_from_spec(module)
    module.loader.exec_module(nd)
    nd_edits, cases = nd.check(original)
    for address, hex_bytes in nd_edits.items():
        offset, data = int(address, 16) - BASE, bytes.fromhex(hex_bytes)
        assert current[offset:offset + len(data)] == data, 'ND selector differs from tested bytes'
    result = {'camera_tested': False, 'package_sha256': report['package_sha256'],
              'previous_expanded_sha256': patch.sha256(previous),
              'expanded_sha256': patch.sha256(current), 'changed_ranges': changed,
              'all_edits_declared': True, 'previous_bytes_back_to_stock': back_to_stock, 'native_loader_bounds_unchanged': True,
              'resources_unchanged': resources == previous_resources, 'resource_alias_words_changed': resource_change,
              'nd_selector_cases': cases,
              'section_tail_space': {r['name']: next(s['end'] for s in regions if s['id'] == owners[r['name']])
                                     - int(r['address'], 16) - r['bytes']
                                     for r in edits if r['name'] in ('ext6', 'ext7', 'ext10')}}
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
