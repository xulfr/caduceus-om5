// PRE: mount the card; record every executed PC inside the project's code ranges (written to PCS at exit).
import fs from 'node:fs';
const spec = JSON.parse(fs.readFileSync(new URL('../firmware/om5ii/patch.json', import.meta.url)));
const lateCode = spec.ranges
  .filter(r => r.component === '0x100' && (+r.address >= 0x61343800 || (+r.address >= 0x605ce800 && +r.address < 0x60829800)))
  .map(r => [+r.address, +r.address + r.bytes]);
export default async function (g) {
  g.__M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  const extensions = [
    [0x605af4b0, 0x605af800], [0x60845a00, 0x60846000],
    [0x60ca7b00, 0x60ca8000], [0x612a4b98, 0x612a5000], ...lateCode,
  ];
  const seen = new Map();
  g.__M.setExecTrace((pc) => { pc >>>= 0; for (const [a, b] of extensions) if (pc >= a && pc < b) { seen.set(pc, (seen.get(pc) ?? 0) + 1); break; } });
  process.on('exit', () => fs.writeFileSync(process.env.PCS, [...seen].sort((x, y) => x[0] - y[0]).map(([p, n]) => p.toString(16) + ' ' + n).join('\n') + '\n'));
}
