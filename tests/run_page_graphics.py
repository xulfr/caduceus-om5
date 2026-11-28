#!/usr/bin/env python3
"""Colour wheel and tone curve graphics of the Color Profile pages (OM-Emu, E148 only).

    python tests/run_page_graphics.py --emu OM_EMU --build BUILD --out NEW_DIR

Opens the Picture Mode direct screen on Color Profile 1 and reads the composited frames. The wheel must show
the twelve colours' blocks on their spokes at the radius of each value, follow a dial edit, the selected colour
(white edge), the group switch and its INFO hint; the tone page must show the curve and bend it with Shadows. Every
consumed dial step must invalidate the page exactly once (OM only repaints the label that changed; a stale
wheel on the camera would look right here only if this count were wrong). Geometry and palette indices are
those of firmware/om5ii/hsl.s. Emulator only: the frame is OM-Emu's model of the OSD plane, not a camera.
"""
import argparse
import os
from pathlib import Path
import struct
import subprocess
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card_block import card_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OPEN = 's1 ok ok ' + 'right ' * 8
GX, GY, ZERO, STEP = 290, 222, 84, 8
TX, TY = 194, 104
SIN = [0, 32, 55, 64, 55, 32, 0, -32, -55, -64, -55, -32, 0, 32, 55]
# OM-Emu's (Y, Cb, Cr) for the palette indices the patch draws with
COLOURS = [(226, 1, 148), (177, 36, 181), (137, 50, 211), (76, 85, 255), (105, 212, 234), (86, 222, 165),
           (74, 229, 110), (102, 210, 69), (149, 186, 67), (105, 91, 52), (149, 43, 21), (169, 66, 117)]
WHITE, GREY = (255, 128, 128), (85, 128, 128)


def frame(path):
    data = path.read_bytes()
    at, idat = 8, b''
    while at < len(data):
        size, kind = struct.unpack('>I4s', data[at:at + 8])
        if kind == b'IHDR':
            width, height = struct.unpack('>II', data[at + 8:at + 16])
        if kind == b'IDAT':
            idat += data[at + 8:at + 8 + size]
        at += 12 + size
    raw = zlib.decompress(idat)
    return [raw[y * (width * 4 + 1) + 1:(y + 1) * (width * 4 + 1)] for y in range(height)]


def px(rows, x, y):
    return tuple(rows[y][4 * x:4 * x + 3])


def spoke(sector, step):
    r = ZERO + STEP * step
    return GX + ((r * SIN[sector]) >> 6), GY - ((r * SIN[sector + 3]) >> 6)


def is_block(rows, x, y, half, colour):
    """A filled square of this colour centred on (x, y), with something else beyond one of two corners (the
    bar's last block touches the other)."""
    inside = all(px(rows, x + dx, y + dy) == colour for dx in (-half, 0, half) for dy in (-half, 0, half))
    return inside and colour in (px(rows, x, y),) and (px(rows, x + half + 1, y - half - 1) != colour
                                                     or px(rows, x - half - 1, y + half + 1) != colour)


def wheel(rows, values, selected):
    """values: step per sector; selected: set of sectors with the white edge. Returns a list of faults."""
    bad = []
    for s in range(12):
        x, y = spoke(s, values[s])
        if not is_block(rows, x, y, 5, COLOURS[s]):
            bad.append(f'sector {s}: no colour block at step {values[s]} ({x},{y}): {px(rows, x, y)}')
        edge = px(rows, x - 7, y - 7) == WHITE and px(rows, x + 7, y + 7) == WHITE
        if edge != (s in selected):
            bad.append(f'sector {s}: white edge {edge}, expected {s in selected}')
        for t in (-5, 5):
            tx, ty = spoke(s, t)
            # the block (and the white edge of a selected colour, 7 px each way) covers the dot of the next step
            if t != values[s] and max(abs(tx - x), abs(ty - y)) > 7:
                if GREY not in (px(rows, tx, ty), px(rows, tx - 1, ty - 1)):
                    bad.append(f'sector {s}: no scale dot at step {t}')
    return bad


