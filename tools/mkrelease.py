#!/usr/bin/env python3
"""Make releases/NAME/patch.json from a strict build (tools/oly_patch.py --decoded) and the stock update file.

    python3 tools/mkrelease.py NAME BUILD_DIR STOCK.BIN [--camera-tested]

The release patch holds only what this project writes: the changed byte runs of the expanded main program, the
resource-ID aliases, and the hashes patch.py checks. patch.py needs no assembler to apply it."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from oly_container import parse, sha256
from oly_compress import expand_image

SRC = ROOT / 'firmware' / 'om5ii'


def runs(a, b, gap=8):
    out, i, n = [], 0, len(a)
    diff = [k for k in range(n) if a[k] != b[k]] if n < 1 << 16 else None
    if diff is None:
        import itertools
        diff = [k for k, (x, y) in enumerate(zip(a, b)) if x != y]
    start = prev = None
    for k in diff:
        if start is None:
            start = prev = k
        elif k - prev > gap:
            out.append((start, prev + 1)); start = prev = k
        else:
            prev = k
    if start is not None:
        out.append((start, prev + 1))
    return out


def main():
    name, build, stock = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    spec = json.loads((SRC / 'patch.json').read_text())
    report = json.loads((build / 'build.json').read_text())
    data = stock.read_bytes()
    blocks = {b.kind: b for b in parse(data)}
    base = int(spec['components']['0x100']['cpu_base'], 16)
    before = expand_image(blocks[0x100].payload)
    after = (build / 'decoded' / '0100.bin').read_bytes()
    edits = [{'address': hex(base + s), 'before_sha256': sha256(before[s:e]), 'bytes': after[s:e].hex()}
             for s, e in runs(before, after)]
    release = {
        'schema': 'caduceus-om5-release/1', 'name': name, 'model': 'OM-5 Mark II', 'model_code': 'E148',
        'firmware': '1.1', 'camera_tested': '--camera-tested' in sys.argv,
        'stock': {'file': 'OLY_E_148_1100_0000_0000.BIN', 'bytes': len(data), 'sha256': sha256(data)},
        'main': {'cpu_base': hex(base), 'expanded_before_sha256': sha256(before),
                 'expanded_after_sha256': sha256(after), 'stored_after_sha256': report['components']['0x100']['sha256'],
                 'edits': edits},
        'resource': {'aliases': spec['resource_aliases'][0]['aliases'],
                     'after_sha256': report['components']['0x101']['sha256']},
        'package': {'file': 'DCOLYMP/E1489999.BIN', 'bytes': report['package_bytes'], 'sha256': report['package_sha256']},
    }
    out = ROOT / 'releases' / name
    out.mkdir(parents=True, exist_ok=True)
    (out / 'patch.json').write_text(json.dumps(release, indent=1) + '\n')
    print(f'{out}/patch.json: {len(edits)} runs, {sum(len(e["bytes"]) // 2 for e in edits)} bytes, package {release["package"]["sha256"]}')


if __name__ == '__main__':
    main()
