// PRE module for tests/run_boot_arm.py: mount the card (unless OM5_UNMOUNTED=1), then start boot.s's background task
// the way its FastEndCb hook does (OM-Emu does not run E148's FastEndCb; sess.mjs --ready has already published
// the section bits). OM5_BG_START = bg_start's address, from the build's symbols. OM5_BG_START unset: nothing started.
export default async function (g) {
  if (process.env.OM5_UNMOUNTED !== '1') g.__M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  const at = process.env.OM5_BG_START;
  if (!at) return;
  const r = g.__call(parseInt(at, 16), {}, [0, 16]);
  const tid = r.d0 >>> 0, lab = g.__lab;
  // OM-Emu runs only the firmware tasks its lab allows (as the c3d runner allows c3d's): allow ours
  const t = lab.nk.tasks().get(tid);
  if (t) lab.lt.allow.add(t[0]);
  console.log(`BG START called: task ${tid} entry ${t ? '0x' + (t[0] >>> 0).toString(16) : 'none'}`);
}
