#!/usr/bin/env python3
"""Tone Curve row icon of the Color Profile screen in all 27 tone states (OM-Emu, E148 only).

    python tests/run_tone_icons.py --emu OM_EMU --build BUILD --out NEW_DIR

The row asks for image 0x38cc when Shadows, Midtones and Highlights are all 0 and for 0x38cd..0x38e6 in the
other 26 sign combinations; all 27 are empty placeholders in E148. They are aliased to E148's own gradation
icon and its 26 Highlight & Shadow glyphs (firmware/om5ii/patch.json, resource_aliases). The session steps
Shadows (front dial), Highlights (rear dial) and Midtones (after INFO) through every combination of -1, 0, +1
and reads the selected row of each frame. The icon must never be blank, the 27 states must give 27 different
icons, and with Midtones at 0 the glyph's curve must bend the way the two values say. Emulator only.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_page_graphics import OPEN, frame, px

ROOT = Path(__file__).resolve().parents[1]
X0, Y0, X1, Y1 = 4, 184, 84, 236        # inside the selected row's cell
LIT = 150                               # luma above the highlighted cell's fill


def walk():
    """Keys and (shadows, highlights, midtones) after each key."""
    keys, states, s = [], [], [0, 0, 0]

    def step(key, part=None, by=0):
        if part is not None:
            s[part] += by
        keys.append(key)
        states.append(tuple(s))

    def plane():
        for key, part, by in (('main+1', 0, 1), ('sub-1', 1, 1), ('main-1', 0, -1), ('main-1', 0, -1),
                              ('sub+1', 1, -1), ('sub+1', 1, -1), ('main+1', 0, 1), ('main+1', 0, 1),
                              ('sub-1', 1, 1), ('main-1', 0, -1)):
            step(key, part, by)

    plane()
    step('info'); step('main+1', 2, 1); step('info'); plane()
    step('info'); step('main-1', 2, -1); step('main-1', 2, -1); step('info'); plane()
    return keys, states


def icon(rows):
    return frozenset((x, y) for y in range(Y0, Y1) for x in range(X0, X1) if px(rows, x, y)[0] > LIT)


def bend(lit):
    """Mean height of the glyph's curve above its diagonal in the lower-left and upper-right halves."""
    xs, ys = [p[0] for p in lit], [p[1] for p in lit]
    left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
    if right - left != 25 or bottom - top != 25:        # the 28 x 28 glyph's frame (the 0 state has a caption)
        return None
    low, high = [], []
    for x in range(left + 3, right - 2):
        column = [y for y in range(top + 3, bottom - 2) if (x, y) in lit]
        if column:
            above = (bottom - (x - left)) - sum(column) / len(column)
            (low if x - left < 11 else high if x - left > 15 else []).append(above)
    return sum(low) / len(low), sum(high) / len(high)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    keys, states = walk()
    lead = (OPEN + 'down down').split()
    cmd = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()), str(a.build.resolve() / 'decoded/0100.bin'),
           str(a.build.resolve() / 'decoded/0101.bin'), str(a.out / 'tone'), ' '.join(lead + keys), '--ready']
    env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tools/dev/mount.mjs'))
    run = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1800)
    (a.out / 'session.log').write_bytes(run.stdout)
    if run.returncode:
        sys.exit(f'session failed; see {a.out / "session.log"}')
    frames = {int(p.name[:2]): p for p in (a.out / 'tone').glob('[0-9][0-9]-*.png')}
    seen, faults = {}, []
    for n, state in enumerate(states):
        lit = icon(frame(frames[len(lead) + 1 + n]))
        if len(lit) < 60:
            faults.append(f'{state}: blank icon after {keys[n]}')
            continue
        if seen.setdefault(state, lit) != lit:
            faults.append(f'{state}: icon differs between two visits')
        if state[2] == 0 and state != (0, 0, 0):
            got = bend(lit)
            if got is None:
                faults.append(f'{state}: not a 28 x 28 curve glyph')
            else:
                for name, value, want in (('shadows', got[0], state[0]), ('highlights', got[1], state[1])):
                    if (value > 1.5) - (value < -1.5) != want:
                        faults.append(f'{state}: {name} side of the glyph bends {value:+.1f}')
    if len(seen) == 27 and len(set(seen.values())) != 27:
        faults.append(f'{len(set(seen.values()))} different icons for 27 states')
    if len(seen) != 27:
        faults.append(f'only {len(seen)} states gave an icon')
    for fault in faults:
        print('FAILED', fault)
    if faults:
        sys.exit('tone icon regressions failed')
    print(f'tone icons passed: 27 states, 27 different icons, {len(states)} frames, bend matches Shadows / Highlights')


if __name__ == '__main__':
    main()
