// POST module: gs_hook (the gamma stage's cache test at 0x603e6a3b, Black / White and tints in live view). Runs the
// hook's code directly from gs_entry with a fake cache record pointer in d3 and checks which exit it takes:
// 0x603e6aa3 (the stock cache-miss path, the curve setter runs) or 0x603e6a41 (stock: the cache test goes on).
// Expected: a cache that has not seen P's GS_GEN misses once, then follows the stock test; d3 = 0 misses (stock);
// unarmed is stock. Also checks that the session's Black / White changes raised GS_GEN. Emulator only: OM-Emu runs
// no live-view development, so this checks the hook's logic, not the picture.
import assert from 'node:assert/strict';
export default async function (g) {
  const M = g.__M, sim = g.__lab.sim;
  const u32 = a => Buffer.from(M.dbgRead(a, 4)).readUInt32LE();
  const w32 = (a, v) => { const b = Buffer.alloc(4); b.writeUInt32LE(v >>> 0); M.dbgWrite(a, new Uint8Array(b)); };
  const h = Buffer.from(M.dbgRead(0xa218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'armed');
  const P = 0xa1e27d80 - 1 + h, GEN = P + 1504, TAB = P + 1508;
  const gen0 = u32(GEN);
  console.log('GS_GEN after the session', gen0);
  if (process.env.OM5_GS_MIN) assert.ok(gen0 >= Number(process.env.OM5_GS_MIN), 'Black / White changes raise GS_GEN');
  const ENTRY = Number(process.env.OM5_GS_ENTRY), MISS = 0x603e6aa3, GO = 0x603e6a41;
  const SP = 0xa1f00000;                                    // scratch stack in uncached RAM
  w32(SP + 56, 0x600d0001);                                 // the stage's (56,sp): a0 at GO
  const run = (d3) => {
    sim.reset({ pc: ENTRY, sp: SP, d3, d2: 1 });
    const r = sim.run([MISS, GO].sort((a, b) => a - b), false, null, []);
    assert.equal(r.fault, 0, 'no fault');
    assert.equal(r.d2, 1, 'd2 kept'); assert.equal(r.d3 >>> 0, d3 >>> 0, 'd3 kept'); assert.equal(r.sp >>> 0, SP, 'sp kept');
    if (r.pc === GO) assert.equal(r.a0 >>> 0, 0x600d0001, 'a0 = (56,sp) at the stock test');
    return r.pc === MISS ? 'miss' : r.pc === GO ? 'go' : `pc ${r.pc.toString(16)}`;
  };
  for (let k = 0; k < 4; k++) { w32(TAB + 8 * k, 0); w32(TAB + 8 * k + 4, 0); }
  const C1 = 0x62345670, C2 = 0x62345680;
  const got = [];
  got.push(['d3 0', run(0)]);
  got.push(['new cache', run(C1)]);
  got.push(['same gen', run(C1)]);
  w32(GEN, gen0 + 1);
  got.push(['gen +1', run(C1)]);
  got.push(['gen seen', run(C1)]);
  got.push(['second cache', run(C2)]);
  got.push(['first still seen', run(C1)]);
  for (const c of [0x62345690, 0x623456a0, 0x623456b0]) run(c);  // fill the table, then one more reuses the last entry
  got.push(['table full, C2 seen', run(C2)]);
  M.dbgWrite(0xa218c2fe, new Uint8Array([0, 0]));
  w32(GEN, gen0 + 2);
  got.push(['unarmed', run(C1)]);
  M.dbgWrite(0xa218c2fe, new Uint8Array([h & 255, h >> 8]));
  console.log('GS ' + JSON.stringify(got));
  assert.deepEqual(got.map(x => x[1]), ['miss', 'miss', 'go', 'miss', 'go', 'miss', 'go', 'go', 'go']);
  console.log('ASSERTIONS passed');
}
