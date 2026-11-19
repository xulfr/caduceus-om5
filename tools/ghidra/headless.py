#!/usr/bin/env python3
"""Prepare verified stock inputs and invoke Ghidra without changing firmware."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import space_map
import symbols_export

LANGUAGE = 'MN103:LE:32:AM33-2'
MODULE_COMMIT = '01fc3928802d227b2d5f06b83f40543ecbe92f40'


def import_command(ghidra, out, analyze=False):
    executable = ghidra / 'support' / ('analyzeHeadless.bat' if sys.platform == 'win32' else 'analyzeHeadless')
    scripts = Path(__file__).resolve().parent
    command = [str(executable), str(out / 'projects'), 'E148-1100',
               '-import', str(out / 'main.expanded.bin'), '-processor', LANGUAGE,
               '-loader', 'BinaryLoader', '-loader-baseAddr', hex(space_map.BASE),
               # Installed processor-module scripts are discovered by Ghidra.
               # A single extra path also avoids Windows batch semicolon parsing.
               '-scriptPath', str(scripts),
               '-preScript', 'import_sections.py', str(out / 'space-map.json'),
               str(out / 'main.expanded.bin'), str(out / 'symbols.json')]
    if not analyze:
        command.append('-noanalysis')
    else:
        command.extend(['-preScript', 'analysis_start.py', str(out / 'analysis-report.json'),
                        '-postScript', 'MN103FixCallFrames.java',
                        '-postScript', 'seed_functions.py', str(scripts / 'e148_research_seeds.json'),
                        '-postScript', 'MN103FixCallFrames.java',
                        '-postScript', 'analysis_report.py', str(out / 'analysis-report.json'),
                        '-postScript', 'ExportImmediateIndex.java', str(out / 'immediates.idx')])
    return command


def prepare(stock, atlas, out):
    # Do all validation before writing any artifacts.
    _, image = space_map.read_stock(stock)
    # Import needs loader extents only. Do not make Jython parse the exhaustive
    # filler report (millions of rows) just to recover ten sections.
    report = {'schema': 'om5-space-map/1', 'base': space_map.BASE,
              'image_sha256': hashlib.sha256(image).hexdigest(),
              'stock_sha256': space_map.STOCK_SHA,
              'sections': space_map.loader_regions(image)}
    symbols = symbols_export.export(space_map.ROOT, atlas)
    if symbols['conflicts']:
        raise ValueError('symbol conflicts: run symbols_export.py and inspect conflicts before importing')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'projects').mkdir(exist_ok=True)
    (out / 'main.expanded.bin').write_bytes(image)
    (out / 'space-map.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (out / 'symbols.json').write_text(json.dumps(symbols, indent=2) + '\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', default=__import__('os').environ.get('OM5_STOCK'))
    p.add_argument('--atlas', required=True, type=Path)
    p.add_argument('--ghidra', type=Path, help='Ghidra install; omit to only prepare inputs')
    p.add_argument('--out', type=Path, default=space_map.ROOT / 'generated/ghidra')
    p.add_argument('--analyze', action='store_true', help='run auto-analysis then fix MN103 call frames')
    args = p.parse_args()
    try:
        if args.ghidra and (args.out / 'projects/E148-1100.gpr').exists():
            raise ValueError('Ghidra project already exists; use a fresh --out or query the existing project')
        prepare(args.stock, args.atlas.resolve(), args.out.resolve())
        if args.ghidra:
            return subprocess.run(import_command(args.ghidra.resolve(), args.out.resolve(), args.analyze), check=False).returncode
        print('Prepared inputs only; Ghidra import/analysis NOT RUN.')
    except (OSError, ValueError) as exc:
        print('headless: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
