#!/usr/bin/env python3
"""Color Profile Shading, Monochrome Film Grain and Color Filter rows (OM-Emu, E148 only).

    python tests/run_profile_rows.py --emu OM_EMU --build BUILD --out NEW_DIR

Alpha9 camera report (research/OM5II-ALPHA9-CAMERA-2026-11-16.md):
- Color Profile Shading (912..914) had no setting descriptor, so the slider knob was grey and dial turns were
  dropped. cp_nd.py adds descriptors; here the knob must be lime (enabled) and move right on main+1.
- Monochrome Film Grain images 0x38e7..0x38ee and the Color Filter row image 0x38cb were empty placeholders.
  The four strip states (Off, Low, Medium, High) must each show four non-blank, different items, and the
  Filter row must not be blank.
Frames are Y/Cb/Cr in the PNG's R/G/B. Emulator only.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_page_graphics import frame, px

ROOT = Path(__file__).resolve().parents[1]
OPEN = 's1 ok ok ' + 'right ' * 8
MONO = OPEN + 'right ' * 3


def run(a, name, keys):
    out = a.out / name
    cmd = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()), str(a.build.resolve() / 'decoded/0100.bin'),
           str(a.build.resolve() / 'decoded/0101.bin'), str(out), keys, '--ready']
    env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tools/dev/mount.mjs'))
    return subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT), out


def knob(rows):
    """(x centre, lime?) of the slider knob in the bar under the title, or None."""
    lime = [x for y in range(425, 462) for x in range(90, 640) if px(rows, x, y)[0] > 150 and px(rows, x, y)[1] < 90]
    grey = [x for y in range(425, 462) for x in range(90, 640)
            if 60 < px(rows, x, y)[0] < 140 and abs(px(rows, x, y)[1] - 128) < 12 and abs(px(rows, x, y)[2] - 128) < 12]
    if len(lime) > 60:
        return sum(lime) / len(lime), True
    if len(grey) > 60:
        return sum(grey) / len(grey), False
    return None


def lit(rows, x0, y0, x1, y1, level=150):
    return frozenset((x, y) for y in range(y0, y1) for x in range(x0, x1) if px(rows, x, y)[0] > level)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    sessions = {
        'shading': run(a, 'shading', OPEN + 'down down down down main+1 main+1'),
        'grain': run(a, 'grain', MONO + 'down down down down down down main+1 main+1 main+1'),
    }
    frames, faults = {}, []
    for name, (proc, out) in sessions.items():
        log, _ = proc.communicate(timeout=1800)
        (a.out / f'{name}.log').write_bytes(log)
        if proc.returncode:
            faults.append(f'{name}: session failed; see {a.out / (name + ".log")}')
            continue
        frames[name] = sorted(out.glob('[0-9][0-9]-*.png'))
    if 'shading' in frames:
        k = [knob(frame(f)) for f in frames['shading'][-3:]]
        if None in k:
            faults.append(f'shading: no slider knob found {k}')
        else:
            if not all(on for _, on in k):
                faults.append(f'shading: knob is grey (disabled) {k}')
            if not k[0][0] + 20 < k[1][0] < k[2][0] - 20:
                faults.append(f'shading: knob does not move right with main+1 {k}')
    if 'grain' in frames:
        f = frames['grain']
        mono_row = frame(f[len(MONO.split())])               # Monochrome Profile 1, Picture Mode row selected
        if len(lit(mono_row, 0, 135, 80, 165)) < 40:
            faults.append('filter: Color Filter row icon is blank')
        strips = [lit(frame(p), 180, 425, 540, 475, 100) for p in f[-4:]]
        if any(len(s) < 150 for s in strips):
            faults.append(f'grain: blank strip {[len(s) for s in strips]}')
        if len(set(strips)) != 4:
            faults.append(f'grain: {len(set(strips))} different strips for 4 values')
        for n, p in enumerate(f[-4:]):
            for item in range(4):
                if len(lit(frame(p), 188 + 88 * item, 425, 268 + 88 * item, 475, 100)) < 20:
                    faults.append(f'grain value {n}: strip item {item} blank')
    for fault in faults:
        print('FAILED', fault)
    if faults:
        sys.exit('profile row regressions failed')
    print('profile rows passed: Color Profile Shading enabled and moves; Film Grain strip 4 items x 4 states; '
          'Color Filter row icon drawn')


if __name__ == '__main__':
    main()
