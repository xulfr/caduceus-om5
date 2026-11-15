# Fifth OM-5 Mark II boot failure: alpha6 (2026-11-15)

**Camera result, negative.** Reported by the owner (xulfr) during the session that produced alpha6 and alpha7.

| | |
|---|---|
| Camera | OM-5 Mark II (E148), stock firmware 1.1 |
| Package | v0.1.0-alpha6. `patch.py` writes the file only when it equals SHA-256 `2bb95563fc7c61fac8da2b9c2f2fa177d6395bcafe2941755b5ed8163d3c3e84`. The owner did not report the printed checksum. |
| Outcome | "Went straight to a boot loop." |
| Not recorded | Card contents, whether a half-press was made, whether OM's 1.1 was restored afterwards and how, what was on the camera's settings before. Ask the owner. |

The owner flashed while the session was paused; no session asked for or suggested the flash.

## What it rules out

Alpha6 has alpha5's expanded main program byte for byte (`cc0efda8…76a0`). It differs from alpha5 only in the LZ4
encoding: sections 6 and 7 re-encoded to OM's packed length modulo 4096 (2,254,191 and 2,505,716 bytes), and the
resource block byte-identical to the 8 Nov build's (`6b93ba21…7a22`), which started on this camera.

- The compressed stream length (alpha5's section 7 = 611 x 4096 bytes) is **not** the cause, or not the only one.
  [The stream-length note](OM5II-STREAM-LENGTH-2026-11-15.md) is kept as a negative result; its length rule stays in
  the builder because the loader's block arithmetic is real, but it explains nothing observed.
- The resource block's encoding is not the cause.

## What remains

The cause is in what the alpha5/alpha6 main program does on a normal start that the 8 Nov build
(`e2ca5b28…92e1`, started once) did not, or in what the 8 Nov run left in the camera:

1. **Settings left by the 8 Nov run.** That build started, froze on the Picture Mode screen, then looped at every
   start until OM's firmware was restored. OM's firmware does not touch part 1 of settings 904-975 (WB records, tone
   save 964-971, look names) or 903/989. With them present, alpha5/alpha6 run the project's refresh, list copies
   and builder during start-up. Not shown on a camera; the emulator does not fail in that state.
2. **Start-up code added since 8 Nov**: the string getter hook `0x60d52ed5` -> `fl_str` (every string), the
   half-press hook `0x602f0b95` -> `arm_hook`, `st_ptr` calls from the WB commit, the tag in `d2` on the refresh
   path, the extension vector and section-10 code. Each was re-read against the stock bytes, frames, MDR/`retf`,
   alignment, `0xfb` opcodes, section order and branches into hook sites; no defect was found on paper.
3. **Stock code meeting the added table entries** with whatever picture-mode state the camera holds.

## Alpha7 (unreleased, blocked, not camera-tested)

Source at this commit; package `e0b76026842440e93b769a936a1f115aca1ed4d7941c28788eaf11c72b63dbd8`. It keeps the length rule and gates every hook on the armed state, so before
the first half-press each hook replays OM's instructions only (addresses 1, not 2 or 3). Emulator: gating probe,
unarmed execution trace, startup probe, static rules and build audit pass; the 19-case regression was started and
**not finished**. Do not flash it on this evidence.

## The one test that separates 1 from 2

Flashing the 8 Nov package (`e2ca5b28…92e1`, rebuilt from `xulfr/oly_fw_analysis` `25a336e`) again, without
touching the Picture Mode screen: if it now loops at once, the camera's stored state is the cause (1); if it starts
as it did on 8 Nov, the code added since is (2 or 3). This is the owner's decision; it is a camera flash of a build
that later looped, and recovery has worked five times but is not guaranteed.
