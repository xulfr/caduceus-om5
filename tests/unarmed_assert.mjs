// POST for sess.mjs. Start-up gating (alpha7): before the first half-press a Color Profile selected in the
// settings must not run the project's refresh; the half-press that arms the patch applies it once.
// EXPECT=inert   keys without s1, ending on a Color Profile: no tone save is taken (the profile refresh did not run)
// EXPECT=applied the same keys followed by s1: the tone save is held (the arming refresh ran the profile path)
// Emulator only. The tone save is word 0 of part 1 of setting 964 (context 0), 0x544f4e45 while held.
import assert from 'node:assert/strict';
export default function (g) {
  const c = g.__call;
  const mode = c(0x602d000d, { d0: 111 }, [0, 4]).d0;
  const save = c(0x602f50f8, { d0: 964, d1: 1 }, [0x80, 8]).d0 >>> 0;
  const armed = Buffer.from(g.__M.dbgRead(0x6218c2fe, 2)).readUInt16LE() !== 0;
  assert.ok(mode >= 54 && mode <= 56, 'session must end on a Color Profile, got ' + mode);
  if (process.env.EXPECT === 'inert') { assert.equal(armed, false); assert.notEqual(save, 0x544f4e45, 'profile refresh ran before arming'); }
  else if (process.env.EXPECT === 'applied') { assert.equal(armed, true); assert.equal(save, 0x544f4e45, 'arming did not apply the profile'); }
  else throw new Error('set EXPECT=inert or EXPECT=applied');
  console.log(`GATING ${process.env.EXPECT}: passed (mode ${mode}, armed ${armed}, tone save ${save.toString(16)})`);
}
