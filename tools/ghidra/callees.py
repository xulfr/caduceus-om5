# @category OM5
import sys
sys.dont_write_bytecode = True
import query_common as common


def run():
    args = getScriptArgs()
    if len(args) != 1:
        raise ValueError('callees.py FUNC')
    function = common.resolve_function(currentProgram, args[0], toAddr)
    if function is None:
        return {'function': None, 'callees': []}
    rows, unresolved = {}, []
    for instruction in currentProgram.getListing().getInstructions(function.getBody(), True):
        monitor.checkCancelled()
        calls = [r for r in instruction.getReferencesFrom() if r.getReferenceType().isCall()]
        if instruction.getFlowType().isCall() and not calls and len(unresolved) < 30:
            unresolved.append('0x%x' % instruction.getAddress().getOffset())
        for ref in calls:
            target = ref.getToAddress()
            callee = currentProgram.getFunctionManager().getFunctionAt(target)
            key = target.getOffset()
            row = rows.setdefault(key, {'entry': '0x%x' % key,
                                        'name': callee.getName() if callee else None, 'sites': []})
            if len(row['sites']) < 8:
                row['sites'].append('0x%x' % instruction.getAddress().getOffset())
    ordered = [rows[key] for key in sorted(rows)]
    return {'function': common.function_info(function), 'callee_count': len(ordered),
            'callees': ordered[:30], 'unresolved_call_sites': unresolved,
            'truncated': len(ordered) > 30}


if __name__ == '__main__':
    common.execute(globals(), run)
