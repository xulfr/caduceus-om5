# Alpha5 boot loop: compressed stream length (2026-11-15)

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
- Section 7's stream ends with the patch code in the section tail. Alpha5 is the first build whose tail code
  (`fl_str`, the string getter's gate) runs on every normal start. The card updater shows no text, so recovery working
  does not show that the tail was intact; checkpoint 12's "updater ran, so section 7 was fine" does not hold for the tail.
- The 8 Nov build's resource block used a different LZ4 encoding (liblz4 HC) from alpha1–5 (pure Python).

Everything else reachable before a half-press was reviewed again (hook bytes, frames, MDR/`retf`, section order,
alignment of every data table, no `0xfb` opcodes, no branch into a hook site, loader extents, load order 1, 8, 2…10,
HLS manager padding). No defect was found there. The E-P7/OM-3 projects' camera lessons were used as the checklist.

## Fix (alpha6, package `2bb95563fc7c61fac8da2b9c2f2fa177d6395bcafe2941755b5ed8163d3c3e84`)

- `tools/oly_compress.py`: `stream_length: "stock-page"` re-encodes each changed stream so that L equals OM's own
  L modulo 4096 (two LZ4 rewrites that do not change the decoded bytes) and refuses a length the loader would
  truncate or that ends within 96 bytes of any power-of-two boundary from 2 KiB to 16 MiB.
  Alpha6: section 6 L = 2,254,191 (1391), section 7 L = 2,505,716 (3060).
- `tools/oly_resource.py`: `lz4_recipe` reproduces the 8 Nov resource block byte for byte (`6b93ba21…7a22`), the
  only patched resource stream that has started on a camera.
- The expanded main program is **byte-identical to alpha5** (`cc0efda8…76a0`): no code changed.
- The builder checks every compressed stream of every rewritten component against the rule.

## Not established

- That the stream length was the cause. It is the only difference found that fits "every start fails, update mode
  works", and it is removed. A camera start is the only proof.
- Possible leftover from the 8 Nov run: hidden setting 903/989 non-zero makes the picture mode read as 63 on the
  first start. Choosing a picture mode once rewrites all four settings.
- The original OM-5 pre-alpha 1 (`70788992…d1b4`) predates this rule and its stream lengths were not checked.
  Do not flash it until it is rebuilt with the rule.
