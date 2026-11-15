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
  const saved = [read(handle, 2), read(tid, 2), read(ready, 4)];
  const hooks = new Map([malloc, getTid].map(pc => [pc, lab.hooks.get(pc)]));
  let allocations = 0, taskCalls = 0, taskResult = 0, taskId = 1, allocation = 0;
  let owned = 0;
  const gate = () => g.__call(0x613f2f7f, {}, [0xf0, 36]);
  try {
    half(handle, 0); half(tid, 1);
    lab.hook_rt(getTid, (h, r) => { taskCalls++; half(r.a0, taskId); h.finish(r, { d0: taskResult }); }, 'audit-get-tid');
    lab.hook_rt(malloc, (h, r) => {
      allocations++; assert.equal(r.d0, 1024); h.finish(r, { a0: allocation });
    }, 'audit-allocation');
    for (let mask = 0; mask < 1023; mask++) { word(ready, mask); gate(); }
    assert.equal(taskCalls, 0, 'all incomplete section masks return before OS calls');
    assert.equal(allocations, 0);
    word(ready, 1023);
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
    M.dbgWrite(owned, Buffer.alloc(1040, 0x5a));
    gate();
    assert.equal(read(handle, 2).readUInt16LE(), owned - 0xa1e27d80 + 1);
    assert.deepEqual(read(owned, 1024), Buffer.alloc(1024), 'initialise the complete state before publishing');
    assert.deepEqual(read(owned + 1024, 16), Buffer.alloc(16, 0x5a), 'state clear stops at its boundary');
    for (const [value, pointer] of [[0, 0], [1, 0xa1e27d80], [43329, 0xa1e326c0], [43330, 0], [65535, 0]]) {
      half(handle, value);
      const r = g.__call(0x613f2ed8, { d0: 0x12345678, d1: 42, a1: 123 }, [0, 8]);
      assert.equal(r.a0 >>> 0, pointer >>> 0, `state handle ${value}`);
      assert.equal(r.d0, 0x12345678); assert.equal(r.d1, 42); assert.equal(r.a1, 123);
    }
    console.log('STARTUP ASSERTIONS passed: 1023 incomplete masks, task gates, allocation retry, clear bounds, handle bounds');
  } finally {
    for (const [pc, hook] of hooks) { if (hook) lab.hooks.set(pc, hook); else lab.hooks.delete(pc); }
    [handle, tid, ready].forEach((a, i) => M.dbgWrite(a, saved[i]));
    if (owned) g.__call(0x6002384a, { a0: owned }, [0, 4]);
  }
}
