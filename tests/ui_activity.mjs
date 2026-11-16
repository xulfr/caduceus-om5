// PRE and POST module for sess.mjs (tests/run_ui_activity.py). Mounts the card, then counts, while tracing is on
// (keys T+ / T-): restarts of the direct-setting screen's inactivity timer (0x60f10fd2 with d0 = 500) and OM's
// widget invalidate (0x60d49294) on a page widget (class 0x60fcb58c, the Color/Monochrome Profile pages).
// POST checks the counts against UI_TIMER / UI_PAGE_INVALIDATE when set. Emulator only.
let timer = 0, page = 0;
export default async function (g) {
  const M = g.__M;
  if (g.__uiActivity) {
    console.log(`UI_ACTIVITY timer=${timer} page_invalidate=${page}`);
    const want = (k) => (process.env[k] === undefined ? null : Number(process.env[k]));
    const t = want('UI_TIMER'), p = want('UI_PAGE_INVALIDATE');
    if (t !== null && t !== timer) throw new Error(`timer restarts ${timer}, expected ${t}`);
    if (p !== null && p !== page) throw new Error(`page invalidations ${page}, expected ${p}`);
    console.log('ASSERTIONS passed');
    return;
  }
  g.__uiActivity = true;
  M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  g.__trace = { on: false };
  M.setExecTrace((pc) => {
    if (!g.__trace.on) return;
    if (pc === 0x60f10fd2) { if ((M.getRegs()[0] >>> 0) === 500) timer++; }
    else if (pc === 0x60d49294) {
      const a0 = M.getRegs()[4] >>> 0;
      if (a0 && Buffer.from(M.dbgRead(a0, 4)).readUInt32LE() === 0x60fcb58c) page++;
    }
  });
}
