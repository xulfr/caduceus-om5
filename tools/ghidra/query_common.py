"""Shared bounded JSON/query helpers; Python 2.7 (Ghidra) and Python 3 compatible."""
import json
import struct

SCOPE = 'Static Ghidra analysis; indirect/unanalysed code may be missing.'


def address_value(text):
    value = int(text, 0)
    if not 0 <= value <= 0xffffffff:
        raise ValueError('address must be unsigned 32-bit')
    return value


def immediate_value(text):
    value = int(text, 0)
    if not -0x80000000 <= value <= 0xffffffff:
        raise ValueError('immediate outside 32-bit range')
    return value & 0xffffffff


def function_info(function):
    if function is None:
        return None
    body = function.getBody()
    return {'entry': '0x%x' % function.getEntryPoint().getOffset(),
            'name': function.getName(), 'size': body.getNumAddresses(),
            'min': '0x%x' % body.getMinAddress().getOffset(),
            'end_exclusive': '0x%x' % (body.getMaxAddress().getOffset()+1)}


def resolve_function(program, text, to_address):
    try:
        address = to_address(address_value(text))
    except ValueError:
        functions = {}
        for symbol in program.getSymbolTable().getSymbols(text):
            function = program.getFunctionManager().getFunctionAt(symbol.getAddress())
            if function:
                functions[function.getEntryPoint().getOffset()] = function
        if len(functions) != 1:
            raise ValueError('function name absent or ambiguous: ' + text)
        return list(functions.values())[0]
    return program.getFunctionManager().getFunctionContaining(address)


def truncate_lines(text, max_lines=32, max_chars=12000):
    if max_lines < 1:
        raise ValueError('max-lines must be positive')
    lines = text.splitlines()
    selected = lines[:max_lines]
    joined = '\n'.join(selected)
    clipped = joined[:max_chars]
    return {'lines': clipped.splitlines(), 'total_lines': len(lines),
            'truncated': len(lines) > max_lines or len(joined) > max_chars}


def index_addresses(handle, value):
    """Binary search unsigned big-endian (value,address) records, eight bytes each."""
    handle.seek(0, 2)
    size = handle.tell()
    if size % 8:
        raise ValueError('truncated immediate index')
    lo, hi = 0, size // 8
    while lo < hi:
        middle = (lo + hi) // 2
        handle.seek(middle*8)
        current = struct.unpack('>II', handle.read(8))[0]
        if current < value:
            lo = middle + 1
        else:
            hi = middle
    handle.seek(lo*8)
    while handle.tell() < size:
        current, address = struct.unpack('>II', handle.read(8))
        if current != value:
            break
        yield address


def execute(namespace, action, marker='OM5_QUERY '):
    if 'currentProgram' not in namespace:
        print(json.dumps({'ghidra_run': False, 'error': 'Run through tools/ghidra/query.py or Ghidra headless.'}))
        return 1
    try:
        result = action()
        result.update(ghidra_run=True, scope=result.get('scope', SCOPE))
    except Exception as exc:
        result = {'ghidra_run': True, 'error': str(exc), 'scope': SCOPE}
    namespace['println'](marker + json.dumps(result, separators=(',', ':')))
    return 1 if 'error' in result else 0
