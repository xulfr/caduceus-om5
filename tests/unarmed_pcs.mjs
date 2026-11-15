// PRE: mount the card; record every executed PC inside the project's code ranges (written to PCS at exit).
import fs from 'node:fs';
export default async function (g) {
  g.__M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  const R = [[0x605af4b0, 0x605af800], [0x60845a00, 0x60846000], [0x60ca7b00, 0x60ca8000], [0x612a4b98, 0x612a5000], [0x613f2b80, 0x613f3000], [0x6169c820, 0x6169d000]];
  const seen = new Map();
  g.__M.setExecTrace((pc) => { pc >>>= 0; for (const [a, b] of R) if (pc >= a && pc < b) { seen.set(pc, (seen.get(pc) ?? 0) + 1); break; } });
  process.on('exit', () => fs.writeFileSync(process.env.PCS, [...seen].sort((x, y) => x[0] - y[0]).map(([p, n]) => p.toString(16) + ' ' + n).join('\n') + '\n'));
}
