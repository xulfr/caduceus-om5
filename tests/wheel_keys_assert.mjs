// POST module for tests/run_wheel_keys.py: the colour wheel's state after the keys (OM-3 v0.41 key map). Reads the
// axis (P+0), Color Profile 1's cursor 2201 (0 = all colours), its one / all cell 2197, and the 12 colours'
// Saturation (OM's getter), Hue and Lightness (the raw cell's nibbles, as tests/look_defaults_assert.mjs), the tint
// cells 968 / 974 and the focused row (1 the colour wheel, 2 Split toning).
// OM5_WHEEL_EXPECT = JSON {axis, cur, one, sat: {colour: v}, hue: {..}, light: {..}}; colours not named must be 0.
import assert from 'node:assert/strict';

export default function (g) {
  const G = (id) => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const R = (id) => g.__call(0x602f50f8, { d0: id, d1: 1 }).d0 >>> 0;
  const nib = (v, s) => ((v >> s) << 28) >> 28;
  const h = Buffer.from(g.__M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'armed');
  // the focused row: the Picture Mode panel ((0x61e588f4)->+4) keeps a state byte per row at +1068 + index, 3 or 4
  const panel = Buffer.from(g.__M.dbgRead(Buffer.from(g.__M.dbgRead(0x61e588f4, 4)).readUInt32LE(0) + 4, 4)).readUInt32LE(0);
  const rows = [...g.__M.dbgRead(panel + 1068, 7)];
  const got = {
    pm: G(111), row: rows.findIndex((v) => v === 3 || v === 4), axis: g.__M.dbgRead(0xa1e27d80 - 1 + h, 1)[0], cur: G(2201), one: G(2197),
    sat: [...Array(12).keys()].map((k) => G(928 + k)),
    hue: [...Array(12).keys()].map((k) => nib(R(928 + k) & 15, 0)),
    light: [...Array(12).keys()].map((k) => nib(R(928 + k) & 0xf0, 4)),
    tint: [968, 974].map((id) => G(id) & 0xff),
  };
  console.log('WHEEL KEYS ' + JSON.stringify(got));
  const want = JSON.parse(process.env.OM5_WHEEL_EXPECT);
  const twelve = (m) => [...Array(12).keys()].map((k) => (m ?? {})[k] ?? 0);
  assert.equal(got.pm, 54, 'Color Profile 1');
  for (const k of ['row', 'axis', 'cur', 'one']) if (want[k] !== undefined) assert.equal(got[k], want[k], k);
  if (want.satAll !== undefined) assert.deepEqual(got.sat, Array(12).fill(want.satAll), 'saturation, all colours');
  else assert.deepEqual(got.sat, twelve(want.sat), 'saturation');
  assert.deepEqual(got.hue, twelve(want.hue), 'hue');
  assert.deepEqual(got.light, twelve(want.light), 'lightness');
  if (want.tint) assert.deepEqual(got.tint, want.tint, 'Shadow / Highlight tint cells 968 / 974');
  console.log('ASSERTIONS passed');
}
