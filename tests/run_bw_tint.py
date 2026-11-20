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
    # Camera report 2026-11-19: "all" on a tint axis wrote every colour in turn (the last, Yellow-green 0x3b, wins).
    # "all" (INFO) on Saturation, then trash to Shadow Tint: the axis is back on one colour (Yellow, 0x30).
    ('cp1-all-to-tint', CP1 + WHEEL + 'info ' + TINT + 'main+3 ' + DONE, dict(pm=54, tint={968: 0x30}, stFlag=1, st=True)),
    # INFO on a tint axis does not select "all".
    ('cp1-tint-info', CP1 + WHEEL + TINT + 'info main+3 ' + DONE, dict(pm=54, tint={968: 0x30}, stFlag=1, st=True)),
    # Live view (owner 2026-11-20): Black / White changes must reach live view; gs_hook makes each gamma cache miss
    # once after a table rebuild. tests/gs_assert.mjs runs the hook's code from gs_entry (see there).
    # Same keys without the value changes: GS_GEN from refreshes alone (arming, mode changes), the baseline.
    ('cp1-gs-baseline', CP1 + TONE + 'info ' + DONE, dict(pm=54, gs=True)),
    ('cp1-bw-gamma-cache', BW + DONE, dict(pm=54, bw=[-1, 0, 0, -2, 0, 0], gs=True, gs_above='cp1-gs-baseline')),
    # Tints too (owner 2026-11-20: tints also changed live view only after a half-press).
    ('cp1-wheel-gs-baseline', CP1 + WHEEL + TINT + DONE, dict(pm=54, gs=True)),
    ('cp1-tint-gamma-cache', CP1 + WHEEL + TINT + 'main+3 ' + DONE,
     dict(pm=54, tint={968: 0x30}, gs=True, gs_above='cp1-wheel-gs-baseline')),
    ('stock-after-tint', CP1 + WHEEL + TINT + 'main+3 ' + DONE + ' ok ok up ' + 'left ' * 6 + DONE,
     dict(pm=5, tint={968: 0x30}, stFlag=0)),
]



def gs_entry(build):
    """gs_entry's address: the target of the jmp gs_hook put at 0x603e6a3b, read from the decoded build."""
    main = (build / 'decoded' / '0100.bin').read_bytes()
    at = 0x603e6a3b - 0x60021020
    if main[at] != 0xdc:
        raise SystemExit('no jmp at the gamma cache test 0x603e6a3b (gs_hook)')
    return hex((0x603e6a3b + int.from_bytes(main[at + 1:at + 5], 'little', signed=True)) & 0xffffffff)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--case', action='append')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    results, failed, gs_seen = [], [], {}
    for name, keys, want in CASES:
        if a.case and name not in a.case:
            continue
        folder = a.out.resolve() / name
        env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tools/dev/mount.mjs'),
                   POST=str(ROOT / 'tests/bw_tint_assert.mjs'), OM5_BW_EXPECT=json.dumps(want))
        if want.get('gs'):
            above = gs_seen.get(want.get('gs_above'))
            if want.get('gs_above') and above is None:
                raise SystemExit(f'{name}: run {want["gs_above"]} first')
            env.update(OM5_GS_ENTRY=gs_entry(a.build), OM5_GS_MIN=str(above + 1 if above is not None else 1))
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), keys, '--ready']
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=400)
        log = run.stdout.decode('utf-8', errors='replace')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'session.log').write_text(log, encoding='utf-8')
        got = [line[len('BW TINT '):] for line in log.splitlines() if line.startswith('BW TINT ')]
        gen = [int(line.split()[-1]) for line in log.splitlines() if line.startswith('GS_GEN after the session ')]
        if gen:
            gs_seen[name] = gen[-1]
        ok = run.returncode == 0 and 'ASSERTIONS passed' in log and bool(got)
        results.append(dict(case=name, passed=ok, expected=want, observed=json.loads(got[-1]) if got else None))
        print(f'{name}: {"passed" if ok else "FAILED"}' + ('' if ok else f' {got[-1] if got else ""} (see {folder}/session.log)'), flush=True)
        if not ok:
            failed.append(name)
    (a.out / 'results.json').write_text(json.dumps(dict(emulator_only=True, camera_tested=False, cases=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
