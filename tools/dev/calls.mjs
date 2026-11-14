// PRE module: mount the card, then log every call made while tracing is on (keys T+ / T-) to the file CALLS:
//   "SP caller target d0 d1 a0 a1" per call. View with tools/dev/calltree.py. Emulator only.
import fs from 'node:fs';
export default async function (g) {
  g.__M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  const M = g.__M; g.__trace = { on: false };
  const out = fs.openSync(process.env.CALLS ?? 'calls.txt', 'w');
  let prev = 0; const hx = (v) => (v >>> 0).toString(16); let buf = [];
  const isCall = new Map();
  M.setExecTrace((pc) => {
    const p = prev; prev = pc;
    if (!g.__trace.on) return;
    const d = pc - p; if (d > 0 && d <= 7) return;
    let c = isCall.get(p);
    if (c === undefined) { let b; try { b = M.dbgRead(p, 2); } catch (e) { b = [0, 0]; }
      c = b[0] === 0xcd || b[0] === 0xdd || (b[0] === 0xf0 && (b[1] & 0xfc) === 0xf0) || (b[0] === 0xfa && b[1] === 0xff) || (b[0] === 0xfc && b[1] === 0xff); isCall.set(p, c); }
    if (!c) return;
    const r = M.getRegs();
    buf.push(`${hx(r[8])} ${hx(p)} ${hx(pc)} ${hx(r[0])} ${hx(r[1])} ${hx(r[4])} ${hx(r[5])}`);
    if (buf.length > 5000) { fs.writeSync(out, buf.join('\n') + '\n'); buf = []; }
  });
  process.on('exit', () => { fs.writeSync(out, buf.join('\n') + '\n'); });
}
