# Explicit analyst-selected function discovery; use -noanalysis to avoid a full pass.
# @category OM5
import json
import re


def parse_seeds(entries):
    if not isinstance(entries, list) or not 1 <= len(entries) <= 20:
        raise ValueError('seeds must contain 1..20 explicit address/name objects')
    seeds = []
    for entry in entries:
        if not isinstance(entry, dict) or 'address' not in entry or 'name' not in entry:
            raise ValueError('seed needs address and name')
        value, name = entry['address'], entry['name']
        address = int(value, 0) if isinstance(value, (str, type(u''))) else int(value)
        if not 0 <= address <= 0xffffffff or not re.match(r'^[A-Za-z_]\w*$', name):
            raise ValueError('invalid seed address/name')
        if any(a == address or n == name for a, n in seeds):
            raise ValueError('duplicate seed address/name')
        seeds.append((address, name))
    return seeds


def run():
    from ghidra.program.model.symbol import SourceType
    args = getScriptArgs()
    if len(args) != 1:
        raise ValueError('seed_functions.py SEEDS.JSON')
    with open(args[0], 'r') as handle:
        seeds = parse_seeds(json.load(handle))
    for value, name in seeds:
        address = toAddr(value)
        owner = getFunctionContaining(address)
        if not currentProgram.getMemory().contains(address):
            raise ValueError('seed outside mapped memory: 0x%x' % value)
        if owner is not None and owner.getEntryPoint() != address:
            raise ValueError('seed is inside another function: 0x%x' % value)
    for value, name in seeds:
        address = toAddr(value)
        if getInstructionAt(address) is None and not disassemble(address):
            raise ValueError('seed disassembly failed: 0x%x' % value)
        function = getFunctionAt(address) or createFunction(address, name)
        if function is None:
            raise ValueError('function creation failed: 0x%x' % value)
        function.setName(name, SourceType.USER_DEFINED)
    println('OM5_SEEDS ' + json.dumps({'ghidra_run': True, 'seeded': len(seeds),
                                       'function_count': currentProgram.getFunctionManager().getFunctionCount()}))


if __name__ == '__main__':
    run()
