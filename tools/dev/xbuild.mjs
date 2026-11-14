#!/usr/bin/env node
// Pair two expanded main programs (base 0x60021020) instruction by instruction with OM-Emu's cross-build map and list
// every paired instruction whose 32-bit constant differs and lies in 0x80000000..0x9fffffff (peripheral, SRAM and
// uncached-DRAM addresses, and also plain ID numbers in that range: read each one before drawing a conclusion).
//   node tools/dev/xbuild.mjs OM_EMU_DIR A_main.bin B_main.bin OUT.json
// Static analysis only.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const [emu, A, B, OUT] = process.argv.slice(2);
const { buildMap } = await import(pathToFileURL(path.resolve(emu, 'emu/src/fw/xmap.mjs')).href);
const a = new Uint8Array(fs.readFileSync(A)), b = new Uint8Array(fs.readFileSync(B));
const BASE = 0x60021020, hx = (v) => '0x' + (v >>> 0).toString(16);
const seeds = [];   // function starts: a movm after a ret / retf / rets
for (let o = 3; o < a.length - 4; o++)
  if ((a[o - 3] === 0xdf || a[o - 3] === 0xde || (a[o - 2] === 0xf0 && a[o - 1] === 0xfc)) && a[o] === 0xcf) seeds.push(o);
const m = buildMap(a, b, { baseA: BASE, baseB: BASE, seeds });
const u32 = (x, o) => (x[o] | x[o + 1] << 8 | x[o + 2] << 16 | x[o + 3] << 24) >>> 0;
const high = (v) => v >= 0x80000000 && v < 0xa0000000;
const sites = [];
for (let o = 0; o < a.length - 6; o++) {
  const p = m.code[o];
  if (p < 0 || !(a[o] === 0xfc || a[o] === 0xfd) || a[o] !== b[p] || a[o + 1] !== b[p + 1]) continue;
  const va = u32(a, o + 2), vb = u32(b, p + 2);
  if (va !== vb && (high(va) || high(vb))) sites.push({ a: hx(BASE + o), b: hx(BASE + p), a_value: hx(va), b_value: hx(vb) });
}
const out = { function_starts: seeds.length, paired_function_starts: seeds.filter((s) => m.code[s] >= 0).length, stats: m.stats, sites };
fs.writeFileSync(OUT, JSON.stringify(out, null, 1) + '\n');
console.log(`${out.paired_function_starts} of ${seeds.length} function starts paired; ${sites.length} differing high constants`);
