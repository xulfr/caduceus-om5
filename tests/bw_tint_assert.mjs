// POST module: Black / White on the tone page and split tone on the colour wheel (v0.2.0-dev). Reads Blacks 965 / 966
// / 967, Whites 993 / 997 / 1020, the tone values 976..984, the tint cells and OM's tone mode 2189 through OM's getter,
// and P's Black / White curve values (P+1172 / 1174), split-tone flag (P+1176) and tone-page state (P+1178).
// OM5_BW_EXPECT = JSON {pm, bw: [6], p: [B, W], tm, tone3: [3], tint: {id: value}, stFlag, st: true}. With st, tests/st_assert.mjs
// then checks the delta tables and the curve setter. Emulator only: no photo is developed.
import assert from 'node:assert/strict';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export default async function (g) {
  const G = id => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const h = Buffer.from(g.__M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'armed');
  const b = Buffer.from(g.__M.dbgRead(0xa1e27d80 - 1 + h + 1172, 8));
  const tintIds = [968, 969, 970, 971, 972, 973, 974, 975, 964];
  const got = { axis: g.__M.dbgRead(0xa1e27d80 - 1 + h, 1)[0], pm: G(111), bw: [965, 966, 967, 993, 997, 1020].map(G), p: [b.readInt16LE(0), b.readInt16LE(2)],
    st: b.readInt16LE(4), tm: b[6], mode: G(2189), tone: Array.from({ length: 9 }, (_, i) => G(976 + i)),
    tint: Object.fromEntries(tintIds.map(id => [id, G(id) & 0xff])), grain: [907, 911, 915].map(G) };
  console.log('BW TINT ' + JSON.stringify(got));
  const want = JSON.parse(process.env.OM5_BW_EXPECT || '{}');
  if (want.axis !== undefined) assert.equal(got.axis, want.axis, 'colour wheel axis');
  if (want.pm !== undefined) assert.equal(got.pm, want.pm, 'picture mode');
  if (want.bw) assert.deepEqual(got.bw, want.bw, 'Blacks / Whites settings');
  if (want.p) assert.deepEqual(got.p, want.p, 'curve values in P');
  if (want.tm !== undefined) assert.equal(got.tm, want.tm, 'tone page Black/White state');
  if (want.tone3) assert.deepEqual(got.tone.slice(0, 3), want.tone3, 'Color Profile 1 tone values 976..978');
  for (const [id, v] of Object.entries(want.tint ?? {})) assert.equal(got.tint[id], v, `tint cell ${id}`);
  if (want.stFlag !== undefined) assert.equal(got.st, want.stFlag, 'split-tone flag in P');
  const here = path.dirname(new URL(import.meta.url).pathname);
  if (want.st) await (await import(pathToFileURL(path.resolve(here, 'st_assert.mjs')).href)).default(g);
  else if (want.gs) await (await import(pathToFileURL(path.resolve(here, 'gs_assert.mjs')).href)).default(g);
  else console.log('ASSERTIONS passed');
}
