// Build once after analysis. Args: INDEX-PATH. Records: unsigned BE32 value/address.
// @category OM5
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.scalar.Scalar;
import java.io.*;
import java.util.*;

public class ExportImmediateIndex extends GhidraScript {
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("ExportImmediateIndex.java INDEX-PATH");
        TreeMap<Long, TreeSet<Long>> values = new TreeMap<>();
        InstructionIterator instructions = currentProgram.getListing().getInstructions(true);
        while (instructions.hasNext()) {
            monitor.checkCancelled();
            Instruction instruction = instructions.next();
            long address = instruction.getAddress().getOffset();
            for (int op = 0; op < instruction.getNumOperands(); op++) {
                for (Object item : instruction.getOpObjects(op)) if (item instanceof Scalar) {
                    Scalar scalar = (Scalar)item;
                    for (long value : new long[]{scalar.getUnsignedValue() & 0xffffffffL, scalar.getSignedValue() & 0xffffffffL})
                        values.computeIfAbsent(value, k -> new TreeSet<>()).add(address);
                }
            }
        }
        long count = 0;
        try (DataOutputStream output = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(args[0])))) {
            for (Map.Entry<Long, TreeSet<Long>> entry : values.entrySet()) for (long address : entry.getValue()) {
                output.writeInt(entry.getKey().intValue()); output.writeInt((int)address); count++;
            }
        }
        try (PrintWriter metadata = new PrintWriter(args[0]+".json")) {
            metadata.printf("{\"ghidra_run\":true,\"records\":%d,\"instruction_count\":%d,\"executable_sha256\":\"%s\"}%n",
                count, currentProgram.getListing().getNumInstructions(), currentProgram.getExecutableSHA256());
        }
        println("OM5_INDEX records="+count);
    }
}
