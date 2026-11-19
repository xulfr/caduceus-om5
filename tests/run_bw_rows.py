#!/usr/bin/env python3
"""Blacks / Whites / Split tone rows (v0.2.0-dev) emulator regressions on a strict decoded E148 build.

Each case drives the Picture Mode screen with the firmware's own GUI. tests/bw_rows_assert.mjs then reads the six
settings and the curve values the refresh wrote into P. Emulator only: OM-Emu develops no photos, so a pass says
nothing about pictures and is not a camera result.

    python tests/run_bw_rows.py --emu OM_EMU_DIR --build generated/strict --out generated/bw-rows
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CP1 = 's1 ok ok ' + 'right ' * 8          # Picture Mode, Color Profile 1 highlighted
BLACK, WHITE, SPLIT = 'down ' * 7, 'down ' * 8, 'down ' * 9   # rows 8, 9, 10 of the Color Profile list
DONE = 'ok wait:500'
TO_STRIP_FROM_BLACK = ' ok ok down down down '  # reopens on Black; down 3 times wraps to the mode strip
CASES = [
    ('cp1-black+2', CP1 + BLACK + 'right right ' + DONE, dict(pm=54, set=[2, 0, 0, 0, 0, 0], p=[40, 0])),
    ('cp1-white-3', CP1 + WHITE + 'left left left ' + DONE, dict(pm=54, set=[0, 0, 0, -3, 0, 0], p=[0, 60])),
    ('cp2-black-5', CP1 + 'right ' + BLACK + 'left ' * 6 + DONE, dict(pm=55, set=[0, -5, 0, 0, 0, 0], p=[-100, 0])),
    ('cp2-after-cp1', CP1 + BLACK + 'right right ' + DONE + TO_STRIP_FROM_BLACK + 'right ' + DONE,
     dict(pm=55, set=[2, 0, 0, 0, 0, 0], p=[0, 0])),
    ('stock-after-cp1', CP1 + BLACK + 'right right ' + DONE + TO_STRIP_FROM_BLACK + 'left ' * 6 + DONE,
     dict(pm=5, set=[2, 0, 0, 0, 0, 0], p=[0, 0])),
    ('back-to-cp1', CP1 + BLACK + 'right right ' + DONE + TO_STRIP_FROM_BLACK + 'left ' * 6 + DONE + ' ok ok ' +
     'right ' * 6 + DONE, dict(pm=54, set=[2, 0, 0, 0, 0, 0], p=[40, 0])),
    ('cp1-split+3', CP1 + SPLIT + 'right right right ' + DONE, dict(pm=54, split=180, splitIds=[3, 0, 0], buf=True)),
    ('cp3-split-2', CP1 + 'right right ' + SPLIT + 'left left ' + DONE, dict(pm=56, split=-120, splitIds=[0, 0, -2], buf=True)),
    ('split-after-cp1', CP1 + SPLIT + 'right right right ' + DONE + ' ok ok down ' + 'left ' * 6 + DONE,
     dict(pm=5, split=0, splitIds=[3, 0, 0])),
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
                   POST=str(ROOT / 'tests/bw_rows_assert.mjs'), OM5_BW_EXPECT=json.dumps(want))
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), keys, '--ready']
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=400)
        log = run.stdout.decode('utf-8', errors='replace')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'session.log').write_text(log, encoding='utf-8')
        got = [line[len('BW ROWS '):] for line in log.splitlines() if line.startswith('BW ROWS ')]
        ok = run.returncode == 0 and 'ASSERTIONS passed' in log and bool(got)
        results.append(dict(case=name, passed=ok, expected=want, observed=json.loads(got[-1]) if got else None))
        print(f'{name}: {"passed" if ok else "FAILED"}' + ('' if ok else f' {got[-1] if got else ""} (see {folder}/session.log)'), flush=True)
        if not ok:
            failed.append(name)
    (a.out / 'results.json').write_text(json.dumps(dict(emulator_only=True, camera_tested=False, cases=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
