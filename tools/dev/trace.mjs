// PRE module: mount the card, then print registers and the code addresses on the stack each time execution
// reaches one of TRACE_PCS (hex, comma separated). TRACE_D0=LO-HI keeps hits with d0 in that range; TRACE_MAX caps.
import fs from 'node:fs';
export default async function (g) {
  g.__M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  const pcs = new Set((process.env.TRACE_PCS ?? '').split(',').filter(Boolean).map((x) => parseInt(x, 16) >>> 0));
  const M = g.__M; const max = Number(process.env.TRACE_MAX ?? 400); let n = 0;
  const filt = process.env.TRACE_D0 ? process.env.TRACE_D0.split('-').map(Number) : null;
  const hx = (v) => (v >>> 0).toString(16);
  g.__trace = { on: true };
  M.setExecTrace((pc) => {
    if (!pcs.has(pc >>> 0) || !g.__trace.on) return;
    const r = M.getRegs();
    if (filt && !((r[0] >>> 0) >= filt[0] && (r[0] >>> 0) <= filt[1])) return;
    if (n++ >= max) return;
    const sp = r[8] >>> 0; let bt = [];
    try { const b = Buffer.from(M.dbgRead(sp, 512)); for (let o = 0; o + 4 <= b.length; o += 4) { const v = b.readUInt32LE(o); if (v >= 0x60021020 && v < 0x617e1020) bt.push(hx(v) + '@' + o); } } catch (e) { bt = ['?']; }
    console.log(`TR ${hx(pc)} regs ${[...r].slice(0, 12).map(hx).join(' ')} | ${bt.slice(0, 28).join(' ')}`);
  });
}
