#!/usr/bin/env python3
"""Hold OK and OM's "changed" hint on a Color Profile holding a look (v0.2.0-dev): emulator regressions on a strict
decoded E148 build.

Each case applies look 1 of tools/dev/films-test.json to Color Profile 1 (trash on the mode strip), changes one row
with a dial, holds OK, and checks with tests/look_defaults_assert.mjs that the row went back to the look (Black /
White and a slot without a look: to 0). Where a case names two steps, OM's "Reset OK Hold" hint (the screen's
bottom-right corner) must appear with the change and look after the reset as it did before the change: hidden, as
the row matches the look again. Emulator only: not a camera result.
research/OM5II-LOOK-DEFAULTS-2026-11-27.md.

    python tests/run_look_defaults.py --emu OM_EMU_DIR --build generated/strict --out generated/look-defaults
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from card.mklooks import looks_bin

CP1 = 's1 ok ok ' + 'right ' * 8      # Picture Mode, Color Profile 1 highlighted
LOOK = CP1 + 'delete '                 # Color Profile 1 takes look 1 (Portra 400)
HOLD = 'hold:ok:3000'                  # OM-Emu: 1.5 s is not a long press, 3 s is
HINT = (480, 418, 712, 466)             # x0, y0, x1, y1 of the "Reset OK Hold" hint on the wheel and tone pages
# (name, keys, expectation, (step before the change, the change, the reset)): the hint shows after the change only
CASES = [
    ('wheel-saturation', LOOK + 'down main+1 ' + HOLD, dict(film=0), ('down', 'main+1', HOLD)),
    # INFO steps Saturation -> Lightness -> Hue (OM-3 v0.41 key map, 2026-11-28)
    ('wheel-hue', LOOK + 'down info info main+1 ' + HOLD, dict(film=0), ('info', 'main+1', HOLD)),
    ('wheel-lightness', LOOK + 'down info main+1 ' + HOLD, dict(film=0), None),
    ('tone', LOOK + 'down down down sub+1 main+1 ' + HOLD, dict(film=0), ('down', 'main+1', HOLD)),
    # The Black / White state: OM's tone IDs write Black / White, which no look holds: 0, tone stays the look's.
    ('tone-black-white', LOOK + 'down down down info sub+2 main-3 ' + HOLD, dict(film=0), None),
    # No look on the slot: OM's default, 0, as before (the wheel's colour 0 keeps the +1 set on it).
    ('no-look', CP1 + 'down main+1 down down sub+1 ' + HOLD, dict(film=None, sat0=1), None),
]


def corner(png):
    """The HINT region's pixels of a frame tools/dev/sess.mjs wrote (RGBA, 8 bit, filter 0 on every row)."""
    data, pos, idat = png.read_bytes(), 8, b''
    while pos < len(data):
        n = int.from_bytes(data[pos:pos + 4], 'big'); kind = data[pos + 4:pos + 8]
        if kind == b'IHDR':
            w = int.from_bytes(data[pos + 8:pos + 12], 'big')
        if kind == b'IDAT':
            idat += data[pos + 8:pos + 8 + n]
        pos += 12 + n
    raw, x0, y0, x1, y1 = zlib.decompress(idat), *HINT
    row = 4 * w + 1
    return b''.join(raw[y * row + 1 + 4 * x0:y * row + 1 + 4 * x1] for y in range(y0, y1))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--case', action='append')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    card = a.out.resolve() / 'card'
    (card / 'OM5MOD').mkdir(parents=True)
    (card / 'OM5MOD' / 'LOOKS.BIN').write_bytes(looks_bin(json.loads((ROOT / 'tools/dev/films-test.json').read_text())))
    results, failed = [], []
    for name, keys, want, same in CASES:
        if a.case and name not in a.case:
            continue
        folder = a.out.resolve() / name
        env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tests/layout_guard.mjs'), OM5_UNMOUNTED='0',
                   POST=str(ROOT / 'tests/look_defaults_assert.mjs'), OM5_LOOK_EXPECT=json.dumps(want))
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), keys, '--ready', '--card=' + str(card)]
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=400)
        log = run.stdout.decode('utf-8', errors='replace')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'session.log').write_text(log, encoding='utf-8')
        got = [line[len('LOOK DEFAULTS '):] for line in log.splitlines() if line.startswith('LOOK DEFAULTS ')]
        ok = run.returncode == 0 and 'ASSERTIONS passed' in log and bool(got)
        note = ''
        if ok and same:
            shots = sorted((folder / 'screens').glob('*.png'))
            pick = lambda tok: [f for f in shots if f.name.split('-', 1)[1].startswith(tok.replace(':', '_', 1))][-1]
            before, changed, after = (corner(pick(t)) for t in same)
            if changed == before:
                ok, note = False, ' no Reset OK Hold hint after the change'
            elif before != after:
                ok, note = False, ' the Reset OK Hold corner differs after the reset from before the change'
        results.append(dict(case=name, passed=ok, expected=want, observed=json.loads(got[-1]) if got else None))
        print(f'{name}: {"passed" if ok else "FAILED"}{note}' + ('' if ok else f' (see {folder}/session.log)'), flush=True)
        if not ok:
            failed.append(name)
    (a.out / 'results.json').write_text(json.dumps(dict(emulator_only=True, camera_tested=False, cases=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
