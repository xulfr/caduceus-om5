# Seed documented stock function entries before the one full auto-analysis pass.
# @category OM5
import json
import time

SEEDS = [(0x60023818, 'malloc'), (0x6002384a, 'stock_free'),
         (0x602d000d, 'stock_get'), (0x60855cdc, 'stock_ui_write'),
         (0x6042394c, 'art_effect_flags'), (0x60389774, 'art_filter_flags'),
         (0x6044dde6, 'development_register_packer'),
         (0x60ce6aa5, 'update_dispatch')]


def run():
    args = getScriptArgs()
    if len(args) != 1:
        raise ValueError('analysis_start.py REPORT.JSON')
    start = time.time()
    for value, name in SEEDS:
        address = toAddr(value)
        if not currentProgram.getMemory().contains(address):
            raise ValueError('seed outside mapped memory: 0x%x' % value)
        if not disassemble(address):
            raise ValueError('seed could not be disassembled: 0x%x' % value)
        if getFunctionAt(address) is None and createFunction(address, name) is None:
            raise ValueError('seed function creation failed: 0x%x' % value)
        currentProgram.getSymbolTable().addExternalEntryPoint(address)
    with open(args[0], 'w') as handle:
        json.dump({'ghidra_run': True, 'started_unix': start,
                   'seeds': [{'address': '0x%x' % a, 'name': n} for a, n in SEEDS],
                   'full_auto_analysis_complete': False}, handle, indent=2)
    println('OM5_ANALYSIS_STARTED ' + str(start))


if __name__ == '__main__':
    run()
