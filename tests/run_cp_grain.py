#!/usr/bin/env python3
"""Color Profile grain (v0.2.0) emulator regressions on a strict decoded E148 build.

Each case drives the Picture Mode screen with the firmware's own GUI, then tests/cp_grain_assert.mjs reads the grain
cells 907 / 911 / 915 and effective setting 998 through OM's getters. Emulator only: OM-Emu has no image pipeline,
so a pass does not show grain in a photo, and nothing here is a camera result.

    python tests/run_cp_grain.py --emu OM_EMU_DIR --build generated/strict --out generated/cp-grain
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CP1 = 's1 ok ok ' + 'right ' * 8              # shooting screen -> Picture Mode, highlight on Color Profile 1
GRAIN = 'down ' * 6                            # Picture Mode row -> Film Grain (the seventh row)
SET_CP1_LOW = CP1 + GRAIN + 'left ok wait:500'  # the carousel reads High Std Low Off; left from Off is Low
REOPEN = ' ok ok down '                        # reopens on the grain row (the last of 7); down wraps to the mode row
CASES = [
    ('cp1-low', SET_CP1_LOW, dict(cells=[1, 0, 0], effective=1), 1),
    ('cp2-high', CP1 + 'right ' + GRAIN + 'left left left ok wait:500', dict(cells=[0, 3, 0], effective=3), 3),
    ('to-cp2', SET_CP1_LOW + REOPEN + 'right ok wait:500', dict(cells=[1, 0, 0], effective=0), 0),
    ('to-stock-mode', SET_CP1_LOW + REOPEN + 'left ' * 6 + 'ok wait:500', dict(cells=[1, 0, 0], effective=0), 0),
    ('to-mono1', SET_CP1_LOW + REOPEN + 'right ' * 3 + 'ok wait:500', dict(cells=[1, 0, 0], effective=0), 0),
    ('back-to-cp1', SET_CP1_LOW + REOPEN + 'left ' * 6 + 'ok wait:500 ok ok ' + 'right ' * 6 + 'ok wait:500',
     dict(cells=[1, 0, 0], effective=1), 1),
    ('cp1-off', CP1 + 'ok wait:500', dict(cells=[0, 0, 0], effective=0), 0),
]


def probe_symbols(build):
    """cg_sel / cg_level addresses from the build's linked ELF, or None when the build has no colour grain probe."""
    elf = build.resolve() / 'assembly/hsl/patch.elf'
    nm = os.environ.get('NM', 'mn10300-elf-nm')
    try:
        out = subprocess.run([nm, str(elf)], stdout=subprocess.PIPE, check=True).stdout.decode()
    except (OSError, subprocess.CalledProcessError):
        return None
    syms = {f[2]: int(f[0], 16) for f in (line.split() for line in out.splitlines()) if len(f) == 3}
    if 'cg_sel' not in syms or 'cg_level' not in syms:
        return None
    return dict(sel=syms['cg_sel'], lvl=syms['cg_level'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--case', action='append', help='run only named cases')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    probe = probe_symbols(a.build)
    print('colour grain probe: ' + (f"cg_sel {probe['sel']:#x}, cg_level {probe['lvl']:#x}" if probe
                                    else 'not in this build (or no mn10300-elf-nm): request checks skipped'))
    results, failed = [], []
    for name, keys, want, level in CASES:
        if a.case and name not in a.case:
            continue
        folder = a.out.resolve() / name
        env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tools/dev/mount.mjs'),
                   POST=str(ROOT / 'tests/cg_probe_assert.mjs'), OM5_GRAIN_EXPECT=json.dumps(want),
                   OM5_CG=json.dumps(dict(probe, level=level) if probe else {}))
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), keys, '--ready']
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        log = run.stdout.decode('utf-8', errors='replace')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'session.log').write_text(log, encoding='utf-8')
        got = [line[len('CP GRAIN '):] for line in log.splitlines() if line.startswith('CP GRAIN ')]
        cg = [json.loads(line[3:]) for line in log.splitlines() if line.startswith('CG {')]
        ok = (run.returncode == 0 and 'ASSERTIONS passed' in log and bool(got)
              and (not probe or 'CG ASSERTIONS passed' in log))
        results.append(dict(case=name, passed=ok, expected=want, observed=json.loads(got[-1]) if got else None,
                            probe_level=level if probe else None, probe=cg))
        print(f'{name}: {"passed" if ok else "FAILED"}' + ('' if ok else f' (see {folder / "session.log"})'))
        if not ok:
            failed.append(name)
    (a.out / 'results.json').write_text(json.dumps(dict(emulator_only=True, camera_tested=False, cases=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
