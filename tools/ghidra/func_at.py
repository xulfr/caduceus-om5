# @category OM5
import sys
sys.dont_write_bytecode = True
import query_common as common


def run():
    args = getScriptArgs()
    if len(args) != 1:
        raise ValueError('func_at.py ADDR')
    value = common.address_value(args[0])
    function = currentProgram.getFunctionManager().getFunctionContaining(toAddr(value))
    return {'address': '0x%x' % value, 'function': common.function_info(function)}


if __name__ == '__main__':
    common.execute(globals(), run)
