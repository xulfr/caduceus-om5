import assert from 'node:assert/strict';
export default function (g) {
  const get = id => g.__call(0x602d000d, {d0: id}, [0, 4]).d0;
  assert.deepEqual([get(111), get(903), get(989)], [1, 0, 0]);
  console.log('STALE ASSERTIONS passed: Natural restored and both profile numbers cleared');
}
