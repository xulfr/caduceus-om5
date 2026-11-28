#!/usr/bin/env python3
"""The colour wheel's keys as on the OM-3 v0.41 (owner, 2026-11-28): emulator regressions on a strict decoded E148
build.

INFO steps Hue -> Saturation -> Lightness (the wheel opens on Saturation, so S -> L -> H -> S). The colour dial (the
rear dial on this body; OM-Emu's "sub") past the first colour gives Sat. All: OM's own ring, whose place 0 between
colour 12 and colour 1 is all colours. On Hue and Lightness that place is skipped. INFO with all colours on goes back
to colour 1 and on to Lightness. Delete does nothing on the wheel. The hint reads "H/S/L [INFO]" on every axis.
tests/wheel_keys_assert.mjs reads the settings and P after the keys. Emulator only: not a camera result.

    python tests/run_wheel_keys.py --emu OM_EMU_DIR --build generated/strict --out generated/wheel-keys
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
WHEEL = 's1 ok ok ' + 'right ' * 8 + 'down '     # Picture Mode, Color Profile 1, the colour wheel row
COLOUR1, COLOUR12 = 928, 939
HINT = (288, 420, 434, 464)                       # x0, y0, x1, y1: "H/S/L" and OM's INFO key under the wheel
# (name, keys, expectation, axes after each INFO press or None, seed cells or None)
CASES = [
    ('info-steps-hsl', 'info info info', dict(axis=0, cur=COLOUR1, one=1), [2, 1, 0], None),
    ('info-edits-each-axis', 'main+1 info main+2 info main+3 info',
     dict(axis=0, cur=COLOUR1, sat={0: 1}, light={0: 2}, hue={0: 3}), [2, 1, 0], None),
    ('delete-does-nothing', 'main+1 delete delete', dict(axis=0, sat={0: 1}), None, None),
    ('sat-all-by-dial', 'sub+1 main+1', dict(axis=0, cur=0, satAll=1), None, None),
    ('sat-all-and-back', 'sub+1 sub-1 main+1', dict(axis=0, cur=COLOUR1, sat={0: 1}), None, None),
    ('info-from-sat-all', 'sub+1 info main+1', dict(axis=2, cur=COLOUR1, light={0: 1}), [2], None),
    ('hue-skips-all', 'info info sub+1 main+1', dict(axis=1, cur=COLOUR12, hue={11: 1}), [2, 1], None),
    ('lightness-skips-all', 'info sub+1 sub-1 main+1', dict(axis=2, cur=COLOUR1, light={0: 1}), [2], None),
    # Earlier builds left OM's one / all cell at "all" with INFO; INFO now puts it back to one colour.
    ('info-restores-one', 'info', dict(axis=2, one=1), [2], {2197: 0}),
]


def region(png, box):
    """The box's pixels of a frame tools/dev/sess.mjs wrote (RGBA, filter 0 on every row)."""
    data, pos, idat, w = png.read_bytes(), 8, b'', 0
    while pos < len(data):
        n, kind = struct.unpack('>I4s', data[pos:pos + 8])
        if kind == b'IHDR':
            w = struct.unpack('>I', data[pos + 8:pos + 12])[0]
        if kind == b'IDAT':
            idat += data[pos + 8:pos + 8 + n]
        pos += 12 + n
    raw, (x0, y0, x1, y1), row = zlib.decompress(idat), box, 4 * w + 1
    return b''.join(raw[y * row + 1 + 4 * x0:y * row + 1 + 4 * x1] for y in range(y0, y1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--case', action='append')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    results, failed = [], []
    for name, keys, want, axes, seed in CASES:
        if a.case and name not in a.case:
            continue
        folder = a.out.resolve() / name
        env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tests/seed_cells.mjs'), OM5_SEED=json.dumps(seed or {}),
                   POST=str(ROOT / 'tests/wheel_keys_assert.mjs'), OM5_WHEEL_EXPECT=json.dumps(want))
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), WHEEL + keys, '--ready', '--peekP']
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=400)
        log = run.stdout.decode('utf-8', errors='replace')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'session.log').write_text(log, encoding='utf-8')
        got = [line[len('WHEEL KEYS '):] for line in log.splitlines() if line.startswith('WHEEL KEYS ')]
        ok, note = run.returncode == 0 and 'ASSERTIONS passed' in log and bool(got), ''
        steps = [line for line in log.splitlines() if line.split(':')[0] in ('down', 'info', 'delete', 'main+1', 'sub+1')]
        seen = [int(line.split('axis=')[1].split()[0]) for line in steps if line.startswith('info:')]
        if ok and axes is not None and seen != axes:
            ok, note = False, f' axes after INFO {seen}, expected {axes}'
        shots = sorted((folder / 'screens').glob('*.png'))
        if ok and name == 'delete-does-nothing':
            # Delete changes nothing on screen: the frames after main+1 and after each Delete are the same
            frames = [line.split()[2] for line in log.splitlines() if line.startswith(('main+1:', 'delete:'))]
            if len(frames) != 3 or len(set(frames)) != 1:
                ok, note = False, f' the screen changed on Delete: {frames}'
        if ok and name == 'info-steps-hsl':
            # the same "H/S/L [INFO]" hint on Saturation, Lightness and Hue, and something drawn there
            pick = [f for f in shots if f.name.split('-', 1)[1].startswith(('down', 'info'))]
            hints = [region(f, HINT) for f in pick]
            if len(hints) != 4 or len(set(hints)) != 1 or len(set(hints[0][i:i + 4] for i in range(0, len(hints[0]), 4))) < 2:
                ok, note = False, ' the hint differs between axes or is blank'
        results.append(dict(case=name, passed=ok, expected=want, axes=seen, observed=json.loads(got[-1]) if got else None))
        print(f'{name}: {"passed" if ok else "FAILED"}{note}' + ('' if ok else f' (see {folder}/session.log)'), flush=True)
        if not ok:
            failed.append(name)
    (a.out / 'results.json').write_text(json.dumps(dict(emulator_only=True, camera_tested=False, cases=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
