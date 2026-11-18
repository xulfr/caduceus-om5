#!/usr/bin/env python3
"""Read-only E148 1.1 loader map. Unreferenced filler is a candidate, not proof of safety."""
import argparse
from bisect import bisect_right
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys

import oly_compress
import oly_container
from om5ii_boot_audit import BASE, loader_regions

ROOT = Path(__file__).resolve().parents[1]
STOCK_SHA = '9de5d77e1d290fa2ed4ebc7d75cee0ed490befbc89566722467d1d421d66d637'


def number(value):
    return int(value, 0) if isinstance(value, str) else int(value)


def read_stock(path):
    if not path or not Path(path).is_file():
        raise ValueError('stock firmware unavailable: set OM5_STOCK or pass --stock (official E148 1.1 BIN)')
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != STOCK_SHA:
        raise ValueError('stock firmware SHA-256 does not match official E148 1.1')
    blocks = [b for b in oly_container.parse(data) if b.kind == 0x100]
    if len(blocks) != 1 or blocks[0].header[2:4] != bytes.fromhex('1480'):
        raise ValueError('expected one E148 main component 0x100')
    block = blocks[0]
    return block, oly_compress.expand_image(block.payload)


def union_size(intervals):
    end, total = -1, 0
    for lo, hi in sorted(intervals):
        total += max(0, hi - max(lo, end))
        end = max(end, hi)
    return total


def intersection(lo, hi, intervals):
    return [(max(lo, a), min(hi, b)) for a, b in intervals if a < hi and lo < b]


def subtract_intervals(lo, hi, blocked):
    """Complement of clipped, possibly overlapping intervals; ends are exclusive."""
    cursor, result = lo, []
    for start, end in sorted(intersection(lo, hi, blocked)):
        if cursor < start:
            result.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < hi:
        result.append((cursor, hi))
    return result


def overlays(manifest):
    """Ranges are authoritative byte counts; assembly/data_edits provide names, not extra usage."""
    rows = []
    for row in manifest.get('ranges', []):
        if number(row['component']) != 0x100 or 'address' not in row:
            continue
        start, size = number(row['address']), number(row['bytes'])
        if size <= 0:
            raise ValueError('invalid patch range size: ' + row['name'])
        rows.append({'name': row['name'], 'start': start, 'end': start + size, 'bytes': size})
    return rows


def filler_runs(image, regions, base=BASE, min_run=1):
    if min_run < 1:
        raise ValueError('min_run must be positive')
    runs = []
    for r in regions:
        if not base <= r['start'] < r['end'] <= base + len(image):
            raise ValueError('loaded section outside expanded image')
        for m in re.finditer(rb'\x00+|\xff+', image[r['start'] - base:r['end'] - base]):
            if m.end() - m.start() >= min_run:
                runs.append({'start': r['start'] + m.start(), 'end': r['start'] + m.end(),
                             'fill': image[r['start'] - base + m.start()], 'section': r['id'],
                             'pointer_refs': []})
    runs.sort(key=lambda r: r['start'])
    for a, b in zip(sorted(regions, key=lambda r: r['start']),
                    sorted(regions, key=lambda r: r['start'])[1:]):
        if a['end'] > b['start']:
            raise ValueError('overlapping native loaded sections')
    return runs


def scan_pointers(image, runs, base=BASE):
    """LE dwords at EVERY byte alignment, including cached/uncached RAM aliases.

    Scan all expanded-main bytes (resident boot and libraries included), conservatively
    retaining coincidental instruction matches. Relative/computed references are NOT covered.
    """
    starts = [r['start'] for r in runs]
    high_bytes = {r['start'] >> 24 for r in runs} | {(r['start'] + 0x40000000) >> 24 for r in runs}
    for at in range(len(image) - 3):
        if image[at + 3] not in high_bytes:
            continue
        raw = struct.unpack_from('<I', image, at)[0]
        target = raw - 0x40000000 if 0xa0000000 <= raw < 0xc0000000 else raw
        i = bisect_right(starts, target) - 1
        if i >= 0 and target < runs[i]['end']:
            runs[i]['pointer_refs'].append({'from': base + at, 'target': raw})


