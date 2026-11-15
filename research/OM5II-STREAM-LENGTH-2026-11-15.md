# Alpha5 boot loop: compressed stream length (2026-11-15)

> **Refuted as the cause on a camera, 15 Nov 2026:** alpha6, built with this fix, boot-looped too.
> See [the fifth boot failure](OM5II-FIFTH-BOOT-FAILURE-2026-11-15.md). Kept as a negative result.

Static analysis and build comparison only. **No camera was used; alpha6 has not run on a camera.**

## Finding

Sections 6 and 7 of the main program are stored as LZ4 streams (`olycompress`, 32-byte header + packed length L).
In the alpha5 package (`98bd2433…80c2`) the section-7 stream is **exactly 2,502,656 bytes = 611 × 4096**.

| Build | Section 6 L (mod 4096) | Section 7 L (mod 4096) | Camera |
|---|---|---|---|
| OM 1.1 | 2,250,095 (1391) | 2,501,620 (3060) | works |
| 8 Nov `e2ca5b28…` | 2,250,847 (2143) | 2,502,551 (3991) | started |
| alpha5 | 2,250,970 (2266) | 2,502,656 (**0**) | boot loop at every start |

- The loader (`0x6005b249`) reads `(L // 2048 + 1) * 2048` bytes from flash although the stream is `32 + L` bytes:
  it ignores the header. Proven consequence: a stream with `L % 2048 > 2016` loses its last bytes. Nothing checked this.
- The stream is decoded by the other processor (mailbox `0x8ff00b80..94`; its code is not in the main program and
  was not found). A length that is an exact page multiple is the edge case of the same "header forgotten" arithmetic.
  This part is an inference: the chance of an exact 4096 multiple by accident is about 1 in 2,000 per build.
- Shape of the stream end (checked in the alpha5 and alpha6 packages): the patch code of the section tail is one
  literal run (about 1 KB), then one match for the `0xff` filler up to the next section (92,570 / 649,402 bytes,
  about 0.4 / 2.5 KB of length bytes), then 5 literals. Losing the last bytes of the stream would shorten the filler
  or fail the decode; it would not damage the patch code itself.
- Against this explanation: the card updater is in section 7 (checkpoint 12), and the restore worked with alpha5
  installed, so section 7 was decoded on that start. For the length to be the cause, the fault must depend on
  something that differs between an update start and a normal start. That is not shown.
- The 8 Nov build's resource block used a different LZ4 encoding (liblz4 HC) from alpha1–5 (pure Python).

Everything else reachable before a half-press was reviewed again (hook bytes, frames, MDR/`retf`, section order,
alignment of every data table, no `0xfb` opcodes, no branch into a hook site, loader extents, load order 1, 8, 2…10,
HLS manager padding). No defect was found there. The E-P7/OM-3 projects' camera lessons were used as the checklist.

## Fix (alpha6, package `2bb95563fc7c61fac8da2b9c2f2fa177d6395bcafe2941755b5ed8163d3c3e84`; kept in alpha7)

- `tools/oly_compress.py`: `stream_length: "stock-page"` re-encodes each changed stream so that L equals OM's own
  L modulo 4096 (two LZ4 rewrites that do not change the decoded bytes) and refuses a length the loader would
  truncate or that ends within 96 bytes of any power-of-two boundary from 2 KiB to 16 MiB.
  Alpha6: section 6 L = 2,254,191 (1391), section 7 L = 2,505,716 (3060).
- `tools/oly_resource.py`: `lz4_recipe` reproduces the 8 Nov resource block byte for byte (`6b93ba21…7a22`), the
  only patched resource stream that has started on a camera.
- The expanded main program is **byte-identical to alpha5** (`cc0efda8…76a0`): no code changed.
- The builder checks every compressed stream of every rewritten component against the rule.

## Second safeguard (alpha7): nothing of ours acts before the first half-press

A second explanation fits the record as well and is independent of the stream: the 8 Nov build started once, froze
when the Picture Mode screen was used, and then looped at every start until OM's firmware was restored. Something
that run stored made the next starts fail. OM's firmware does not touch the profile settings this project adds
(part 1 of settings 904–975, the tone save in 964–971, 903/989), so they were still there when alpha5 started for
the first time, and alpha5 ran the project's picture-mode refresh, list copies and builder at start-up.

Alpha7 therefore gates every hook on the armed state (set at the first shutter half-press after power-on, with all
ten sections initialised). Until then each hook replays OM's displaced instructions and returns:

| Hook | Before the first half-press |
|---|---|
| picture-mode refresh tail (`rt_tail`) | stock tail (alpha5: profile apply / undo ran) |
| capture builder (`apply_values`) | nothing (alpha5: read properties and cells) |
| mode-list copies (`pm_set`, `pm_put`), custom-mode reset (`creset`) | the stock call only |
| WB commit and profile-setting commit (`wb_load`) | stock commit for every setting |
| string getter, editor read/write/display, Delete, labels | stock (as alpha5) |

At the half-press that arms the patch, `arm_refresh` runs the camera's refresh once for a context that is on a
profile or still holds a tone save, so a profile left selected at power-off is applied then.
What still differs from OM's firmware during start-up: the data tables (profile entries, ND, resource aliases), the
displaced-instruction replays, and one read of the state handle per hook.

Consequence: the profile's contrast and sharpness, hue/lightness, and looks are active from the first half-press
after power-on. A photo taken without a half-press (for example by remote control) before that uses stock values.

Emulator: `tests/unarmed_assert.mjs` (inert before, applied after), all 19 look/menu cases, startup probe.

## Not established

- Which of the two explanations, if either, caused the alpha5 loop. Both are removed in alpha7. A camera start is
  the only proof.
- Whether a Color Profile works on the camera's image processor at all. If it does not, alpha7 should fail when a
  profile is applied after a half-press, not at start-up.
- Possible leftover from the 8 Nov run: hidden setting 903/989 non-zero makes the picture mode read as 63 on the
  first start. Choosing a picture mode once rewrites all four settings.
- The original OM-5 pre-alpha 1 (`70788992…d1b4`) predates this rule and its stream lengths were not checked.
  Do not flash it until it is rebuilt with the rule.
