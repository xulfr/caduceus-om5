// PRE module: mount the card, then print "STORE id value" for every call of E148 1.1's setting store
// 0x602d19b6 (d0 = setting id, d1 = value; wb.s hooks its entry, which still executes first). Emulator only.
import mount from '../tools/dev/mount.mjs';
export default async function (g) {
  await mount(g);
  const M = g.__M;
  M.setExecTrace((pc) => {
    if (pc !== 0x602d19b6) return;
    const r = M.getRegs();
    console.log(`STORE ${r[0] & 0xffff} ${r[1] | 0}`);
  });
}