def build_map(image, regions, manifest, base=BASE, payload_file_offset=32,
              built=None, min_run=1):
    if built is not None and len(built) != len(image):
        raise ValueError('built expanded image size differs from stock')
    usage = overlays(manifest)
    for row in usage:
        if not any(r['start'] <= row['start'] < row['end'] <= r['end'] for r in regions):
            raise ValueError('patch range outside native loaded bounds: ' + row['name'])
    runs = filler_runs(image, regions, base, min_run)
    scan_pointers(image, runs, base)
    used_intervals = [(u['start'], u['end']) for u in usage]
    candidates = []
    for run in runs:
        run['bytes'] = run['end'] - run['start']
        run['status'] = 'partly-referenced-filler' if run['pointer_refs'] else 'unreferenced-filler-candidate'
        run['patch_bytes'] = union_size(intersection(run['start'], run['end'], used_intervals))
        # An absolute pointer establishes its target address, not the pointee's
        # extent. Reserve that byte only, report unknown extent, and retain every
        # source hit for review. Do not let a hit in used code erase an unused tail.
        pointed = sorted({ref['target'] - 0x40000000 if 0xa0000000 <= ref['target'] < 0xc0000000
                          else ref['target'] for ref in run['pointer_refs']})
        reference_ranges = [(target, target+1) for target in pointed]
        remaining = subtract_intervals(run['start'], run['end'], reference_ranges)
        candidates.extend(remaining)
        free = subtract_intervals(run['start'], run['end'], reference_ranges + used_intervals)
        run['candidate_free_bytes'] = union_size(free)
        if pointed:
            run['reference_ranges'] = [{'start': a, 'end': b, 'pointee_extent_known': False}
                                       for a, b in reference_ranges]
            run['candidate_free_ranges'] = [{'start': a, 'end': b} for a, b in free]
    sections = []
    for r in regions:
        lo, hi = r['start'], r['end']
        contained = [u for u in usage if lo <= u['start'] < u['end'] <= hi]
        # Source is the native logical-flash address. The expanded payload preserves
        # virtual offsets; a compressed section has no per-byte physical file mapping.
        row = dict(r, compressed=bool(r['compressed']), loaded_bytes=hi - lo,
                   expanded_offset=lo - base, file_offset=payload_file_offset + lo - base,
                   patch_bytes_used=union_size(intersection(lo, hi, used_intervals)),
                   candidate_free_bytes=sum(g['candidate_free_bytes'] for g in runs if g['section'] == r['id']),
                   overlays=contained)
        if built is not None:
            row['changed_bytes'] = sum(a != b for a, b in zip(image[lo-base:hi-base], built[lo-base:hi-base]))
            declared_changes = 0
            cursor = lo
            for a, b in sorted(intersection(lo, hi, used_intervals)):
                a = max(a, cursor)
                if b > a:
                    declared_changes += sum(x != y for x, y in zip(image[a-base:b-base], built[a-base:b-base]))
                cursor = max(cursor, b)
            row['changes_outside_manifest'] = row['changed_bytes'] - declared_changes
        sections.append(row)
    # Extension capacity stops at the next overlay or native loaded end. Free bytes
    # count only pointer-unreferenced filler, never all bytes in that capacity.
    extension_names = {'ext2', 'ext5', 'ext6', 'ext7', 'ext8', 'ext10', 'extvec',
                       'wb_extension', 'wb_body', 'wb_profile'}
    region_usage = []
    for u in usage:
        owner = next(r for r in regions if r['start'] <= u['start'] < r['end'])
        end = u['end']
        if u['name'] in extension_names:
            end = min([owner['end']] + [v['start'] for v in usage if u['end'] <= v['start'] < owner['end']])
        free = union_size(intersection(u['start'], end, candidates))
        free -= union_size([part for a, b in intersection(u['start'], end, candidates)
                            for part in intersection(a, b, used_intervals)])
        region_usage.append(dict(u, capacity_end=end, capacity_bytes=end-u['start'],
                                 candidate_free_bytes=free))
    return {'schema': 'om5-space-map/2', 'base': base, 'image_sha256': hashlib.sha256(image).hexdigest(),
            'min_run': min_run, 'sections': sections, 'gaps': runs, 'regions': region_usage,
            'limitations': ['Unreferenced filler is an inference, not certified usable space.',
                            'All-alignment absolute LE32 scan includes uncached aliases and false positives.',
                            'Only pointed-to bytes are reserved; actual pointee extents are UNKNOWN and require review.',
                            'Relative branches, computed pointers, runtime ownership and constructor extents need review.',
                            'file_offset is the encoded BIN location of a section start; compressed bytes have no linear mapping.']}


def summary(report):
    lines = ['E148 1.1: native loaded bounds; ends exclusive; free = unreferenced filler CANDIDATE.',
             'Absolute pointer scan cannot prove absence of relative/computed/runtime references.']
    for r in report['sections']:
        lines.append(f"section {r['id']:2}: {r['start']:#010x}..{r['end']:#010x} file={r['file_offset']:#x} "
                     f"{'compressed' if r['compressed'] else 'raw'} used={r['patch_bytes_used']} free?={r['candidate_free_bytes']}")
    for r in report['regions']:
        if r['name'].startswith(('ext', 'wb_')):
            lines.append(f"{r['name']}: used={r['bytes']} free?={r['candidate_free_bytes']} capacity={r['capacity_bytes']}")
    hooks = [r for r in report['regions'] if not r['name'].startswith(('ext', 'wb_'))]
    lines.append(f"other hooks/data: {len(hooks)} ranges, {union_size([(r['start'], r['end']) for r in hooks])} bytes; details in JSON")
    lines.append(f"filler runs: {len(report['gaps'])}; pointer-referenced: {sum(bool(g['pointer_refs']) for g in report['gaps'])}")
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', default=os.environ.get('OM5_STOCK'))
    parser.add_argument('--built', type=Path, help='decoded, expanded main image (not an OE BIN)')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'firmware/om5ii/patch.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'generated')
    parser.add_argument('--min-run', type=int, default=1, help='default reports every uniform 00/FF run')
    args = parser.parse_args(argv)
    try:
        block, image = read_stock(args.stock)
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        report = build_map(image, loader_regions(image), manifest,
                           payload_file_offset=block.offset + 32,
                           built=args.built.read_bytes() if args.built else None, min_run=args.min_run)
        report['stock_sha256'] = STOCK_SHA
        report['manifest_sha256'] = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        streams = {p: (packed, raw) for p, packed, raw in oly_compress.spans(block.payload)}
        for r in report['sections']:
            if block.offset + r['source'] - block.address != r['file_offset']:
                raise ValueError('descriptor flash source disagrees with main file mapping')
            if r['compressed']:
                packed, raw = streams[r['expanded_offset']]
                r.update(stored_stream_bytes=32+packed, expanded_stream_bytes=raw)
                if r['loaded_bytes'] > raw:
                    raise ValueError('native load exceeds expanded stream')
        if args.built:
            report['built_sha256'] = hashlib.sha256(args.built.read_bytes()).hexdigest()
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / 'space-map.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        text = summary(report)
        (args.out / 'space-map.txt').write_text(text, encoding='utf-8')
        print(text, end='')
    except (OSError, ValueError, KeyError) as exc:
        print('space-map: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
