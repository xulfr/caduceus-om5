#!/usr/bin/env python3
"""Static rules for a strict build, from camera failures of this family that an emulator does not show.

    python3 tools/dev/static_rules.py BUILD_DIR STOCK.BIN      (mn10300-elf-objdump and -nm on PATH)

1. No 0xfb-prefixed instruction in patch code (reported to misbehave on the OM-3; caduceus-ep7 FIRMWARE_GUIDE).
2. Every word / halfword data table of the patch is aligned (the camera faults on a misaligned access).
3. Every compressed stream of the rebuilt package passes tools/oly_compress.length_fault and keeps OM's packed
   length modulo 4096 (research/OM5II-STREAM-LENGTH-2026-11-15.md).
Not a camera test."""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import oly_compress as oc
from oly_container import parse
from oly_resource import alias_images

TABLES = {'hue_lut': 2, 'light_lut': 2, 'rs_cp_table': 2, 'rs_mono_table': 2, 'rs_tone_ids': 2, 'rs_stock': 2,
          'fl_cells': 2, 'fl_ids': 2, 'text_style': 4, 'text_saturation': 2, 'text_hue': 2, 'text_lightness': 2,
          'text_switch': 2, 'ext_halfpress': 4}
DATA = re.compile(r'<(fl_lo|fl_wbm|fl_path|fl_mode|wb_modes|wb_mono_map|sector_of_record|hue_lut|light_lut|rs_\w+|'
                  r'fl_cells|fl_ids|text_\w+|ext_halfpress|refresh_cases|\.data.*)>')


def main():
    build, stock = Path(sys.argv[1]), Path(sys.argv[2]).read_bytes()
    bad = []
    for unit in ('hsl', 'wb'):
        elf = build / 'assembly' / unit / 'patch.elf'
        in_data = False
        for line in subprocess.check_output(['mn10300-elf-objdump', '-d', str(elf)], text=True).splitlines():
            if line.endswith('>:'):
                in_data = bool(DATA.search(line))
            elif not in_data and re.match(r'\s*[0-9a-f]+:\tfb ', line):
                bad.append(f'{unit}: 0xfb opcode: {line.strip()}')
        seen = set()
        for line in subprocess.check_output(['mn10300-elf-nm', '-n', str(elf)], text=True).splitlines():
            address, _, name = line.split()[:3]
            if name in TABLES:
                seen.add(name)
                if int(address, 16) % TABLES[name]:
                    bad.append(f'{unit}: {name} at {address} is not {TABLES[name]}-byte aligned')
        if unit == 'hsl' and seen != set(TABLES):
            bad.append(f'hsl: tables not found: {sorted(set(TABLES) - seen)}')
    blocks = {b.kind: b for b in parse(stock)}
    spec = json.loads((ROOT / 'firmware/om5ii/patch.json').read_text())
    main_stored = oc.repack_image(blocks[0x100].payload, (build / 'decoded/0100.bin').read_bytes(), split=True,
                                  literal_limit=0, stream_length=spec['components']['0x100'].get('stream_length'))
    for (at, new), (_, old) in zip(oc.stream_lengths(main_stored), oc.stream_lengths(blocks[0x100].payload)):
        if oc.length_fault(new) or new % 4096 != old % 4096:
            bad.append(f'main stream at {at:#x}: {new} bytes ({oc.length_fault(new) or "page offset differs from stock"})')
    for at, new in oc.stream_lengths((build / 'decoded/0101.bin').read_bytes()):
        if oc.length_fault(new):
            bad.append(f'resource stream at {at:#x}: {oc.length_fault(new)}')
    print('\n'.join(bad) if bad else 'STATIC RULES passed: no 0xfb opcode, 14 tables aligned, stream lengths safe')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
