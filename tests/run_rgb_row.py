#!/usr/bin/env python3
"""The RGB curves row (roadmap phase 4, 2026-11-28): OM's tone editor a second time under the tone row, as the OM-3
v0.41's RGB row. Its three INFO pages edit one channel's five points (Hi/Sh: 3 / 1, Mid: 2, Bl/Wh: 4 / 0); INFO from
Bl/Wh steps the channel R -> G -> B -> R. The points are the curve cells (985-987, 1030-1032, 1002 / 1006 / 1010) and
the refresh adds the curves to the split-tone tables (tests/st_assert.mjs). The tone row keeps OM's own values.
The row's logic is in the card block, so every session has it. Emulator only: not a camera result.

    python tests/run_rgb_row.py --emu OM_EMU_DIR --build generated/strict --out generated/rgb-row
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from card_block import card_for  # noqa: E402

CP = 's1 ok ok ' + 'right ' * 8
RGB = CP + 'down down down down '        # rows: wheel, Split toning, tone, RGB
Z = [0, 0, 0, 0, 0]
CASES = [
    # Hi/Sh: as on the tone row, OM-Emu's main dial moves Sh (point 1) and the sub dial Hi (point 3, OM's direction)
    ('rgb-hi-sh', RGB + 'main+1 sub+1', dict(row=4, ch=0, cells={985: [0, 1, 0, -1, 0], 986: None}, tone={976: 0, 978: 0}, st=True)),
    ('rgb-mid', RGB + 'info main+2', dict(row=4, ch=0, cells={985: [0, 0, 2, 0, 0]}, tone={977: 0}, st=True)),
    # Bl/Wh: main Black (point 0), sub White (point 4)
    ('rgb-bl-wh', RGB + 'info info main+1 sub-1', dict(row=4, ch=0, cells={985: [1, 0, 0, 0, 1]}, st=True)),
    # INFO from Bl/Wh: the next channel, back on Hi/Sh
    ('rgb-green', RGB + 'info info info main+1', dict(row=4, ch=1, cells={985: None, 986: [0, 1, 0, 0, 0]}, st=True)),
    ('rgb-blue-and-wrap', RGB + 'info ' * 6 + 'main+1 ' + 'info ' * 3, dict(row=4, ch=0, cells={987: [0, 1, 0, 0, 0]})),
    # Profile 2's cells
    ('rgb-profile-2', CP + 'right down down down down main+1', dict(row=4, cells={1030: [0, 1, 0, 0, 0], 985: None}, st=True)),
    # the tone row is OM's: its edits stay in 976..978, the curves untouched; the RGB row reads its own after it
    ('tone-row-own', RGB + 'main+1 up main+2', dict(row=3, cells={985: [0, 1, 0, 0, 0]}, tone={978: 2, 976: 0})),
    ('tone-then-rgb', CP + 'down down down main+2 down main-1', dict(row=4, ch=0, cells={985: [0, -1, 0, 0, 0]}, tone={978: 2})),
    # OM reopens Picture Mode on the remembered item's row: the tone row, not the RGB row
    ('reopen-on-tone-row', RGB + 'main+1 ok wait:500 ok ok', dict(row=3, cells={985: [0, 1, 0, 0, 0]})),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--case', action='append')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    card = card_for(a.build, a.out)
    results, failed = [], []
    for name, keys, want in CASES:
        if a.case and name not in a.case:
            continue
        folder = a.out.resolve() / name
        env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tools/dev/mount.mjs'),
                   POST=str(ROOT / 'tests/rgb_row_assert.mjs'), OM5_RGB_EXPECT=json.dumps(want))
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), keys, '--ready', '--card=' + str(card)]
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        log = run.stdout.decode('utf-8', errors='replace')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'session.log').write_text(log, encoding='utf-8')
        got = [line[len('RGB ROW '):] for line in log.splitlines() if line.startswith('RGB ROW ')]
        ok = run.returncode == 0 and 'ASSERTIONS passed' in log and bool(got)
        results.append(dict(case=name, passed=ok, expected=want, observed=json.loads(got[-1]) if got else None))
        print(f'{name}: {"passed" if ok else "FAILED"}' + ('' if ok else f' {got[-1] if got else ""} (see {folder}/session.log)'), flush=True)
        if not ok:
            failed.append(name)
    (a.out / 'results.json').write_text(json.dumps(dict(emulator_only=True, camera_tested=False, cases=results), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
