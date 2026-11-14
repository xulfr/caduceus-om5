export default async function (g) {
  const out = [];
  for (let id = 0; id < 7000; id++) {
    let a0; try { a0 = g.__call(0x60d52ed5, { d0: id }, [0x80, 8]).a0 >>> 0; } catch (e) { continue; }
    if (!a0) continue;
    let b; try { b = Buffer.from(g.__M.dbgRead(a0, 48)); } catch (e) { continue; }
    let s = ''; for (let i = 0; i < 48; i += 2) { const c = b.readUInt16LE(i); if (!c) break; s += String.fromCharCode(c); }
    if (/Color Profile|Monochrome Profile|^Picture Mode$|^Color Creator$/.test(s)) out.push(id + ':' + s + '@' + a0.toString(16));
  }
  console.log(out.join(' | '));
}
