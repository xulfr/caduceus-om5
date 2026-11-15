// PRE module for tests/run_emulator.py: mount the card (unless OM5_UNMOUNTED=1) and watch the Picture Mode
// screen's row descriptor. Only stock addresses are used, so the same module runs on stock and patched images.
//   0x60dad5f5  the visibility updater's last call (patched: jmp pages_hook); a0 = the RAM row descriptor
//               (u16 +0 kind, u16 +4 title id, u16 +6 title style index)
//   0x60f05459  direct_layout's common tail, where stock reads +6 for every row kind; (28,sp) = descriptor
// Between the two only the title id (+4) may change. Alpha4 rewrote +4 with a 32-bit store, which zeroed +6
// (stock 1 -> 0) on every layout of a named slot. No visible effect was seen in OM-Emu (both indices give the
// same style word for this row kind), but it was a write into stock state outside the intended field.
export default async function (g) {
  if (process.env.OM5_UNMOUNTED !== '1') g.__M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  const M = g.__M;
  const guard = g.__layoutGuard = { checked: 0, kind4: 0, violations: [] };
  let pending = null;
  const read = (a) => { const b = Buffer.from(M.dbgRead(a, 12)); return { kind: b.readUInt16LE(0), title: b.readUInt16LE(4), style: b.readUInt16LE(6), w8: b.readUInt32LE(8) }; };
  M.setExecTrace((pc) => {
    pc >>>= 0;
    if (pc === 0x60dad5f5) { const a0 = M.getRegs()[4] >>> 0; pending = { a0, ...read(a0) }; return; }
    if (pc !== 0x60f05459 || !pending) return;
    const sp = M.getRegs()[8] >>> 0;
    const desc = Buffer.from(M.dbgRead(sp + 28, 4)).readUInt32LE(0);
    if (desc !== pending.a0) return;
    const now = read(desc);
    guard.checked++;
    if (pending.kind === 4) guard.kind4++;
    if (now.kind !== pending.kind || now.style !== pending.style || now.w8 !== pending.w8)
      guard.violations.push({ before: pending, after: now });
    pending = null;
  });
}
