#!/usr/bin/env python3
"""Arming in the background after start-up (boot.s): emulator regressions on a strict decoded E148 build.

OM-Emu does not run E148's FastEndCb, so tests/boot_pre.mjs starts boot.s's task as the hook does (bg_start), after the
section bits are published. Each case then idles or presses keys without a half-press first, and
tests/boot_arm_assert.mjs checks the state block P: armed, the start-up refresh pending until the first half-press,
LOOKS.BIN read in the background, and the look button working before any half-press. Cases with BG off are the
unchanged half-press path. Emulator only: start-up timing, the real FastEndCb and the card's speed are camera-only.

    python tests/run_boot_arm.py --emu OM_EMU_DIR --build generated/strict --out generated/boot-arm
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from card.mklooks import looks_bin

CP1 = 'ok ok ' + 'right ' * 8         # Picture Mode, Color Profile 1 highlighted (no half-press)
# (name, background task started, card mounted, keys, expectation)
CASES = [
    ('bg-arms', True, True, 'wait:4000', dict(armed=True, pend=1, films=1, count=4, slot0=None)),
    ('bg-look-without-halfpress', True, True, 'wait:4000 ' + CP1 + 'delete', dict(armed=True, pend=1, films=1, slot0=0)),
    ('bg-then-halfpress', True, True, 'wait:4000 s1', dict(armed=True, pend=0, films=1)),
    # No card: armed, LOOKS.BIN not tried (the task waits 10 s for a medium, then leaves it to the half-press)
    ('bg-no-card', True, False, 'wait:12000', dict(armed=True, pend=1, films=0)),
    ('bg-no-card-halfpress', True, False, 'wait:12000 s1', dict(armed=True, pend=0, films=0)),
    # The half-press path alone, as before boot.s (the task not started)
    ('halfpress-only', False, True, 's1', dict(armed=True, pend=0, films=1)),
    ('no-task-no-halfpress', False, True, 'wait:4000', dict(armed=False)),
]


def bg_start(build):
    nm = subprocess.run(['mn10300-elf-nm', str(build / 'assembly/hsl/patch.elf')], capture_output=True, text=True,
                        check=True).stdout
    return next(line.split()[0] for line in nm.splitlines() if line.endswith(' bg_start'))


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
    start = bg_start(a.build.resolve())
    results, failed = [], []
    for name, bg, mounted, keys, want in CASES:
        if a.case and name not in a.case:
            continue
        folder = a.out.resolve() / name
        env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tests/boot_pre.mjs'),
                   POST=str(ROOT / 'tests/boot_arm_assert.mjs'), OM5_BOOT_EXPECT=json.dumps(want),
                   OM5_UNMOUNTED='0' if mounted else '1')
        if bg:
            env['OM5_BG_START'] = start
        else:
            env.pop('OM5_BG_START', None)
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), keys, '--ready', '--card=' + str(card)]
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        log = run.stdout.decode('utf-8', errors='replace')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'session.log').write_text(log, encoding='utf-8')
        got = [line[len('BOOT ARM '):] for line in log.splitlines() if line.startswith('BOOT ARM ')]
        ok = run.returncode == 0 and 'ASSERTIONS passed' in log and bool(got)
        results.append(dict(case=name, passed=ok, expected=want, observed=json.loads(got[-1]) if got else None))
        print(f'{name}: {"passed" if ok else "FAILED"}' + ('' if ok else f' {got[-1] if got else ""} (see {folder}/session.log)'), flush=True)
        if not ok:
            failed.append(name)
    (a.out / 'results.json').write_text(json.dumps(dict(emulator_only=True, camera_tested=False, cases=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
