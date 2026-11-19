// POST for a session without key presses. Bounded fault injection in the
// actual E148 arming code; this does not emulate the physical boot loader.
import assert from 'node:assert/strict';

export default function(g) {
  const lab = g.__lab, M = g.__M;
  const read = (a, n) => Buffer.from(M.dbgRead(a, n));
  const word = (a, v) => { const b = Buffer.alloc(4); b.writeUInt32LE(v >>> 0); M.dbgWrite(a, b); };
  const half = (a, v) => { const b = Buffer.alloc(2); b.writeUInt16LE(v); M.dbgWrite(a, b); };
  const handle = 0x6218c2fe, tid = 0x6218c2fc, ready = 0xa26e2694;
  const malloc = 0x60023818, getTid = 0x600317b4;
  const SIZE = 1136;   // hsl.s ST_SIZE (1024 before the Shading descriptors' nodes, 1040 before CP grain's, 1064 / 1104 before Blacks/Whites / Split tone)
  const saved = [read(handle, 2), read(tid, 2), read(ready, 4)];
  const trig = 0x602f0cc2, resume = 0x602f0b9a, armGate = 0x613f2d93;
  const hooks = new Map([malloc, getTid, trig, resume, armGate].map(pc => [pc, lab.hooks.get(pc)]));
  let allocations = 0, taskCalls = 0, taskResult = 0, taskId = 1, allocation = 0;
  let owned = 0;
  const gate = () => g.__call(armGate, {}, [0xf0, 36]);
  try {
    half(handle, 0); half(tid, 1);
    lab.hook_rt(getTid, (h, r) => { taskCalls++; half(r.a0, taskId); h.finish(r, { d0: taskResult }); }, 'audit-get-tid');
    lab.hook_rt(malloc, (h, r) => {
      allocations++; assert.equal(r.d0, SIZE); h.finish(r, { a0: allocation });
    }, 'audit-allocation');
    // Run the native hook and inject a half-press in the stock trigger frame.
    lab.hook_rt(trig, (h, r) => { word(r.sp + 36 + 16, 0x02000100); h.finish(r); }, 'audit-trigger');
    lab.hook_rt(resume, (h, r) => h.return_here(r, [0xf0, 36]), 'audit-trigger-resume');
    lab.hook_rt(armGate, () => assert.fail('incomplete mask reached section 8'), 'audit-forbidden-arm');
    for (let mask = 0; mask < 1023; mask++) {
      word(ready, mask);
      g.__call(0x602f0b95, {}, [0xf0, 36]);
    }
    word(ready, 1023);
    let reached = false;
    lab.hook_rt(armGate, (h, r) => { reached = true; h.finish(r); }, 'audit-allowed-arm');
    g.__call(0x602f0b95, {}, [0xf0, 36]);
    assert.equal(reached, true, 'the injected half-press reaches section 8 with the complete mask');
    if (hooks.get(armGate)) lab.hooks.set(armGate, hooks.get(armGate)); else lab.hooks.delete(armGate);
    assert.equal(taskCalls, 0, 'all incomplete section masks return before OS calls');
    assert.equal(allocations, 0);
    for (const [stored, actual, result] of [[0, 1, 0], [0x8001, 1, 0], [1, 2, 0], [1, 1, 1]]) {
      half(tid, stored); taskId = actual; taskResult = result; gate();
    }
    assert.equal(allocations, 0, 'wrong task and failed task query never allocate');
    half(tid, 1); taskId = 1; taskResult = 0;
    gate(); gate();
    assert.equal(allocations, 2, 'null allocation can be retried');
    assert.equal(read(handle, 2).readUInt16LE(), 0, 'null allocation stays unarmed');
    // Obtain a genuine pool block, then return it from the controlled allocator.
    if (hooks.get(malloc)) lab.hooks.set(malloc, hooks.get(malloc)); else lab.hooks.delete(malloc);
    owned = g.__call(malloc, { d0: 2048 }, [0, 4]).a0 >>> 0;
    assert.ok(owned >= 0xa1e27d80 && owned <= 0xa1e27d80 + 43328, 'real class-1 allocation');
    allocation = owned;
    lab.hook_rt(malloc, (h, r) => h.finish(r, { a0: allocation }), 'audit-allocation-success');
    M.dbgWrite(owned, Buffer.alloc(SIZE + 16, 0x5a));   // the block and a 16-byte guard band
    gate();
    assert.equal(read(handle, 2).readUInt16LE(), owned - 0xa1e27d80 + 1);
    const fresh = Buffer.alloc(SIZE); fresh.writeUInt32LE(0x55444143, 60);
    assert.deepEqual(read(owned, SIZE), fresh, 'initialise the complete state (zeros and the magic) before publishing');
    assert.equal(read(0xa218c2fe, 2).readUInt16LE(), owned - 0xa1e27d80 + 1, 'handle is in RAM as well');
    assert.deepEqual(read(owned + SIZE, 16), Buffer.alloc(16, 0x5a), 'state clear stops at its boundary');
    // A handle counts only when in range, 4-aligned and pointing at a block with the magic.
    const spots = [0xa1e27d80, 0xa1e326c0, 0xa1e27d84].map(a => [a + 60, read(a + 60, 4)]);
    for (const [value, pointer, magic] of [[0, 0, 1], [1, 0xa1e27d80, 1], [1, 0, 0], [43329, 0xa1e326c0, 1], [43329, 0, 0], [2, 0, 1], [5, 0xa1e27d84, 1], [43330, 0, 1], [65535, 0, 1]]) {
      for (const [a] of spots) word(a, magic ? 0x55444143 : 0x12345678);
      half(handle, value);
      const r = g.__call(0x605af4b0, { d0: 0x12345678, d1: 42, a1: 123 }, [0, 8]);
      assert.equal(r.a0 >>> 0, pointer >>> 0, `state handle ${value}`);
      assert.equal(r.d0, 0x12345678); assert.equal(r.d1, 42); assert.equal(r.a1, 123);
    }
    for (const [a, saved] of spots) M.dbgWrite(a, saved);
    console.log('STARTUP ASSERTIONS passed: 1023 incomplete masks, task gates, allocation retry, clear bounds, handle bounds, alignment and magic');
  } finally {
    for (const [pc, hook] of hooks) { if (hook) lab.hooks.set(pc, hook); else lab.hooks.delete(pc); }
    [handle, tid, ready].forEach((a, i) => M.dbgWrite(a, saved[i]));
    if (owned) g.__call(0x6002384a, { a0: owned }, [0, 4]);
  }
}
