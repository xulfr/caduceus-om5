// POST module: Split tone (v0.2.0-dev). After the GUI has set tints on the colour wheel, checks the delta tables the
// refresh built in P against the documented formula (from the tint cells) and calls the camera's R/G/B curve setter
// 0x603e6974 (hooked by wb.s st_entry / st_tint) with three ramp tables and a fake job output: the stored table
// pointers (O+0xa24/0xa28/0xa2c) and values must be the ramps plus the delta at each value's output level
// (value >> 4: the curve tables are indexed by linear input, so zones go by output level since 2026-11-20), clamped to
// 0..4095. With ST_A cleared
// the stock tables must pass through. Black / White (P+1172 / 1174) add -(X * u) >> 5 to every channel, X = Blacks
// below the middle and Whites from it up (hsl.s tn_tables). Emulator only: no photo is developed.
// OM5_ST_EXPECT (JSON, optional): {"cells": {"968": 48, ...}} cell values the GUI should have produced.
import assert from 'node:assert/strict';

const ST_A = 1176, ST_BUF = 1180;
const TINT_IDS = [968, 969, 970, 971, 972, 973, 974, 975, 964];   // 3 z + p: shadows, midtones, highlights
const RGB = Array.from({ length: 12 }, (_, k) => [0, 1, 2].map(c => Math.round(64 * Math.cos((60 - 30 * k - 120 * c) * Math.PI / 180))));

// R / G / B curves (phase 4, card block rgb.s): working cells RGB_IDS[3p + c], 0xC5 << 24 | five 4-bit offsets; the
// delta entry k gains D(16 k) of the OM-3 model (tests/rgb_curves.py, checked there against the OM-3's own).
const tdiv = (a, b) => Math.trunc(a / b);
const RGB_IDS = [985, 986, 987, 1030, 1031, 1032, 1002, 1006, 1010];
function curve(cell) {
  if (((cell >>> 24) & 255) !== 0xc5) return null;
  const v = [0, 1, 2, 3, 4].map(j => { const n = (cell >>> (4 * j)) & 15; return Math.max(-7, n >= 8 ? n - 16 : n); });
  if (!v.some(x => x)) return null;
  const Y = v.map(x => 48 * x), d = [0, 1, 2, 3].map(i => 4 * (Y[i + 1] - Y[i]));
  const m = [d[0], 0, 0, 0, d[3]];
  for (let i = 1; i < 4; i++) { const a = d[i - 1], b = d[i]; m[i] = !a || !b || (a < 0) !== (b < 0) ? 0 : tdiv(2 * a * b, a + b); }
  return Array.from({ length: 256 }, (_, k) => { const i = k >> 6, s = 64 * (k & 63), s2 = (s * s) >> 12, s3 = (s2 * s) >> 12;
    return ((2 * s3 - 3 * s2 + 4096) * Y[i] + (s3 - 2 * s2 + s) * (m[i] >> 2) + (3 * s2 - 2 * s3) * Y[i + 1] + (s3 - s2) * (m[i + 1] >> 2)) >> 12; });
}

