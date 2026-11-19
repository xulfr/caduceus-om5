// POST module: colour grain probe cg1 (firmware/om5ii/cg.s), after cp_grain_assert.mjs.
// Calls cg_level and the request hook cg_sel natively on a fake development request and context in heap memory
// (stock malloc), as request configuration 0x6036fc58 would (`call cg_sel,[d2,a2],12`, a0 = context), then reads
// what the hook left. OM5_CG = JSON {"level": L, "sel": ADDR, "lvl": ADDR}: L is the grain level the active Color
// Profile should give (0 = none). Emulator only: OM-Emu has no image pipeline, so this checks the request edits, not
// grain in a photo.
import assert from 'node:assert/strict';
import cpGrain from './cp_grain_assert.mjs';

const REQ = 2048, CTX = 64;

export default function(g) {
  cpGrain(g);
  const cfg = JSON.parse(process.env.OM5_CG ?? '{}');
  if (cfg.sel === undefined) return;
  const M = g.__M;
  const level = g.__call(cfg.lvl, {}, [0, 4]).d0 >>> 0;
  const malloc = n => g.__call(0x60023818, { d0: n }, [0, 4]).a0 >>> 0;
  const req = malloc(REQ), ctx = malloc(CTX);
  assert.ok(req && ctx, 'malloc for the fake request');
  const u8 = (a, o, v) => M.dbgWrite(a + o, new Uint8Array([v & 0xff]));
  const u16 = (a, o, v) => M.dbgWrite(a + o, new Uint8Array([v & 0xff, (v >> 8) & 0xff]));
  const u32 = (a, o, v) => M.dbgWrite(a + o, new Uint8Array([v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff, (v >>> 24) & 0xff]));
  const r8 = (a, o) => M.dbgRead(a + o, 1)[0];
  const r32 = (a, o) => Buffer.from(M.dbgRead(a + o, 4)).readUInt32LE();
  // One request per case: COLOR still development by default, then one field changed.
  const run = (name, tweak) => {
    M.dbgWrite(req, new Uint8Array(REQ)); M.dbgWrite(ctx, new Uint8Array(CTX));
    u8(req, 16, 0); u16(req, 14, 0x1000); u8(req, 10, 11); u16(req, 12, 0); u16(req, 1838, 0);
    u32(ctx, 4, req); u32(ctx, 52, 11);
    tweak?.();
    const before = { key: r8(req, 10), ctx: r32(ctx, 52) };
    const r = g.__call(cfg.sel, { a0: ctx }, [0xa0, 12]);
    const out = { name, combiner: r.d0 >>> 0, grain: r8(req, 1828), key: r8(req, 10), ctx: r32(ctx, 52), before };
    console.log('CG ' + JSON.stringify(out));
    return out;
  };
  const marked = (o, lvl) => o.grain === lvl && o.key === 12 && o.ctx === 12;
  const stock = o => o.grain === 0 && o.key === o.before.key && o.ctx === o.before.ctx;
  console.log('CG level ' + level);
  assert.equal(level, cfg.level, 'cg_level: grain level of the active Color Profile');
  const still = run('color-still');
  if (cfg.level) assert.ok(marked(still, cfg.level), 'COLOR still development gets grain, key 12, context 12');
  else assert.ok(stock(still), 'no grain set: the request stays stock');
  // Requests the probe must never touch, whatever the grain setting.
  assert.ok(stock(run('live-view', () => u16(req, 14, 0x0130))), 'live-view request (+14 0x0130) untouched');
  assert.ok(stock(run('kind-3', () => u8(req, 16, 3))), 'kind-3 request untouched');
  assert.ok(stock(run('mono-key', () => { u8(req, 10, 12); u32(ctx, 52, 12); })), 'MONO request untouched');
  assert.ok(stock(run('own-effect', () => u16(req, 1838, 0x0c00))), 'request with its own effect (Shading 0x0c00) untouched');
  console.log('CG ASSERTIONS passed');
}
