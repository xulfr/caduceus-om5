import assert from 'node:assert/strict';
import fs from 'node:fs';

export default function(g) {
  const expect = JSON.parse(fs.readFileSync(process.env.OM5_EXPECT, 'utf8'));
  const R = (id, part = 1) => g.__call(0x602f50f8, { d0: id, d1: part }).d0 >>> 0;
  const G = id => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const h = Buffer.from(g.__M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  const guard = g.__layoutGuard;
  assert.ok(guard, 'layout guard installed (PRE tests/layout_guard.mjs)');
  assert.deepEqual(guard.violations, [], 'Picture Mode row descriptor: only the title id may change');
  console.log(`LAYOUT GUARD ${guard.checked} layouts, ${guard.kind4} on the mode strip, no descriptor change`);
  if (expect.state === null) {
    assert.equal(h, 0, 'state handle stays unpublished');
    console.log('ASSERTIONS passed');
    return;
  }
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
    // A look without a WB shift sets 0 / 0 (as LookLab previews it); it never keeps the previous look's.
    const [ab, gm] = film.wb ?? [0, 0];
    const wb = 904 + 4*p;
    assert.equal(R(wb + 2), (ab & 255) | ((gm & 255) << 8), `slot ${p} WB shift record`);
    assert.equal(R(wb + 3), (R(wb) ^ R(wb + 1) ^ R(wb + 2) ^ 0x57420101) >>> 0, `slot ${p} WB checksum`);
    if (G(111) === 54 + p) {
      const mode = [0, 18, 3, 1, 6, 17, 7, 8, 13, 14, 15, 16, 9].indexOf(G(1578));
      assert.notEqual(mode, -1, 'WB mode has shift settings');
      assert.equal(G(1580 + mode), ab, `slot ${p} live A/B`);
      assert.equal(G(1593 + mode), gm, `slot ${p} live G/M`);
    }
  }
  if (expect.case === 'persisted-name') {
    // Simulate a name saved by alpha1-3, then ask each stock label-id family
    // for it. Invalid bytes must never reach the formatted-text renderer.
    const bytes = Buffer.from('@A034@\x1f\x7f\x80ABC', 'latin1');
    const saved = [R(917), R(918), R(919)];
    const write = (id, value) => g.__call(0x602f5121, { d0: id, d1: 1, a0: value });
    try {
      for (let k = 0; k < 3; k++) write(917 + k, bytes.readUInt32LE(4*k));
      for (const id of [2749, 2752, 2859]) {
        const addr = g.__call(0x60d52ed5, { d0: id }).a0 >>> 0;
        assert.equal(Buffer.from(g.__M.dbgRead(addr, 26)).toString('utf16le').replace(/\0.*$/, ''),
                     '?A034????ABC', `literal persisted name for string ${id}`);
      }
      for (let k = 0; k < 3; k++) assert.equal(R(917 + k), bytes.readUInt32LE(4*k), 'display does not rewrite stored names');
    } finally {
      saved.forEach((value, k) => write(917 + k, value));
    }
  }
  console.log('ASSERTIONS passed');
}
