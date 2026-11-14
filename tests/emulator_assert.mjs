import assert from 'node:assert/strict';
import fs from 'node:fs';

export default function(g) {
  const expect = JSON.parse(fs.readFileSync(process.env.OM5_EXPECT, 'utf8'));
  const R = (id, part = 1) => g.__call(0x602f50f8, { d0: id, d1: part }).d0 >>> 0;
  const G = id => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const h = Buffer.from(g.__M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'state allocated after half press');
  const state = Buffer.from(g.__M.dbgRead(0xa1e27d80 - 1 + h, 80));
  assert.equal(state[64], expect.state, 'film load state');
  assert.equal(state[65], expect.count, 'film count');
  assert.equal(state[66], 0, 'no film write in progress');
  assert.equal(state[67], 0, 'title repaint request consumed by the page layout');
  for (let p = 0; p < 3; p++) {
    const base = [916, 924, 972][p], film = expect.slots[p];
    if (!film) { assert.equal(R(base) >>> 16, 0, `slot ${p} untouched`); continue; }
    assert.equal(R(base), (0x464c0000 | film.index << 8) >>> 0, `slot ${p} index`);
    const name = Buffer.alloc(12);
    for (let k = 0; k < 3; k++) name.writeUInt32LE(R(base + 1 + k), k * 4);
    assert.equal(name.toString('ascii').replace(/\0.*$/, ''), film.name);
    for (let k = 0; k < 12; k++) {
      const v = ((film.hue?.[k] ?? 0) & 15) | (((film.light?.[k] ?? 0) & 15) << 4);
      assert.equal(R(928 + 12 * p + k), (0x48310000 | ((v ^ 255) << 8) | v) >>> 0, `slot ${p} H/L ${k}`);
      assert.equal(G(928 + 12 * p + k), film.sat?.[k] ?? 0, `slot ${p} saturation ${k}`);
    }
    for (const [id, key] of [[908 + p, 'contrast'], [904 + p, 'sharpness'], [912 + p, 'shading'],
                            [978 + 3*p, 'shadows'], [977 + 3*p, 'midtones'], [976 + 3*p, 'highlights']])
      assert.equal(G(id), film[key] ?? 0, `slot ${p} ${key}`);
    const addr = g.__call(0x60d52ed5, { d0: 2749 + p }).a0 >>> 0;
    assert.equal(Buffer.from(g.__M.dbgRead(addr, 26)).toString('utf16le').replace(/\0.*$/, ''), film.name);
    if (film.wb) {
      const wb = 904 + 4*p;
      assert.equal(R(wb + 2), (film.wb[0] & 255) | ((film.wb[1] & 255) << 8), `slot ${p} WB shift`);
      assert.equal(R(wb + 3), (R(wb) ^ R(wb + 1) ^ R(wb + 2) ^ 0x57420101) >>> 0, `slot ${p} WB checksum`);
    }
  }
  console.log('ASSERTIONS passed');
}
