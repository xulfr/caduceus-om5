// POST module: Color Profile grain (v0.2.0). Reads the grain cells 907 / 911 / 915 (value, part 0, through
// OM's getter), their part-1 WB record words, and effective 998 (store 2, context 0) through the refresh getter.
// OM5_GRAIN_EXPECT = JSON {"cells": [g1, g2, g3], "effective": e}; omitted keys are only printed.
// Emulator only: OM-Emu has no image pipeline, so this does not show grain reaching a photo.
import assert from 'node:assert/strict';

export default function(g) {
  const G = id => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const R = (id, part = 1) => g.__call(0x602f50f8, { d0: id, d1: part }).d0 >>> 0;
  const RG = (id, ctx, st) => g.__call(0x602d2fc2, { a0: id, d0: ctx, d1: st }, [0x80, 8]).d0 | 0;
  const cells = [907, 911, 915].map(G);
  const wb = [907, 911, 915].map(id => R(id).toString(16));
  const got = { pm: G(111), cells, effective: RG(998, 0, 2), mono: [999, 1000, 1001].map(G), wb_part1: wb };
  console.log('CP GRAIN ' + JSON.stringify(got));
  const want = process.env.OM5_GRAIN_EXPECT ? JSON.parse(process.env.OM5_GRAIN_EXPECT) : {};
  if (want.cells) assert.deepEqual(cells, want.cells, 'Color Profile grain cells 907/911/915');
  if (want.effective !== undefined) assert.equal(got.effective, want.effective, 'effective grain 998');
  if (want.mono) assert.deepEqual(got.mono, want.mono, 'Monochrome grain 999..1001 unchanged');
  console.log('ASSERTIONS passed');
}
