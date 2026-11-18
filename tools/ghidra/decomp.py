# @category OM5
import query_common as common


def run():
    from ghidra.app.decompiler import DecompInterface
    args = list(getScriptArgs())
    if not args:
        raise ValueError('decomp.py FUNC [--max-lines N]')
    target, max_lines = args.pop(0), 32
    if args:
        if len(args) != 2 or args[0] != '--max-lines':
            raise ValueError('decomp.py FUNC [--max-lines N]')
        max_lines = int(args[1])
    if not 1 <= max_lines <= 200:
        raise ValueError('max-lines must be 1..200')
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
            row.update(common.truncate_lines(result.getDecompiledFunction().getC(), max_lines))
        else:
            row['error'] = str(result.getErrorMessage())
        return row
    finally:
        decompiler.dispose()


if __name__ == '__main__':
    common.execute(globals(), run)
