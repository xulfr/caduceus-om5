# Print incoming xrefs and call sites as one compact JSON object.
# @category OM5
import json


def parse_address(text):
    value = int(text, 0)
    if not 0 <= value <= 0xffffffff:
        raise ValueError('ADDRESS must be an unsigned 32-bit address')
    return value


def query(program, address, limit=100):
    refs, callers, count = [], set(), 0
    iterator = program.getReferenceManager().getReferencesTo(address)
    for ref in iterator:
        count += 1
        if len(refs) >= limit:
            continue
        source = ref.getFromAddress()
        function = program.getFunctionManager().getFunctionContaining(source)
        kind = ref.getReferenceType()
        row = {'from': '0x%x' % source.getOffset(), 'type': str(kind)}
        if function:
            row['function'] = function.getName()
        refs.append(row)
        if kind.isCall():
            callers.add(('0x%x' % function.getEntryPoint().getOffset()) if function else row['from'])
    return {'address': '0x%x' % address.getOffset(), 'xref_count': count,
            'xrefs': refs, 'callers': sorted(callers), 'truncated': count > limit,
            'scope': 'existing Ghidra analysis; indirect/unanalysed references may be missing'}


def run():
    args = getScriptArgs()
    if len(args) not in (1, 2):
        raise ValueError('find_refs.py ADDRESS [LIMIT=100]')
    limit = int(args[1]) if len(args) == 2 else 100
    if limit < 1:
        raise ValueError('LIMIT must be positive')
    result = query(currentProgram, toAddr(parse_address(args[0])), limit)
    # Ghidra's own log lines surround this marker; the payload itself is short JSON.
    println('OM5_REFS ' + json.dumps(result, separators=(',', ':')))


if __name__ == '__main__':
    run()
