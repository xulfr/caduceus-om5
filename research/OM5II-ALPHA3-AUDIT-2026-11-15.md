# OM-5 Mark II alpha2 audit and alpha3 retest

Target is E148 firmware 1.1 build 1100. The alpha2 source rebuilt to its published package
SHA-256, `2eac7af1d82b119acba3952e8dac1dd6b8faec3cbaf1fcbfa9fcced600167ca9`.

## Delete could branch into the last-loaded section before arming

`hsl_delete_action` in section 7 called `fl_delete` in section 10 before checking the state handle.
The check inside `fl_delete` could run only after the branch had already reached section 10.
The state handle is published after the loader completion check for all ten sections.

To isolate the call, the `unarmed-delete` case leaves the handle unpublished, replaces the
section-10 extension with its stock bytes and presses Delete on the Picture Mode strip. Alpha2
trapped at `0x6169c954` in OM-Emu. Alpha3 checks `st_ptr` from section 7 before the call.
The same case stayed on the Picture Mode screen with the handle still unpublished.

## A ten-look bank with trailing data could pass verification

Alpha2's read stopped after 832 bytes. A valid ten-look bank plus a trailing byte passed the
length and CRC checks because the extra byte was never read. In `oversized-bank` the asserted
load state was rejected (2), but alpha2 reported loaded (1).

Alpha3 reads up to 833 bytes and rejects counts above 832 before checking the header. The buffer
begins at offset 152 in the 1024-byte state allocation, so the extra byte fits. The 833-byte case
is rejected and the 832-byte case loads and applies a look.

## Windows launcher ran the patcher twice after a refusal

With both `py` and `python` available, the old batch file treated every failure from `py -3 patch.py`
as a reason to run `python patch.py`. A stub returning 1 ran twice. The revised launcher probes
for a working Python 3 launcher first, runs the patcher once and returns its exit status. A real
`NO` response to the acknowledgement prompted once and returned 1.

## Build verification

- The strict builder checked hook preimages, native loaded section bounds, compression and
  package checksums. The expanded main comparison located every difference from alpha2 in
  declared ranges in sections 7 and 10. Existing section sizes in the native loader and the
  resource component were byte-identical across the two builds.
- All 15 emulator cases passed with zero additional image stores relative to their matching stock
  sessions. See [alpha3 results](../tests/alpha3-results.json).
- The Live ND static selector check passed 768 inputs. Physical Live ND exposures remain unverified.
- The default installer generated the alpha3 package and an exact E148 stock restore. It copied
  the starter bank byte for byte from the release. The release manifest records the package hash.
- The original OM-5 pre-alpha 1 instructions pin the existing alpha2 donor revision. A build
  from that revision reproduced the published E144 checksum.

## Open

The Picture Mode strip can still show the generic title after returning from a lower row, even
when the look changes. The super control panel still lacks a Color Profile icon in OM-Emu.
The emulated startup case exercises the branch in isolation. The real loader, second processor,
image processing, settings persistence and card recovery require physical validation. Alpha3
has no camera result. Three earlier builds caused boot loops, as recorded in [Safety](../docs/SAFETY.md).
