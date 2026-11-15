#!/usr/bin/env python3
"""Audit an E148 decoded build against stock and its predecessor. No camera access."""
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'previous', 'stock', 'out'):
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    spec = json.loads((ROOT / 'firmware/om5ii/patch.json').read_text())
    stock = a.stock.read_bytes()
    assert patch.sha256(stock) == spec['stock']['sha256']
    blocks = {b.kind: b for b in patch.parse(stock)}
    original = patch.expand_image(blocks[0x100].payload)
    current = (a.build / 'decoded/0100.bin').read_bytes()
    previous = (a.previous / 'decoded/0100.bin').read_bytes()
    report = json.loads((a.build / 'build.json').read_text())
    assert len(original) == len(current) == len(previous)
    assert patch.sha256(current) == spec['components']['0x100']['after_sha256']
    assert patch.sha256(current) == report['components']['0x100']['expanded_sha256']
    resources = (a.build / 'decoded/0101.bin').read_bytes()
    assert patch.sha256(resources) == spec['components']['0x101']['after_sha256']
    assert resources == (a.previous / 'decoded/0101.bin').read_bytes(), 'resource block changed'
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
    assert all(covered[i] or (x == y == z) for i, (x, y, z) in enumerate(zip(original, previous, current))), 'unexplained edit'
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
              'all_edits_declared': True, 'native_loader_bounds_unchanged': True,
              'resources_unchanged': True, 'nd_selector_cases': cases,
              'section_tail_space': {r['name']: next(s['end'] for s in regions if s['id'] == owners[r['name']])
                                     - int(r['address'], 16) - r['bytes']
                                     for r in edits if r['name'] in ('ext6', 'ext7', 'ext10')}}
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
