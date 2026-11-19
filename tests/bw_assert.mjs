// POST module: Blacks / Whites (v0.2.0-dev) on the stock tone-curve modifier 0x60385f08 and the gate wrapper.
// Calls the firmware's own code on a 256-entry ramp in heap memory, with P+1100/1102 (Blacks/Whites) set as
// given. Emulator only: OM-Emu does not develop photos, so this checks the table maths, not a picture.
import assert from 'node:assert/strict';
import fs from 'node:fs';

export default function(g) {
  const M = g.__M;
  const h = Buffer.from(M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'state block allocated (armed)');
  const P = 0xa1e27d80 - 1 + h;
  const alloc = n => g.__call(0x60023818, { d0: n }, [0, 4]).a0 >>> 0;
  const tab = alloc(1024), par = alloc(256), zero = alloc(256);
  M.dbgWrite(zero, new Uint8Array(32));
  const gate = Number(process.env.BW_GATE);
  const curve = (b, w, shadows) => {
    const bw = Buffer.alloc(4); bw.writeInt16LE(b, 0); bw.writeInt16LE(w, 2); M.dbgWrite(P + 1100, new Uint8Array(bw));
    const t = Buffer.alloc(512); for (let i = 0; i < 256; i++) t.writeUInt16LE(Math.round(i * 1023 / 255), 2 * i);
    M.dbgWrite(tab, new Uint8Array(t));
    const p = Buffer.alloc(32); p.writeInt16LE(shadows, 6); M.dbgWrite(par, new Uint8Array(p));
    g.__call(0x60385f08, { a0: tab, a1: par, d0: 0 }, [0xf0, 16]);
    const r = Buffer.from(M.dbgRead(tab, 512));
    const opened = g.__call(gate, { a0: zero }, [0x80, 8]).d0 & 0xff;
    return { lut: Array.from({ length: 256 }, (_, i) => r.readUInt16LE(2 * i)), opened };
  };
  const out = { off: curve(0, 0, 0), off_sh: curve(0, 0, 40), bw: curve(64, 64, 0), bw_sh: curve(64, 64, 40),
                crush: curve(-64, -64, 0) };
  M.dbgWrite(P + 1100, new Uint8Array(4));
  if (process.env.BW_OUT) fs.writeFileSync(process.env.BW_OUT, JSON.stringify(out));
  const pick = k => [0, 32, 64, 128, 192, 240, 255].map(i => out[k].lut[i]);
  for (const k of Object.keys(out)) console.log(`BW ${k} gate=${out[k].opened} ${pick(k).join(' ')}`);
  if (process.env.BW_EXPECT_STOCK) {           // alpha12 / stock build: nothing may change
    assert.deepEqual(out.bw.lut, out.off.lut, 'stock ignores P+1052');
  } else {
    assert.equal(out.off.opened, 0, 'gate stays closed with Blacks = Whites = 0 and no tone value');
    assert.equal(out.bw.opened, 1, 'gate opens for Blacks / Whites');
    assert.equal(out.bw.lut[0], 64, 'Blacks +64 lifts the black end');
    assert.ok(out.bw.lut[255] <= 960 && out.bw.lut[255] >= 955, 'Whites +64 lowers the white end');
    assert.ok(Math.abs(out.bw.lut[128] - out.off.lut[128]) <= 4, 'middle grey stays');
    for (let i = 1; i < 256; i++) assert.ok(out.bw.lut[i] >= out.bw.lut[i - 1], 'monotonic');
    assert.ok(out.bw_sh.lut[64] > out.bw.lut[64], 'Shadows still applies on top');
    assert.equal(out.crush.lut[0], 0, 'negative Blacks clamps at 0');
  }
  console.log('ASSERTIONS passed');
}
