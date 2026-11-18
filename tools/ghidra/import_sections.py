# Map verified expanded main to native sections and apply conflict-free symbols.
# @category OM5
# Ghidra's bundled Jython (Python 2.7); not a standalone CPython script.
import hashlib
import json
import re


def import_plan(report, image):
    if report.get('schema') != 'om5-space-map/1':
        raise ValueError('unsupported space map')
    if hashlib.sha256(image).hexdigest() != report['image_sha256']:
        raise ValueError('expanded image and space map disagree')
    base = report['base']
    blocks = []
    for row in sorted(report['sections'], key=lambda r: r['start']):
        start, end = row['start'], row['end']
        if not base <= start < end <= base + len(image):
            raise ValueError('section outside image')
        if blocks and start < blocks[-1]['end']:
            raise ValueError('overlapping sections')
        blocks.append(dict(name='section_%d' % row['id'], start=start, end=end, offset=start-base))
    # Boot code, descriptors and allocator precede section 1. This analysis-only
    # prefix is NOT part of the space map's candidate-free accounting.
    if blocks and blocks[0]['start'] > base:
        blocks.insert(0, dict(name='resident_prefix', start=base, end=blocks[0]['start'], offset=0))
    return blocks


def label_plan(document):
    if document.get('schema') != 'om5-symbols/1' or document.get('conflicts'):
        raise ValueError('unsupported symbols or unresolved conflicts')
    labels = []
    seen = {}
    for row in document['symbols']:
        # Keep all original names in the JSON; Ghidra labels have a smaller alphabet.
        name = re.sub(r'[^A-Za-z0-9_]', '_', row['name'])
        if not name or name[0].isdigit():
            name = 'sym_' + name
        if name in seen:
            raise ValueError('symbol names collide after Ghidra sanitization: ' + name)
        seen[name] = row['name']
        labels.append((name, row['address']))
    return labels


def run():
    from java.io import ByteArrayInputStream
    from ghidra.program.model.symbol import SourceType
    args = getScriptArgs()
    if len(args) != 3:
        raise ValueError('import_sections.py SPACE-MAP.JSON MAIN.EXPANDED.BIN SYMBOLS.JSON')
    with open(args[0], 'r') as handle:
        report = json.load(handle)
    with open(args[1], 'rb') as handle:
        image = handle.read()
    with open(args[2], 'r') as handle:
        labels = label_plan(json.load(handle))
    blocks = import_plan(report, image)
    memory = currentProgram.getMemory()
    # BinaryLoader initially maps the full file. Remove it before creating the
    # real sections; inter-section flash padding must not be executable memory.
    for block in list(memory.getBlocks()):
        memory.removeBlock(block, monitor)
    for block in blocks:
        size = block['end'] - block['start']
        stream = ByteArrayInputStream(image[block['offset']:block['offset']+size])
        try:
            created = memory.createInitializedBlock(block['name'], toAddr(block['start']), stream, size, monitor, False)
        finally:
            stream.close()
        created.setRead(True)
        created.setWrite(False)
        created.setExecute(True)
    for name, address in labels:
        createLabel(toAddr(address), name, False, SourceType.USER_DEFINED)
    # Label all addresses, but do not declare data/table labels to be functions.
    println(json.dumps({'blocks': len(blocks), 'labels': len(labels), 'auto_functions': False}))


if __name__ == '__main__':
    run()
