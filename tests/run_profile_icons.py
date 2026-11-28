#!/usr/bin/env python3
"""Shooting-screen Picture Mode icon of edited Color and Monochrome Profiles (OM-Emu, E148 only).

    python tests/run_profile_icons.py --emu OM_EMU --build BUILD --out NEW_DIR

An unedited profile's shooting-screen icon is image 0x3d62..0x3d64 (Color 1-3) or 0x3d5a..0x3d5c (Monochrome
1-3). Once a profile is edited the firmware asks for 0x3d66..0x3d68 and 0x3d5e..0x3d60 instead (traced with
tools/dev/imgwatch.mjs, 16 November 2026); in stock E148 these are empty placeholders, so the icon vanished.
They are listed in the artwork sprites of firmware/om5ii/patch.json. For each of the six profiles the session
selects it in the Picture Mode carousel, edits one row, confirms and returns to the shooting screen. The icon
must not be blank and the six icons must differ. Emulator only.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_page_graphics import frame, px

ROOT = Path(__file__).resolve().parents[1]
X0, Y0, X1, Y1 = 660, 285, 720, 325     # the Picture Mode icon at the right edge of the shooting screen
LIT = 150
PROFILES = {'Color 1': 8, 'Color 2': 9, 'Color 3': 10, 'Monochrome 1': 11, 'Monochrome 2': 12, 'Monochrome 3': 13}


def icon(rows):
    return frozenset((x, y) for y in range(Y0, Y1) for x in range(X0, X1) if px(rows, x, y)[0] > LIT)


def run(a, name, rights):
    rows = 'down down down' if rights < 11 else 'down down'   # the tone row; Color Profiles have Split toning above it
    keys = 's1 ok ok ' + 'right ' * rights + rows + ' main+1 ok s1 wait:500'
    out = a.out / name.replace(' ', '-').lower()
    cmd = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()), str(a.build.resolve() / 'decoded/0100.bin'),
           str(a.build.resolve() / 'decoded/0101.bin'), str(out), keys, '--ready']
    env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tools/dev/mount.mjs'))
    return subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT), out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    sessions = {name: run(a, name, rights) for name, rights in PROFILES.items()}
    icons, faults = {}, []
    for name, (proc, out) in sessions.items():
        log, _ = proc.communicate(timeout=1800)
        (a.out / f'{out.name}.log').write_bytes(log)
        if proc.returncode:
            faults.append(f'{name}: session failed; see {a.out / (out.name + ".log")}')
            continue
        last = sorted(out.glob('[0-9][0-9]-*.png'))[-1]
        if b'ID_ST_CA_REQ_DISP' not in log.splitlines()[-1]:
            faults.append(f'{name}: did not return to the shooting screen')
        lit = icon(frame(last))
        if len(lit) < 40:
            faults.append(f'{name}: blank shooting-screen icon after an edit ({last.name})')
        else:
            icons[name] = lit
    if len(icons) == len(PROFILES) and len(set(icons.values())) != len(PROFILES):
        faults.append(f'{len(set(icons.values()))} different icons for {len(PROFILES)} profiles')
    for fault in faults:
        print('FAILED', fault)
    if faults:
        sys.exit('profile icon regressions failed')
    print(f'profile icons passed: {len(PROFILES)} edited profiles, {len(PROFILES)} different shooting-screen icons')


if __name__ == '__main__':
    main()
