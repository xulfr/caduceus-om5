#!/usr/bin/env python3
"""Run bounded E148 firmware regressions; requires an OM-Emu checkout and strict decoded build."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from card.mklooks import looks_bin
import patch


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--stock', type=Path, required=True, help='hash-pinned E148 stock for image-store baseline')
    ap.add_argument('--case', action='append', help='run only named cases')
    a = ap.parse_args()
    films = json.loads((ROOT / 'tools/dev/films-test.json').read_text())
    good = looks_bin(films)
    crc_bad = bytearray(good); crc_bad[-1] ^= 1
    range_bad = bytearray(good); range_bad[32] = 8
    struct.pack_into('<I', range_bad, 8, zlib.crc32(range_bad[12:]))
    selected = lambda i: dict(films[i], index=i)
    to_slot = 's1 ok ok ' + 'right ' * 8
    a.out.mkdir(parents=True, exist_ok=True)
    baseline = a.out.resolve() / 'stock-baseline'
    baseline.mkdir(exist_ok=False)
    stock = a.stock.read_bytes()
    spec = json.loads((ROOT / 'firmware/om5ii/patch.json').read_text())
    assert patch.sha256(stock) == spec['stock']['sha256']
    blocks = {b.kind: b for b in patch.parse(stock)}
    for kind in (0x100, 0x101):
        data = patch.expand_image(blocks[kind].payload) if kind == 0x100 else blocks[kind].payload
        (baseline / f'{kind:04x}.bin').write_bytes(data)
    twins = looks_bin([dict(films[1], name='Twin One'), dict(films[1], name='Twin Two')])
    twin = lambda i: dict(films[1], name=('Twin One', 'Twin Two')[i], index=i)
    cases = [
        ('four-films', good, True, 'delete', 1, 4, [selected(0), None, None]),
        ('next-film', good, True, 'delete delete', 1, 4, [selected(1), None, None]),
        ('slot-two', good, True, 'delete right delete', 1, 4, [selected(0), selected(1), None]),
        ('wrap', good, True, 'delete ' * 5, 1, 4, [selected(0), None, None]),
        ('ten-films', looks_bin((films * 3)[:10]), True, 'delete', 1, 10, [selected(0), None, None]),
        ('bad-crc', crc_bad, True, 'delete', 2, 0, [None] * 3),
        ('bad-range', range_bad, True, 'delete', 2, 0, [None] * 3),
        # Delete below the Picture Mode row: the colour wheel takes it (axis), the other rows ignore it.
        ('other-rows', good, True, 'down delete down delete down delete down delete down delete', 1, 4, [None] * 3),
        ('row-return', good, True, 'down down down down down down delete', 1, 4, [selected(0), None, None]),
        # Two films that differ only in name: the frame must change on each step (title repaint).
        ('title-redraw', twins, True, 'delete delete', 1, 2, [twin(1), None, None]),
        ('scp-name', good, True, 'delete ok wait:500 ok wait:500', 1, 4, [selected(0), None, None]),
        ('empty-card', None, True, 'delete', 2, 0, [None] * 3),
        ('no-card', None, False, 'delete', 0, 0, [None] * 3),
    ]
    results = []
    for name, data, mounted, keys, state, count, slots in cases:
        if a.case and name not in a.case:
            continue
        folder = a.out.resolve() / name
        folder.mkdir(parents=True, exist_ok=False)
        card = folder / 'card' / 'OM5MOD'; card.mkdir(parents=True)
        if data is not None:
            (card / 'LOOKS.BIN').write_bytes(data)
        expected = folder / 'expect.json'
        expected.write_text(json.dumps(dict(state=state, count=count, slots=slots)))
        pre = ROOT / 'tools/dev/mount.mjs' if mounted else ROOT / 'tests/unmounted.mjs'
        env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(pre), POST=str(ROOT / 'tests/emulator_assert.mjs'), OM5_EXPECT=str(expected))
        command = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()),
                   str(a.build.resolve() / 'decoded/0100.bin'), str(a.build.resolve() / 'decoded/0101.bin'),
                   str(folder / 'screens'), to_slot + keys, '--ready', '--watch', '--json', '--card=' + str(card.parent)]
        base_env = dict(env)
        base_env.pop('POST')
        base_command = command.copy()
        base_command[3:6] = [str(baseline / '0100.bin'), str(baseline / '0101.bin'), str(folder / 'stock-screens')]
        stock_run = subprocess.run(base_command, env=base_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300, check=True)
        stock_log = stock_run.stdout.decode('utf-8', errors='replace')
        (folder / 'stock-session.log').write_text(stock_log, encoding='utf-8')
        stock_summary = [json.loads(line[5:]) for line in stock_log.splitlines() if line.startswith('JSON ')][-1]
        stock_stores = dict(stock_summary['image_stores'])
        run = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        log = run.stdout.decode('utf-8', errors='replace')
        (folder / 'session.log').write_text(log, encoding='utf-8')
        summaries = [json.loads(line[5:]) for line in log.splitlines() if line.startswith('JSON ')]
        if run.returncode or 'ASSERTIONS passed' not in log or not summaries:
            raise RuntimeError(f'{name} failed; see {folder / "session.log"}')
        # Some emulator initialization writes are also made with unmodified stock.
        # Reject every new PC/address pair or increased count; retain raw logs for review.
        unexpected = [(site, n) for site, n in summaries[-1]['image_stores'] if n > stock_stores.get(site, 0)]
        if unexpected:
            raise AssertionError(f'{name}: image stores beyond stock baseline: {unexpected}')
        frames = [line.split()[-1] for line in summaries[-1]['steps']]
        stock_frames = [line.split()[-1] for line in stock_summary['steps']]
        if name in ('four-films', 'next-film', 'title-redraw', 'ten-films'):
            # every film step repaints at once: no frame equals the one before it
            for k in range(1, len(keys.split()) + 1):
                assert frames[-k] != frames[-k - 1], f'{name}: no repaint after delete {len(keys.split()) - k + 1}'
        if name == 'other-rows':
            # tone, shading, sharpness and contrast rows: Delete changes nothing on screen (as stock)
            for k in (4, 6, 8, 10):
                assert frames[-11 + k] == frames[-12 + k], f'{name}: Delete acted on row {k // 2}'
        if name == 'scp-name':
            assert frames[-1] != stock_frames[-1], 'scp-name: the control panel shows no film name'
        results.append(dict(case=name, status='passed', image_stores_beyond_stock=0))
        print(f'{name}: passed', flush=True)
    if not results:
        raise ValueError('no matching test cases')
    (a.out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
