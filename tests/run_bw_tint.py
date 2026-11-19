#!/usr/bin/env python3
"""Black / White on the tone page and split tone on the colour wheel (v0.2.0-dev): emulator regressions on a strict
decoded E148 build.

Each case drives the Picture Mode screen with the firmware's own GUI. tests/bw_tint_assert.mjs then reads the
settings, the values the refresh wrote into P and, for split-tone cases, runs tests/st_assert.mjs (delta tables and the
camera's R/G/B curve setter). Emulator only: OM-Emu develops no photos, so a pass says nothing about pictures and is
not a camera result.

    python tests/run_bw_tint.py --emu OM_EMU_DIR --build generated/strict --out generated/bw-tint
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CP1 = 's1 ok ok ' + 'right ' * 8          # Picture Mode, Color Profile 1 highlighted
TONE, WHEEL = 'down down ', 'down '           # rows 3 (tone curve) and 2 (colour wheel)
TINT = 'delete delete delete '                # colour wheel axis: Saturation -> Hue -> Lightness -> Shadow Tint
DONE = 'ok wait:500'
# OM-Emu's dials: in the Black/White state sub+2 sets Black -1 and main-3 White -2 (the stock Sh / Hi steps).
BW = CP1 + TONE + 'info sub+2 main-3 '
CASES = [
    ('cp1-black-white', BW + DONE, dict(pm=54, bw=[-1, 0, 0, -2, 0, 0], p=[-20, 40], tm=1, tone3=[0, 0, 0], stFlag=1, st=True)),
    ('cp1-info-cycle', BW + 'info info sub+1 ' + DONE,
     dict(pm=54, bw=[-1, 0, 0, -2, 0, 0], p=[-20, 40], tm=0, tone3=[-1, 0, 0])),
    # a lone main-3 moves OM's Sh by -3 (checked on stock Hi/Sh), so here Black of Color Profile 2
    ('cp2-black', CP1 + 'right ' + TONE + 'info main-3 ' + DONE, dict(pm=55, bw=[0, -3, 0, 0, 0, 0], p=[-60, 0], tm=1,
                                                                   stFlag=1, st=True)),
    ('stock-after-bw', BW + DONE + ' ok ok up up ' + 'left ' * 6 + DONE, dict(pm=5, bw=[-1, 0, 0, -2, 0, 0], p=[0, 0], stFlag=0)),
    ('cp1-tints', CP1 + WHEEL + TINT + 'main+3 delete delete sub+2 sub+2 main+2 ' + DONE,
     dict(pm=54, tint={968: 0x30, 974: 0x19}, stFlag=1, st=True)),
    ('cp3-midtone', CP1 + 'right right ' + WHEEL + TINT + 'delete main+3 ' + DONE,
     dict(pm=56, tint={973: 0x30}, stFlag=1, st=True)),
    ('stock-after-tint', CP1 + WHEEL + TINT + 'main+3 ' + DONE + ' ok ok up ' + 'left ' * 6 + DONE,
     dict(pm=5, tint={968: 0x30}, stFlag=0)),
]



def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--case', action='append')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    results, failed = [], []
    for name, keys, want in CASES:
        if a.case and name not in a.case:
            continue
        folder = a.out.resolve() / name
        env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tools/dev/mount.mjs'),
                   POST=str(ROOT / 'tests/bw_tint_assert.mjs'), OM5_BW_EXPECT=json.dumps(want))
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), keys, '--ready']
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=400)
        log = run.stdout.decode('utf-8', errors='replace')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'session.log').write_text(log, encoding='utf-8')
        got = [line[len('BW TINT '):] for line in log.splitlines() if line.startswith('BW TINT ')]
        ok = run.returncode == 0 and 'ASSERTIONS passed' in log and bool(got)
        results.append(dict(case=name, passed=ok, expected=want, observed=json.loads(got[-1]) if got else None))
        print(f'{name}: {"passed" if ok else "FAILED"}' + ('' if ok else f' {got[-1] if got else ""} (see {folder}/session.log)'), flush=True)
        if not ok:
            failed.append(name)
    (a.out / 'results.json').write_text(json.dumps(dict(emulator_only=True, camera_tested=False, cases=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
