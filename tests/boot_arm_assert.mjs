// POST module for tests/run_boot_arm.py. OM5_BOOT_EXPECT = JSON {armed, pend, films, count, slot0}:
//   armed  the state block P is allocated; pend  P+16, the start-up refresh still pending (boot.s ST_PEND)
//   films  P+64 (films.s FL_STATE: 0 not tried, 1 loaded, 2 no / bad file); count  P+65
//   slot0  Color Profile 1's look index (from its name cells), or null for none
import assert from 'node:assert/strict';

export default function (g) {
  const want = JSON.parse(process.env.OM5_BOOT_EXPECT);
  const h = Buffer.from(g.__M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  const R = (id) => g.__call(0x602f50f8, { d0: id, d1: 1 }).d0 >>> 0;
  const got = { armed: h !== 0, pend: null, films: null, count: null, slot0: null };
  if (h) {
    const P = Buffer.from(g.__M.dbgRead(0xa1e27d80 - 1 + h, 80));
    got.pend = P[16]; got.films = P[64]; got.count = P[65];
    const tag = R(916);
    got.slot0 = (tag >>> 16) === 0x464c ? (tag >>> 8) & 255 : null;
  }
  console.log('BOOT ARM ' + JSON.stringify(got));
  for (const k of Object.keys(want)) assert.deepEqual(got[k], want[k], k);
  console.log('ASSERTIONS passed');
}
