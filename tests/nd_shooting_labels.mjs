// Use as both PRE and POST with ND_STEP=4, 5 or 6 and keys 'ok ok ok'.
// Inject the display-side setting reads. OM-Emu does not run the exposure pipeline.
import assert from 'node:assert/strict';

export default function (g) {
  const step = Number(process.env.ND_STEP);
  const liveView = process.env.ND_LV !== '0';
  const prefixId = new Map([[4, 0x2060], [5, 0x2062], [6, 0x205d]]).get(step);
  assert.ok(prefixId, 'set ND_STEP to 4, 5 or 6');
  const { __lab: lab, __M: memory } = g;
  if (!g.__ndLabelReads) {
    const reads = new Set();
    g.__ndLabelReads = reads;
    lab.hook_rt(0x60d5a294, (hle, r) => {
      if (r.d0 < 1709 || r.d0 > 1711) {
        hle.sim.packet('s');
        return;
      }
      reads.add(r.d0);
      const value = Buffer.alloc(4);
      value.writeUInt32LE(r.d0 === 1710 ? step : r.d0 === 1711 ? Number(liveView) : 1);
      memory.dbgWrite(r.a0, value);
      hle.finish(r, { d0: 0 });
    }, 'inject-live-nd-display-settings');
    return;
  }

  assert.deepEqual([...g.__ndLabelReads].sort(), [1709, 1710, 1711]);
  assert.equal(lab.state(), 0x108, 'finish on the shooting screen');
  const bitmapBody = id => Buffer.from(memory.dbgRead(0xa3435ccc + 4 * id, 4)).readUInt32LE() + 24;
  const draws = lab.draw_log.filter(d => d.op === 'bitmap' && d.y === 39);
  assert.ok(draws.some(d => d.data === bitmapBody(prefixId) && d.x + d.width === 98),
    'draw the selected ND prefix ending at the suffix');
  assert.equal(draws.some(d => d.data === bitmapBody(0x2061) && d.x === 98), liveView,
    'draw -LV only when live view is enabled');
  console.log(`Live ND label passed for step ${step} with LV ${liveView ? 'on' : 'off'}`);
}
