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

## Alpha7 (blocked)

Alpha7 can call section 8 from section 2 during startup. Alpha8 moves the gates into section 2.
[Load-order findings](../HANDOVER.md).

Package `c6f3a8fa5e68082498dc2ea148dfc8e50f2dcf349ad9f30d91c3ffffa330243a`, `releases/v0.1.0-alpha7`. It keeps the length rule and changes the main program:

- **Every hook is gated on the armed state.** Before the first half-press each hook replays OM's displaced
  instructions and returns once its gate can run: refresh tail, capture builder, mode-list copies, custom-mode reset, WB and
  profile-setting commits, the Picture Mode page updater; the editor, Delete, labels and the string getter were
  already gated. This removes explanation 1 for project code. `tests/unarmed_pcs.py` traces an unarmed emulator
  session and accepts only gates and replays.
- **The armed state is checked, not trusted.** `st_ptr` reads the handle from RAM (uncached alias; the main program
  runs on more than one CPU, each with its own cache), and accepts it only if it is inside the pool, 4-aligned and
  the block carries the magic `CADU` that `arm_gate` writes. Alpha5/alpha6 accepted any in-range value read through
  the cache. Arming writes the handle through the cache and to RAM. This narrows explanation 2 (a wrong or stale
  handle at start-up would have made alpha5/alpha6 act as armed, write into the heap and enter section 10).
- **At the arming half-press** (`arm_refresh`, section 10): a profile number left without its family (903 / 989
  non-zero while 111's family is another mode, which makes 111 read 63) is cleared, and the camera's own refresh
  runs for a context that is on a profile, holds a tone save, or was just repaired.

OM's startup code still reads the added table entries, and the string getter still runs for every string.
The physical boot sequence remains unverified.

Emulator and host checks are listed in `tests/alpha7-results.json`.

## The one test that separates 1 from 2

Flashing the 8 Nov package (`e2ca5b28…92e1`, rebuilt from `xulfr/oly_fw_analysis` `25a336e`) again, without
touching the Picture Mode screen: if it now loops at once, the camera's stored state is the cause (1); if it starts
as it did on 8 Nov, the code added since is (2 or 3). This is the owner's decision; it is a camera flash of a build
that later looped, and recovery has worked five times but is not guaranteed.
