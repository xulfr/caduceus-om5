# @category OM5
import json
import query_common as common


def scalar_values(instruction):
    values = set()
    for index in range(instruction.getNumOperands()):
        for item in instruction.getOpObjects(index):
            if hasattr(item, 'getUnsignedValue'):
                values.add(item.getUnsignedValue() & 0xffffffff)
                values.add(item.getSignedValue() & 0xffffffff)
    return values


def run():
    args = list(getScriptArgs())
    if not args:
        raise ValueError('find_imm.py VALUE [--near ADDR] [--index PATH]')
    value = common.immediate_value(args.pop(0))
    near, index_path, offset = None, None, 0
    while args:
        option = args.pop(0)
        if not args or option not in ('--near', '--index', '--offset'):
            raise ValueError('expected --near ADDR, --index PATH or --offset N')
        text = args.pop(0)
        if option == '--near':
            near = common.address_value(text)
        elif option == '--index':
            index_path = text
        else:
            offset = int(text)
            if offset < 0:
                raise ValueError('offset must be nonnegative')
    listing = currentProgram.getListing()
    if index_path:
        with open(index_path + '.json', 'r') as handle:
            metadata = json.load(handle)
        if (metadata['instruction_count'] != listing.getNumInstructions() or
                metadata['executable_sha256'] != currentProgram.getExecutableSHA256()):
            raise ValueError('stale immediate index; regenerate ExportImmediateIndex.java')
        with open(index_path, 'rb') as handle:
            addresses = list(common.index_addresses(handle, value))
        instructions = (listing.getInstructionAt(toAddr(a)) for a in addresses)
        mode = 'indexed'
    else:
        instructions = listing.getInstructions(True)
        mode = 'listing-scan'
    groups, matches = {}, 0
    for instruction in instructions:
        monitor.checkCancelled()
        if instruction is None:
            continue
        address = instruction.getAddress().getOffset()
        if near is not None and abs(address-near) > 0x10000:
            continue
        if value not in scalar_values(instruction):
            continue
        matches += 1
        function = currentProgram.getFunctionManager().getFunctionContaining(instruction.getAddress())
        key = function.getEntryPoint().getOffset() if function else address
        group = groups.setdefault(key, {'function': common.function_info(function), 'count': 0, 'instructions': []})
        group['count'] += 1
        if len(group['instructions']) < 8:
            group['instructions'].append({'address': '0x%x' % address, 'text': str(instruction)})
    ordered = [groups[key] for key in sorted(groups)]
    return {'value': '0x%x' % value, 'near': ('0x%x' % near) if near is not None else None,
            'near_radius': 0x10000 if near is not None else None, 'mode': mode,
            'match_count': matches, 'function_group_count': len(ordered),
            'offset': offset, 'groups': ordered[offset:offset+30],
            'truncated': offset > 0 or len(ordered) > offset+30 or any(g['count'] > 8 for g in ordered[offset:offset+30])}


if __name__ == '__main__':
    common.execute(globals(), run)
