#!/usr/bin/env python3
"""Inactivity timeout and HSL axis repaint regressions for the custom Color Profile pages (OM-Emu, E148 only).

    python tests/run_ui_activity.py --emu OM_EMU --build BUILD --out NEW_DIR [--case NAME]

Each case opens the Picture Mode direct screen on Color Profile 1 with a mounted LOOKS.BIN, moves to a row and
repeats one control seven times, 2.5 s apart (well past the screen's 8000 ms timer 500). Every custom control
must keep the screen open (state 0x0418); with no input the screen must still close (0x0108). The axis cases
press Delete on the colour wheel and require one timer restart and one colour-page invalidation per press, and
the axis to cycle Hue, Lightness, Saturation. Emulator only: OM-Emu repaints the whole plane, so the frames
cannot show the camera's missing repaint; the invalidation count is the check.
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

OPEN = 's1 ok ok ' + 'right ' * 8
STAY, CLOSED = '0x418', '0x108'
CASES = {
    # name: (row keys, action, expected state after each repetition)
    'wheel-delete': ('down', 'delete', STAY),
    'wheel-info': ('down', 'info', STAY),
    'wheel-dial': ('down', 'main+1', STAY),
    'tone-info': ('down down', 'info', STAY),
    'tone-main-dial': ('down down', 'main+1', STAY),
    'tone-sub-dial': ('down down', 'sub+1', STAY),
    'strip-film-step': ('', 'delete', STAY),
    'strip-dial': ('', 'main+1', STAY),
    'idle': ('down', 'wait:1', None),
}


def session(a, card, name, keys, env=None):
    out = a.out / name
    cmd = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()), str(a.build.resolve() / 'decoded/0100.bin'),
           str(a.build.resolve() / 'decoded/0101.bin'), str(out), keys, '--ready', '--peekP', '--card=' + str(card)]
    e = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tests/ui_activity.mjs'), POST=str(ROOT / 'tests/ui_activity.mjs'), **(env or {}))
    run = subprocess.run(cmd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    log = run.stdout.decode('utf-8', errors='replace')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'session.log').write_text(log, encoding='utf-8')
    if run.returncode or 'ASSERTIONS passed' not in log:
        raise AssertionError(f'{name}: session failed; see {out / "session.log"}')
    return log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--case', action='append')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    card = a.out / 'card'
    (card / 'OM5MOD').mkdir(parents=True)
    (card / 'OM5MOD/LOOKS.BIN').write_bytes(looks_bin(json.loads((ROOT / 'tools/dev/films-test.json').read_text())))
    results = {}
    for name, (row, action, want) in CASES.items():
        if a.case and name not in a.case:
            continue
        keys = f'{OPEN}{row} T+ ' + ' '.join(f'{action} wait:2500' for _ in range(7)) + ' T-'
        log = session(a, card, name, keys)
        states = [line.split()[1] for line in log.splitlines() if line.startswith('wait:2500:')]
        if want is None:
            ok = states[0] == STAY and states[-1] == CLOSED
        else:
            ok = len(states) == 7 and all(s == want for s in states)
        results[name] = dict(states=states, ok=ok)
        print(name, 'ok' if ok else 'FAILED', ' '.join(states), flush=True)
    if not a.case or 'axis' in a.case:
        log = session(a, card, 'axis', OPEN + 'down T+ delete delete delete T-', dict(UI_TIMER='3', UI_PAGE_INVALIDATE='3'))
        axes = [int(line.split('axis=')[1].split()[0]) for line in log.splitlines() if line.startswith('delete:')]
        ok = axes == [1, 2, 0]
        results['axis'] = dict(axes=axes, ok=ok)
        print('axis', 'ok' if ok else 'FAILED', axes, flush=True)
    (a.out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    if not all(r['ok'] for r in results.values()):
        sys.exit('ui activity regressions failed')
    print('all', len(results), 'ui activity cases passed')


if __name__ == '__main__':
    main()
