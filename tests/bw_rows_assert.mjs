// POST module: Blacks / Whites rows (v0.2.0-dev). Reads the six settings (Blacks 965 / 966 / 967, Whites
// 993 / 997 / 1020) through OM's getter and the curve values the refresh put in P+1100 / P+1102.
// OM5_BW_EXPECT = JSON {"set": [6 values], "p": [B, W]}. Emulator only: no photo is developed.
import assert from 'node:assert/strict';

export default function(g) {
  const G = id => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const h = Buffer.from(g.__M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'armed');
  const b = Buffer.from(g.__M.dbgRead(0xa1e27d80 - 1 + h + 1100, 4));
  const got = { pm: G(111), set: [965, 966, 967, 993, 997, 1020].map(G), p: [b.readInt16LE(0), b.readInt16LE(2)],
                grain: [907, 911, 915].map(G) };
  console.log('BW ROWS ' + JSON.stringify(got));
  const want = JSON.parse(process.env.OM5_BW_EXPECT || '{}');
  if (want.set) assert.deepEqual(got.set, want.set, 'Blacks / Whites settings');
  if (want.p) assert.deepEqual(got.p, want.p, 'curve values in P');
  if (want.pm !== undefined) assert.equal(got.pm, want.pm, 'picture mode');
  console.log('ASSERTIONS passed');
}
