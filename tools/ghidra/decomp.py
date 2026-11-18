# @category OM5
import sys
sys.dont_write_bytecode = True
import query_common as common


def run():
    from ghidra.app.decompiler import DecompInterface
    args = list(getScriptArgs())
    if not args:
        raise ValueError('decomp.py FUNC [--max-lines N] [--start-line N]')
    target, max_lines, start_line = args.pop(0), 32, 0
    while args:
        option = args.pop(0)
        if not args or option not in ('--max-lines', '--start-line'):
            raise ValueError('expected --max-lines N or --start-line N')
        value = int(args.pop(0))
        if option == '--max-lines':
            max_lines = value
        else:
            start_line = value
    if not 1 <= max_lines <= 200 or start_line < 0:
        raise ValueError('max-lines must be 1..200; start-line must be nonnegative')
    function = common.resolve_function(currentProgram, target, toAddr)
    if function is None:
        return {'function': None, 'decompile_completed': False}
    decompiler = DecompInterface()
    try:
        if not decompiler.openProgram(currentProgram):
            raise ValueError('decompiler could not open program')
        result = decompiler.decompileFunction(function, 45, monitor)
        row = {'function': common.function_info(function), 'decompile_completed': result.decompileCompleted()}
        if result.decompileCompleted():
            row.update(common.truncate_lines(result.getDecompiledFunction().getC(), max_lines, start_line=start_line))
        else:
            row['error'] = str(result.getErrorMessage())
        return row
    finally:
        decompiler.dispose()


if __name__ == '__main__':
    common.execute(globals(), run)
