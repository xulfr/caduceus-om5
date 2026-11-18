# Print incoming xrefs and call sites as one compact JSON object.
# @category OM5
import json
import sys
sys.dont_write_bytecode = True
import query_common as common


def parse_address(text):
    value = int(text, 0)
    if not 0 <= value <= 0xffffffff:
        raise ValueError('ADDRESS must be an unsigned 32-bit address')
    return value


def query(program, address, limit=30):
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
            'xrefs': refs, 'callers': sorted(callers),
            'data_refs': [r for r in refs if 'DATA' in r['type'] or 'READ' in r['type'] or 'WRITE' in r['type']],
            'truncated': count > limit,
            'scope': 'existing Ghidra analysis; indirect/unanalysed references may be missing'}


def run():
    args = getScriptArgs()
    if len(args) not in (1, 2):
        raise ValueError('find_refs.py ADDRESS [LIMIT=30]')
    limit = int(args[1]) if len(args) == 2 else 30
    if limit < 1:
        raise ValueError('LIMIT must be positive')
    result = query(currentProgram, toAddr(parse_address(args[0])), limit)
    return result


if __name__ == '__main__':
    common.execute(globals(), run, 'OM5_REFS ')
