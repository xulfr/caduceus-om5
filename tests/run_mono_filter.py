#!/usr/bin/env python3
"""Monochrome Profile colour filter controls (OM-Emu, E148 only).

    python tests/run_mono_filter.py --emu OM_EMU --build BUILD --out NEW_DIR

The filter page (Monochrome Profile p, second sidebar row) steps setting 1007+p with the sub dial in the
OM-3's order (None, Yellow, Orange, Red, Magenta, Blue, Cyan, Green, Yellow-Green; list 0x6050cb23) and the
main dial steps the level shown as "+n". Check the native header and setting stores (0x602d19b6),
the selected swatch and centre, persistence on re-entry, and that Monochrome Profile 2 is unchanged.
Frames are Y/Cb/Cr in the PNG's R/G/B.
Emulator only.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_page_graphics import COLOURS, GREY, WHITE, frame, px

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card_block import card_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MONO = 's1 ok ok ' + 'right ' * 11          # Monochrome Profile 1, Picture Mode row
FX, FY, R, D = 556, 236, 80, 57
SLOT_XY = [(0, -R), (D, -D), (R, 0), (D, D), (0, R), (-D, D), (-R, 0), (-D, -D)]
SLOT_COLOUR = [COLOURS[i] for i in (0, 1, 3, 4, 7, 8, 10, 11)]   # Y, O, R, M, B, C, G, YG
SLOT_OF = {0: None, 1: 0, 2: 1, 3: 2, 6: 3, 7: 4, 8: 5, 4: 6, 5: 7}
DIAL = [1, 2, 3, 6, 7, 8, 4, 5, 0, 1, 2, 3]  # 1007 after each sub-1 from None (wraps once)
HEADER, LEVEL_VALUE = (470, 72, 650, 108), (567, 362, 602, 392)


def run(a, name, keys):
    out = a.out / name
    cmd = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()), str(a.build.resolve() / 'decoded/0100.bin'),
           str(a.build.resolve() / 'decoded/0101.bin'), str(out), keys, '--ready',
           '--card=' + str(card_for(a.build, a.out))]   # the filter ring is in the card block
    env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tests/store_log.mjs'))
    return subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT), out


def region(rows, box, level=150):
    x0, y0, x1, y1 = box
    return frozenset((x, y) for y in range(y0, y1) for x in range(x0, x1) if px(rows, x, y)[0] > level)


def ring(rows, value):
    """Faults of the filter graphic for a stored value."""
    bad, sel = [], SLOT_OF[value]
    for s, (dx, dy) in enumerate(SLOT_XY):
        x, y = FX + dx, FY + dy
        if not all(px(rows, x + u, y + v) == SLOT_COLOUR[s] for u in (-10, 0, 10) for v in (-10, 0, 10)):
            bad.append(f'slot {s}: swatch {px(rows, x, y)}')
        edge = all(px(rows, x + u, y + v) == WHITE for u, v in ((-15, 0), (15, 0), (0, -15), (0, 15)))
        if edge != (s == sel):
            bad.append(f'slot {s}: white edge {edge}')
    want = GREY if sel is None else SLOT_COLOUR[sel]
    if not all(px(rows, FX + u, FY + v) == want for u in (-20, 0, 20) for v in (-20, 0, 20)):
        bad.append(f'centre {px(rows, FX, FY)}, expected {want}')
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    other = 'up right down'                    # Monochrome Profile 2's filter page
    steps = ['down'] + ['sub-1'] * len(DIAL) + ['main+1', 's1', 'ok', 'ok'] + other.split()
    sessions = {'base': run(a, 'base', MONO + 'down ' + other), 'filter': run(a, 'filter', MONO + ' '.join(steps))}
    logs, frames, faults = {}, {}, []
    for name, (proc, out) in sessions.items():
        log, _ = proc.communicate(timeout=1800)
        logs[name] = log.decode('utf-8', errors='replace')
        (a.out / f'{name}.log').write_text(logs[name], encoding='utf-8')
        if proc.returncode:
            sys.exit(f'{name}: session failed; see {a.out / (name + ".log")}')
        frames[name] = {int(p.name[:2]): p for p in out.glob('[0-9][0-9]-*.png')}
    n0 = len(MONO.split())                      # frame index of the first key after MONO is n0 + 1
    f = lambda k: frame(frames['filter'][n0 + 1 + k])
    # stores per key: the log prints STORE lines before each step line
    per_key, cur = [], []
    for line in logs['filter'].splitlines():
        m = re.match(r'STORE (\d+) (-?\d+)', line)
        if m:
            cur.append((int(m[1]), int(m[2])))
        elif re.match(r'^[a-z0-9+-]+: 0x', line):
            per_key.append(cur)
            cur = []
    per_key = per_key[n0 + 1:]                  # drop 'start' and the keys of MONO
    header0 = region(f(0), HEADER)
    faults += [f'entry: {b}' for b in ring(f(0), 0)]
    headers = [header0]
    for k, value in enumerate(DIAL, 1):
        rows = f(k)
        faults += [f'step {k}: {b}' for b in ring(rows, value)]
        stores = [v for i, v in per_key[k] if i in (1007, 1008, 1009)] if k < len(per_key) else []
        ids = {i for i, _ in per_key[k] if i in (1007, 1008, 1009)} if k < len(per_key) else set()
        if stores[-1:] != [value] or ids - {1007}:
            faults.append(f'step {k}: stores {per_key[k] if k < len(per_key) else None}, expected 1007 = {value}')
        headers.append(region(rows, HEADER))
    if not all(headers[:9]) or len(set(headers[:9])) != 9:
        faults.append(f'header: {len(set(headers[:9]))} different labels for 9 filters')
    if headers[9] != header0:
        faults.append('header: None after the wrap differs from None on entry')
    k = len(DIAL) + 1                           # main+1: level
    faults += [f'level change: {b}' for b in ring(f(k), DIAL[-1])]
    if region(f(k), LEVEL_VALUE) == region(f(k - 1), LEVEL_VALUE):
        faults.append('level: "+n" did not change on main+1')
    if not any(i in (1011, 1012) for i, _ in per_key[k]):
        faults.append(f'level: no store to 1011 / 1012 on main+1 ({per_key[k]})')
    back = len(DIAL) + 4                        # s1 ok ok: the screen again, on the filter row
    faults += [f're-entry: {b}' for b in ring(f(back), DIAL[-1])]
    if region(f(back), HEADER) != headers[len(DIAL)]:
        faults.append('re-entry: header differs from before leaving')
    if region(f(back), LEVEL_VALUE) != region(f(k), LEVEL_VALUE):
        faults.append('re-entry: level differs from before leaving')
    mp2 = frame(frames['base'][max(frames['base'])])
    mp2_after = f(len(steps) - 1)
    faults += [f'Profile 2: {b}' for b in ring(mp2_after, 0)]
    if region(mp2, (380, 40, 720, 400)) != region(mp2_after, (380, 40, 720, 400)):
        faults.append('Monochrome Profile 2: filter page differs after editing Profile 1')
    for fault in faults:
        print('FAILED', fault)
    if faults:
        sys.exit('mono filter regressions failed')
    print(f'mono filter passed: {len(DIAL)} dial steps (all 9 filters and the wrap) stored to 1007; '
          'header and ring follow; +n changes; values kept after leaving the screen; Profile 2 unchanged')


if __name__ == '__main__':
    main()
