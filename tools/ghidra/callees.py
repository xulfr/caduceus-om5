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
    rows, tails, shared, unresolved, unresolved_count = {}, {}, {}, [], 0
    for instruction in currentProgram.getListing().getInstructions(function.getBody(), True):
        monitor.checkCancelled()
        calls = [r for r in instruction.getReferencesFrom() if r.getReferenceType().isCall()]
        fallthrough = instruction.getFallThrough()
        if fallthrough is not None and not function.getBody().contains(fallthrough):
            successor = currentProgram.getFunctionManager().getFunctionAt(fallthrough)
            if successor:
                shared[successor.getEntryPoint().getOffset()] = common.function_info(successor)
        if instruction.getFlowType().isCall() and not calls:
            unresolved_count += 1
            if len(unresolved) < 30:
                unresolved.append('0x%x' % instruction.getAddress().getOffset())
        for ref in instruction.getReferencesFrom():
            if ref.getReferenceType().isJump():
                callee = currentProgram.getFunctionManager().getFunctionAt(ref.getToAddress())
                if callee and callee.getEntryPoint() != function.getEntryPoint():
                    tails[callee.getEntryPoint().getOffset()] = common.function_info(callee)
        for ref in calls:
            target = ref.getToAddress()
            callee = currentProgram.getFunctionManager().getFunctionAt(target)
            key = target.getOffset()
            row = rows.setdefault(key, {'entry': '0x%x' % key,
                                        'name': callee.getName() if callee else None, 'sites': [], 'site_count': 0})
            row['site_count'] += 1
            if len(row['sites']) < 8:
                row['sites'].append('0x%x' % instruction.getAddress().getOffset())
    ordered = [rows[key] for key in sorted(rows)]
    return {'function': common.function_info(function), 'callee_count': len(ordered),
            'callees': ordered[:30], 'unresolved_call_sites': unresolved,
            'unresolved_call_count': unresolved_count,
            'tail_jump_candidates': [tails[key] for key in sorted(tails)[:30]],
            'shared_entry_successors': [shared[key] for key in sorted(shared)[:30]],
            'truncated': len(ordered) > 30 or len(tails) > 30 or unresolved_count > 30 or
                         len(shared) > 30 or
                         any(row['site_count'] > 8 for row in ordered[:30])}


if __name__ == '__main__':
    common.execute(globals(), run)