export default function (g) {
  const M = g.__M;
  const h = Buffer.from(M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'armed');
  const P = 0xa1e27d80 - 1 + h;
  const get = id => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const want = process.env.OM5_ST_EXPECT ? JSON.parse(process.env.OM5_ST_EXPECT) : {};
  for (const [id, v] of Object.entries(want.cells ?? {})) assert.equal(get(Number(id)) & 0xff, v, `cell ${id}`);
  const p = get(111) - 54;
  assert.ok(p >= 0 && p < 3, 'a Color Profile is selected');
  const T = [0, 1, 2].map(z => { const v = get(TINT_IDS[3 * z + p]) & 0xff, k = v & 15, s = v >> 4;
    return k < 12 && s < 11 ? RGB[k].map(x => Math.floor(s * x / 2)) : [0, 0, 0]; });   // strength 0..10, half steps
  const bw = Buffer.from(M.dbgRead(P + 1172, 4)), BB = bw.readInt16LE(0), WW = bw.readInt16LE(2);   // Blacks, Whites
  const wc = id => g.__call(0x602f514d, { d0: id }, [0, 4]).d0 >>> 0;
  const cv = [0, 1, 2].map(c => curve(wc(RGB_IDS[3 * p + c])));
  const any = T.some(t => t.some(x => x)) || BB !== 0 || WW !== 0 || cv.some(x => x);
  const pb = Buffer.from(M.dbgRead(P + ST_A, 8));
  assert.equal(pb.readInt16LE(0), any ? 1 : 0, 'ST_A follows the tints and Black / White');
  if (!any) { console.log('ST no tint'); console.log('ASSERTIONS passed'); return; }
  const buf = pb.readUInt32LE(4);
  assert.notEqual(buf, 0, 'buffer allocated');
  // Tone Balance b (907 + 4p, -5..+5): the tint weights' u from the hand-over point c = 128 - 16b, scaled to +-128 on
  // each side (division truncates, as the CPU's div); Black / White keep u = i - 128.
  const bal = Math.max(-5, Math.min(5, (get(907 + 4 * p) << 24) >> 24)), cc = 128 - 16 * bal;
  const ut = i => !bal ? i - 128 : i < cc ? Math.trunc((i - cc) * 128 / cc) : Math.trunc((i - cc) * 128 / (256 - cc));
  const exp = [0, 1, 2].map(c => Array.from({ length: 256 }, (_, i) => { const u = i - 128, v = ut(i), w = v * v, e = v < 0 ? 0 : 2;
    return ((w * T[e][c] + (16384 - w) * T[1][c]) >> 14) - (((u < 0 ? BB : WW) * u) >> 5) + (cv[c] ? cv[c][i] : 0); }));
  const db = Buffer.from(M.dbgRead(buf + 1552, 1536));
  for (let c = 0; c < 3; c++) for (let i = 0; i < 256; i++) assert.equal(db.readInt16LE(512 * c + 2 * i), exp[c][i], `delta c${c} i${i}`);
  const alloc = n => g.__call(0x60023818, { d0: n }, [0, 4]).a0 >>> 0;
  const O = alloc(4096), R = alloc(600), G = alloc(600), B = alloc(600);
  const ramp = Buffer.alloc(512); for (let i = 0; i < 256; i++) ramp.writeUInt16LE(Math.round(i * 4095 / 255), 2 * i);
  for (const t of [R, G, B]) M.dbgWrite(t, new Uint8Array(ramp));
  const u32 = a => Buffer.from(M.dbgRead(a, 4)).readUInt32LE();
  const tab = a => { const b = Buffer.from(M.dbgRead(a, 512)); return Array.from({ length: 256 }, (_, i) => b.readUInt16LE(2 * i)); };
  const run = () => { M.dbgWrite(O, new Uint8Array(4096)); g.__call(0x603e6974, { a0: O, a1: R, d0: G, d1: B }, [0xa0, 8]);
    const ptr = [u32(O + 0xa24), u32(O + 0xa28), u32(O + 0xa2c)]; return { ptr, t: ptr.map(tab) }; };
  const ready = 0xa26e2694, saved = M.dbgRead(ready, 4).slice();
  try {
    // The caller in section 2 is available, the tint body in section 4 is not.
    M.dbgWrite(ready, Uint8Array.of(3, 0, 0, 0));
    assert.deepEqual(run().ptr, [R, G, B], 'partial load: keep the stock curves even with a valid P');
  } finally {
    M.dbgWrite(ready, saved);
  }
  const on = run();
  const sa = Buffer.alloc(2); M.dbgWrite(P + ST_A, new Uint8Array(sa));
  const off = run();
  sa.writeInt16LE(1); M.dbgWrite(P + ST_A, new Uint8Array(sa));
  assert.deepEqual(off.ptr, [R, G, B], 'no tint: the stock tables pass through');
  assert.deepEqual(on.ptr, [buf, buf + 512, buf + 1024], 'tint: the buffer tables');
  for (let c = 0; c < 3; c++) for (let i = 0; i < 256; i++)
    assert.equal(on.t[c][i], Math.min(4095, Math.max(0, off.t[c][i] + exp[c][off.t[c][i] >> 4])), `out c${c} i${i}`);
  assert.equal(Buffer.from(M.dbgRead(0x6218c2fe, 2)).readUInt16LE(), h, 'state handle intact');
  console.log('ST T ' + JSON.stringify(T) + ' curves ' + JSON.stringify(cv.map(x => x && [x[0], x[64], x[128], x[192], x[255]])));
  for (const i of [0, 32, 64, 128, 192, 224, 255]) console.log(`ST i=${i} off=${off.t.map(t => t[i])} on=${on.t.map(t => t[i])}`);
  console.log('ASSERTIONS passed');
}
