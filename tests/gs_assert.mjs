// POST module: gs_hook (the gamma stage's cache test at 0x603e6a3b, Black / White and tints in live view). Runs the
// hook's code from the patched stock instruction with a fake cache record pointer in d3 and checks which exit it takes:
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
  const ENTRY = 0x603e6a3b, MISS = 0x603e6aa3, GO = 0x603e6a41;
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
  const ready = 0xa26e2694, handle = 0xa218c2fe;
  const savedReady = u32(ready), savedHandle = M.dbgRead(handle, 2).slice();
  const table = () => Buffer.from(M.dbgRead(TAB, 32));
  const snapshot = table();
  let gateSteps = 0, escaped;
  M.setExecTrace(pc => {
    gateSteps++;
    if (pc < 0x6029f800 || pc >= 0x605af800) escaped ??= pc;
  });
  try {
    // Even a published, valid P must be ignored before all loader bits are set.
    for (let mask = 0; mask < 1023; mask++) {
      w32(ready, mask);
      assert.equal(run(C2 + 256), 'go', `incomplete loader mask ${mask}`);
    }
    assert.deepEqual(table(), snapshot, 'partial startup left the table untouched');
    w32(ready, savedReady);
    for (const invalid of [0, 2, 42242, 65535]) {
      M.dbgWrite(handle, Uint8Array.of(invalid & 255, invalid >> 8));
      assert.equal(run(C2 + 256), 'go', `invalid state handle ${invalid}`);
    }
    assert.deepEqual(table(), snapshot);
    assert.ok(gateSteps > 0, 'traced the startup path');
    assert.equal(escaped, undefined, 'startup stayed inside native section 2');
  } finally {
    M.setExecTrace(null);
    M.dbgWrite(handle, savedHandle);
    w32(ready, savedReady);
  }
  console.log('GS ' + JSON.stringify(got));
  assert.deepEqual(got.map(x => x[1]), ['miss', 'miss', 'go', 'miss', 'go', 'miss', 'go', 'go']);
  console.log('ASSERTIONS passed');
}
