# Bounded live smoke test of the E148 import and MN103 direct-call xrefs.
# Run with -readOnly: these analysis changes should not be persisted.
# @category OM5
import json


def run():
    from ghidra.app.cmd.disassemble import DisassembleCommand
    from ghidra.program.model.address import AddressSet
    memory = currentProgram.getMemory()
    for value in (0x60023818, 0x6002384a, 0x6002424e, 0x612a4fff):
        if not memory.contains(toAddr(value)):
            raise ValueError('expected loaded/resident address absent: 0x%x' % value)
    for value in (0x60846000, 0x612a5000):
        if memory.contains(toAddr(value)):
            raise ValueError('native unloaded gap was mapped: 0x%x' % value)
    labels = list(currentProgram.getSymbolTable().getSymbols(toAddr(0x60023818)))
    if not any(symbol.getName() == 'malloc' for symbol in labels):
        raise ValueError('malloc label missing')
    start, end = toAddr(0x6002424e), toAddr(0x6002426b)
    if not DisassembleCommand(start, AddressSet(start, end), True).applyTo(currentProgram, monitor):
        raise ValueError('bounded native caller disassembly failed')
    for source, target in ((0x60024251, 0x60023818), (0x60024263, 0x6002384a)):
        refs = currentProgram.getReferenceManager().getReferencesTo(toAddr(target))
        if not any(ref.getFromAddress().getOffset() == source and ref.getReferenceType().isCall() for ref in refs):
            raise ValueError('native call xref missing: 0x%x -> 0x%x' % (source, target))
    println('OM5_IMPORT_CHECK ' + json.dumps({'passed': True, 'native_call_xrefs': 2,
                                             'scope': 'bounded static smoke test; no full auto-analysis'}))


if __name__ == '__main__':
    run()
