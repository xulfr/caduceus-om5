// POST module (tests/run_rgb_row.py): the RGB curves row's cells after the keys. OM5_RGB_EXPECT = JSON
// {cells: {id: [5 offsets] | null (untagged)}, tone: {id: value}, row, ch, st: true (then tests/st_assert.mjs checks
// the delta tables, curves included)}. Emulator only.
import assert from 'node:assert/strict';
import stAssert from './st_assert.mjs';

export default function (g) {
  const M = g.__M;
  const want = JSON.parse(process.env.OM5_RGB_EXPECT || '{}');
  const h = Buffer.from(M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'armed');
  const P = 0xa1e27d80 - 1 + h;
  const wc = id => g.__call(0x602f514d, { d0: id }, [0, 4]).d0 >>> 0;
  const G = id => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const pts = c => ((c >>> 24) & 255) !== 0xc5 ? null : [0, 1, 2, 3, 4].map(j => { const n = (c >>> (4 * j)) & 15; return n >= 8 ? n - 16 : n; });
  const ids = [985, 986, 987, 1030, 1031, 1032, 1002, 1006, 1010];
  const pnl = Buffer.from(M.dbgRead(Buffer.from(M.dbgRead(Buffer.from(M.dbgRead(0x61e588f4, 4)).readUInt32LE() + 4, 4)).readUInt32LE() + 1068, 8));
  const got = { cells: Object.fromEntries(ids.map(i => [i, pts(wc(i))])), tone: Object.fromEntries([976, 977, 978].map(i => [i, G(i)])),
    row: [...pnl].findIndex(b => b === 3 || b === 4), ch: M.dbgRead(P + 1542, 1)[0], tm: M.dbgRead(P + 1178, 1)[0] };
  console.log('RGB ROW ' + JSON.stringify(got));
  for (const [id, v] of Object.entries(want.cells ?? {})) assert.deepEqual(got.cells[id], v, `cell ${id}`);
  for (const [id, v] of Object.entries(want.tone ?? {})) assert.equal((got.tone[id] << 24) >> 24, v, `tone ${id}`);
  if (want.row !== undefined) assert.equal(got.row, want.row, 'focused row');
  if (want.ch !== undefined) assert.equal(got.ch, want.ch, 'channel');
  if (want.st) stAssert(g); else console.log('ASSERTIONS passed');
}