def curve(rows, column):
    """Height (0..192) of the white curve's centre in a 4-pixel column, None when absent."""
    ys = [y for y in range(TY - 4, TY + 197) if px(rows, TX + 4 * column + 1, y) == WHITE]
    return TY + 191 - (min(ys) + max(ys)) / 2 if ys else None


def session(a, name, keys, invalidations):
    out = a.out / name
    cmd = ['node', str(ROOT / 'tools/dev/sess.mjs'), str(a.emu.resolve()), str(a.build.resolve() / 'decoded/0100.bin'),
           str(a.build.resolve() / 'decoded/0101.bin'), str(out), keys, '--ready', '--peekP',
           '--card=' + str(card_for(a.build, a.out))]   # the graphics are in the card block
    env = dict(os.environ, OM_EMU_MODEL='E148', PRE=str(ROOT / 'tests/ui_activity.mjs'),
               POST=str(ROOT / 'tests/ui_activity.mjs'), UI_PAGE_INVALIDATE=str(invalidations))
    run = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    log = run.stdout.decode('utf-8', errors='replace')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'session.log').write_text(log, encoding='utf-8')
    if run.returncode or 'ASSERTIONS passed' not in log:
        raise AssertionError(f'{name}: session failed; see {out / "session.log"}')
    return {int(p.name[:2]): p for p in out.glob('[0-9][0-9]-*.png')}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--emu', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    faults = []

    def check(name, bad):
        print(name, 'ok' if not bad else 'FAILED: ' + '; '.join(bad[:6]), flush=True)
        faults.extend(f'{name}: {b}' for b in bad)

    # frames: 12 = the wheel row; then three steps up, next colour, two steps down, Hue, one step, Midtone Tint, five up
    keys = OPEN + 'down T+ main+1 main+1 main+1 sub-1 main-1 main-1 delete main+1 info ' + 'main+1 ' * 5 + 'T-'
    f = session(a, 'wheel', keys, 14)
    zero = [0] * 12
    check('wheel-entry', wheel(frame(f[12]), zero, {0}))
    check('wheel-edit', wheel(frame(f[15]), [3] + [0] * 11, {0}))
    check('wheel-next-colour', wheel(frame(f[16]), [3] + [0] * 11, {1}))
    check('wheel-second-colour', wheel(frame(f[18]), [3, -2] + [0] * 10, {1}))
    check('wheel-hue-axis', wheel(frame(f[19]), zero, {1}))
    check('wheel-hue-edit', wheel(frame(f[20]), [0, 1] + [0] * 10, {1}))
    check('wheel-midtone-tint', wheel(frame(f[21]), zero, {1}))
    check('wheel-midtone-edit', wheel(frame(f[26]), [0, 5] + [0] * 10, {1}))
    def hint(n, left, right):
        return [row[4 * left:4 * right] for row in frame(f[n])[425:460]]
    check('wheel-group-hint', [] if hint(20, 295, 356) != hint(21, 295, 356)
          and hint(20, 358, 422) == hint(21, 358, 422) else ['group text or INFO glyph did not match'])

    # tone row: straight on entry, then Shadows +5 lifts the lower quarter and leaves the upper half
    f = session(a, 'tone', OPEN + 'down down T+ ' + 'main+1 ' * 5 + 'T-', 5)
    rows = frame(f[13])
    bad = [f'column {c}: {curve(rows, c)}' for c in (4, 12, 24, 36, 44) if curve(rows, c) is None or abs(curve(rows, c) - 4 * c - 2) > 3]
    for c in range(0, 193, 48):
        if px(rows, TX + c, TY + 30) != GREY or px(rows, TX + 30, TY + c) != GREY:
            bad.append(f'grid line {c} missing')
    check('tone-entry', bad)
    rows = frame(f[18])
    lift = curve(rows, 12) - 4 * 12 - 2 if curve(rows, 12) is not None else None
    bad = [] if lift is not None and 17 <= lift <= 23 else [f'Shadows +5 lifts column 12 by {lift}, expected 20']
    if curve(rows, 30) is None or abs(curve(rows, 30) - 4 * 30 - 2) > 3:
        bad.append(f'column 30 moved: {curve(rows, 30)}')
    check('tone-shadows', bad)

    if faults:
        sys.exit('page graphics regressions failed')
    print('all 11 page graphics checks passed')


if __name__ == '__main__':
    main()
