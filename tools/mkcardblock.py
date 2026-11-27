#!/usr/bin/env python3
"""Make OM5MOD/CADUCEUS.BIN, the card block, for one strict E148 build.

    python3 tools/mkcardblock.py --build generated/strict --out CADUCEUS.BIN

The block is firmware/om5ii/cardblock/*.s linked at a fixed address (cardblock/block.ld) against the flashed build's
symbols (BUILD/assembly/hsl/patch.elf). boot.s (cb_load) reads it at the first chance after arming and runs it only if:
  - it is whole: magic 'CADB', ABI 1, length and a CRC-32 of the body;
  - every flashed function the block calls is where this block expects it: for each such symbol the header holds
    {4-aligned address, the word the build has there}, read from BUILD/decoded/0100.bin.
A block made for another build therefore fails its checks and is not run. Writes nothing but OUT."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'firmware/om5ii/cardblock'
MAGIC, ABI, HDR, BODY, MAX, NCHK = 0x42444143, 1, 256, 0x63700100, 0x10000, 29
BASE = 0x60021020                     # the expanded main image's address
ALWAYS = ('cb_find', 'hp_entry')      # boot.s itself: the build the block belongs to


def tool(name):
    path = shutil.which('mn10300-elf-' + name)
    if not path:
        sys.exit(f'mn10300-elf-{name} not found (see docs/OM5_PREALPHA.md for the assembler)')
    return path


def symbols(elf):
    out = {}
    for line in subprocess.run([tool('nm'), str(elf)], capture_output=True, text=True, check=True).stdout.splitlines():
        parts = line.split()
        if len(parts) == 3:
            out[parts[2]] = (int(parts[0], 16), parts[1])
    return out


def code_ranges():
    spec = json.loads((ROOT / 'firmware/om5ii/patch.json').read_text())
    names = set()
    for group in spec['assembly']:
        names.update(group['sections'])
    return [(int(r['address'], 16), int(r['address'], 16) + r['bytes']) for r in spec['ranges']
            if r['name'] in names and 'address' in r]


def build(build_dir, out):
    elf = build_dir / 'assembly/hsl/patch.elf'
    image = (build_dir / 'decoded/0100.bin').read_bytes()
    flashed = symbols(elf)
    ranges = code_ranges()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        objects = []
        for source in sorted(SRC.glob('*.s')):
            obj = tmp / (source.stem + '.o')
            subprocess.run([tool('as'), '-o', str(obj), str(source)], check=True)
            objects.append(obj)
        blk = tmp / 'block.elf'
        subprocess.run([tool('ld'), '--no-relax', '-T', str(SRC / 'block.ld'), '--just-symbols=' + str(elf),
                        '-o', str(blk), *map(str, objects)], check=True)
        body_file = tmp / 'body.bin'
        subprocess.run([tool('objcopy'), '-O', 'binary', '--only-section=.text', str(blk), str(body_file)], check=True)
        body = body_file.read_bytes()
        undefined = set()
        for obj in objects:
            for line in subprocess.run([tool('nm'), '-u', str(obj)], capture_output=True, text=True,
                                       check=True).stdout.splitlines():
                undefined.add(line.split()[-1])
        own = symbols(blk)
    if own.get('cb_entries', (0,))[0] != BODY:
        sys.exit('cb_entries must be the first thing in the block')
    checks = []
    for name in sorted(undefined | set(ALWAYS)):
        if name not in flashed:
            sys.exit(f'{name}: not in the flashed build')
        addr = flashed[name][0]
        if not any(lo <= addr < hi for lo, hi in ranges):
            continue                      # stock code or data: fixed for E148 1.1
        aligned = addr & ~3
        word = struct.unpack_from('<I', image, aligned - BASE)[0]
        checks.append((aligned, word, name))
    checks = sorted(set(checks))
    if len(checks) > NCHK:
        sys.exit(f'{len(checks)} checks, at most {NCHK} fit the header')
    header = struct.pack('<5I', MAGIC, ABI, len(body), zlib.crc32(body), len(checks))
    header += b''.join(struct.pack('<II', a, w) for a, w, _ in checks)
    header = header.ljust(HDR, b'\0')
    data = header + body
    if len(data) > MAX:
        sys.exit(f'{len(data)} bytes; boot.s reads at most {MAX}')
    out.write_bytes(data)
    return dict(bytes=len(data), body=len(body), checks=[(hex(a), n) for a, _, n in checks])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    print(json.dumps(build(a.build, a.out), indent=1))


if __name__ == '__main__':
    main()
