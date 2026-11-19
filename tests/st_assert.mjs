// POST module: Split tone (v0.2.0-dev). Calls the camera's R/G/B curve setter 0x603e6974 (hooked by wb.s
// st_entry) with three ramp tables and a fake job output, with the Split tone amount in P set as given,
// and reads back the table pointers the setter stored (O+0xa24/0xa28/0xa2c) and their values.
// Emulator only: no photo is developed.
import assert from 'node:assert/strict';

export default function(g) {
  const M = g.__M;
  const h = Buffer.from(M.dbgRead(0x6218c2fe, 2)).readUInt16LE();
  assert.notEqual(h, 0, 'armed');
  const P = 0xa1e27d80 - 1 + h;
  const alloc = n => g.__call(0x60023818, { d0: n }, [0, 4]).a0 >>> 0;
  const O = alloc(4096), R = alloc(600), G = alloc(600), B = alloc(600), buf = alloc(1552);
  const ramp = Buffer.alloc(512); for (let i = 0; i < 256; i++) ramp.writeUInt16LE(Math.round(i * 4095 / 255), 2 * i);
  for (const t of [R, G, B]) M.dbgWrite(t, new Uint8Array(ramp));
  const u32 = a => Buffer.from(M.dbgRead(a, 4)).readUInt32LE();
  const tab = a => { const b = Buffer.from(M.dbgRead(a, 512)); return Array.from({ length: 256 }, (_, i) => b.readUInt16LE(2 * i)); };
  const run = A => {
    const p = Buffer.alloc(8); p.writeInt16LE(A, 0); p.writeUInt32LE(buf, 4); M.dbgWrite(P + 1128, new Uint8Array(p));
    M.dbgWrite(O, new Uint8Array(4096));
    g.__call(0x603e6974, { a0: O, a1: R, d0: G, d1: B }, [0xa0, 8]);
    const ptr = [u32(O + 0xa24), u32(O + 0xa28), u32(O + 0xa2c)];
    return { ptr, r: tab(ptr[0]), g: tab(ptr[1]), b: tab(ptr[2]) };
  };
  let off, on, neg;
  try { off = run(0); on = run(180); neg = run(-120); } catch (e) { console.log('ST error ' + String(e).slice(0, 600)); throw e; }
  M.dbgWrite(P + 1128, new Uint8Array(8));
  const at = (x, i) => [x.r[i], x.g[i], x.b[i]];
  console.log('ST off ptr ' + off.ptr.map(v => v.toString(16)) + ' on ptr ' + on.ptr.map(v => v.toString(16)));
  for (const i of [0, 32, 64, 128, 192, 224, 255]) console.log(`ST i=${i} off=${at(off, i)} on=${at(on, i)} neg=${at(neg, i)}`);
  assert.deepEqual(off.ptr, [R, G, B], 'A = 0: the stock tables pass through');
  assert.deepEqual(on.ptr, [buf, G, buf + 1024], 'A != 0: tinted R and B, G passes through');
  assert.deepEqual(on.g, off.g, 'green unchanged');
  assert.equal(Buffer.from(M.dbgRead(0x6218c2fe, 2)).readUInt16LE(), h, 'state handle intact');
  assert.ok(Math.abs(on.r[128] - off.r[128]) <= 1 && Math.abs(on.b[128] - off.b[128]) <= 1, 'middle unchanged');
  assert.ok(on.r[224] > off.r[224] && on.b[224] < off.b[224], 'highlights warmer (R up, B down)');
  assert.ok(on.r[32] < off.r[32] && on.b[32] > off.b[32], 'shadows cooler (R down, B up)');
  assert.ok(neg.r[224] < off.r[224] && neg.b[32] < off.b[32], 'negative amount reverses');
  assert.ok(on.r.every(v => v >= 0 && v <= 4095) && on.b.every(v => v >= 0 && v <= 4095), 'clamped 0..4095');
  console.log('ASSERTIONS passed');
}
