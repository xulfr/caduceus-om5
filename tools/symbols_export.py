#!/usr/bin/env python3
"""Collect named addresses without importing firmware or resolving conflicts."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = re.compile(r'^0x[0-9a-fA-F]{6,8}$')


def ld_symbols(text, source):
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    for name, address in re.findall(r'\b([A-Za-z_]\w*)\s*=\s*(0x[\da-fA-F]+)\s*;', text):
        if int(address, 16) >= 0x10000:
            yield dict(name=name, address=int(address, 16), kind='linker-symbol', source_file=source)
    for name, address in re.findall(r'\.([\w.]+)\s+(0x[\da-fA-F]+)\s*:', text):
        yield dict(name=name, address=int(address, 16), kind='patch-section', source_file=source)


def json_symbols(value, source, path='patch'):
    """Walk all named scalar addresses, preserving component/address-space context."""
    if isinstance(value, dict):
        name = str(value.get('name', path))
        for key, item in value.items():
            child = name if key == 'address' else name + '.' + key
            if isinstance(item, str) and ADDRESS.fullmatch(item):
                yield dict(name=child, address=int(item, 16), kind='patch-address', source_file=source)
            else:
                yield from json_symbols(item, source, child)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from json_symbols(item, source, path + '.' + str(i))


def atlas_symbols(document, source):
    for record in document.get('records', []):
        if not isinstance(record, dict):
            continue
        name = record.get('name') or record.get('id')
        if not name:
            continue
        address = record.get('address', {})
        if not isinstance(address, dict):
            address = {'value': address}
        for field, value in address.items():
            if (isinstance(value, str) and ADDRESS.fullmatch(value)) or (
                    isinstance(value, int) and 0x10000 <= value <= 0xffffffff):
                yield dict(name=name if field == 'value' else name + '.' + field,
                           address=int(value, 16) if isinstance(value, str) else value,
                           kind=record.get('category', 'atlas-address'), source_file=source)


def collect(rows):
    unique = {}
    for row in rows:
        key = (row['name'], row['address'])
        entry = unique.setdefault(key, dict(name=key[0], address=key[1], kinds=set(), source_files=set()))
        entry['kinds'].add(row['kind'])
        entry['source_files'].add(row['source_file'])
    symbols = []
    by_name = defaultdict(list)
    for key, entry in sorted(unique.items()):
        kinds = sorted(entry.pop('kinds'))
        entry['kind'] = kinds[0] if len(kinds) == 1 else 'multiple'
        entry['kinds'] = kinds
        entry['source_files'] = sorted(entry['source_files'])
        symbols.append(entry)
        by_name[key[0]].append(entry)
    conflicts = [{'name': name, 'definitions': entries} for name, entries in sorted(by_name.items())
                 if len(entries) > 1]
    return {'schema': 'om5-symbols/1', 'symbols': symbols, 'conflicts': conflicts}


def export(root, atlas):
    # YAML is deliberately an optional tool dependency, not an installer dependency.
    try:
        import yaml
    except ImportError as exc:
        raise ValueError('PyYAML required: python -m pip install PyYAML==6.0.3') from exc
    files = sorted((atlas / 'records/reference').glob('om5-ii-1100*.yaml'))
    if not files:
        raise ValueError('Atlas om5-ii-1100*.yaml records unavailable; pass --atlas CHECKOUT')
    rows, inputs = [], []
    for path in [root / 'firmware/om5ii/layout.ld', root / 'firmware/om5ii/wb.ld',
                 root / 'firmware/om5ii/patch.json'] + files:
        source = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()
        data = path.read_bytes()
        inputs.append({'source_file': source, 'sha256': hashlib.sha256(data).hexdigest()})
        text = data.decode('utf-8')
        if path.suffix == '.ld':
            rows.extend(ld_symbols(text, source))
        elif path.suffix == '.json':
            rows.extend(json_symbols(json.loads(text), source))
        else:
            for document in yaml.safe_load_all(text):
                rows.extend(atlas_symbols(document or {}, source))
    result = collect(rows)
    result['inputs'] = inputs
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--atlas', type=Path, required=True, help='read-only Atlas checkout')
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--out', type=Path, default=ROOT / 'generated/symbols.json')
    args = p.parse_args(argv)
    try:
        result = export(args.root.resolve(), args.atlas.resolve())
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(f"{len(result['symbols'])} symbols; {len(result['conflicts'])} conflicts; {args.out}")
        return 2 if result['conflicts'] else 0
    except (OSError, ValueError) as exc:
        print('symbols-export: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
