# Original OM-5 pre-alpha 1: first camera report, failed to start (2026-11-17)

**Camera result, negative.** The first report from an original OM-5 (E144). A tester posted it in a
[comment on issue #4](https://github.com/xulfr/caduceus-om5/issues/4#issuecomment-6941382886) on 17 November 2026.
The issue itself is about an unrelated proposal. The owner did not run this test, and nobody has confirmed the
report independently.

| | |
|---|---|
| Camera | Original OM-5 (E144), stock firmware 1.2 |
| Package | Pre-alpha 1, SHA-256 `70788992f032dad53bfa4e145b2147e376d3f25a62e2b1ce2929973fec26d1b4`, as reported by the tester. That is the checksum published for pre-alpha 1 (`tests/e144-results.json`). It was built from revision `02c3cb2` with the Mark II **v0.1.0-alpha2** donor (donor package `2eac7af1…7ca9`). |
| Install | `generated/om5-prealpha1/install/DCOLYMP/E1449999.BIN` from the SD card (hold OK, switch on). The tester says the update "completed normally". |
| Outcome | Did not start. The screen stayed completely black, with no backlight and no display, and the camera was "completely silent". |
| Recovery | The tester restored OM's firmware 1.2 from the card (hold OK, switch on). They report the camera is fully working again. |
| Not recorded | Whether step 0 (flashing OM's own 1.2 first) was done. The update light sequence. Whether the lens or stabiliser moved. Whether the restore worked first time. The battery and card used. The `jpegtran` version. Whether a half-press or any button was tried. |

## What it shows

- **Pre-alpha 1 does not start on this camera.** It reached no visible UI at all.
- **The E144 card update still worked after a failed transplant.** This is the first evidence on an original OM-5.
  Until now the tester page called this unknown. It is one camera and one failure mode (black screen). It does not
  show that recovery will work after every kind of failure.
- The update itself was accepted. The bootloader took the E144 container that the builder wrote: outer headers,
  slot layout and checksums. On the Mark II a refused file blinks fast straight away. The tester reports a normal update.

## What it does not tell apart

Pre-alpha 1's donor is a blocked Mark II build. The alpha2 manifest says it "shares the startup code of alpha5,
which caused a boot loop on 15 Nov 2026; never flashed." Alpha2 was never run on a Mark II. So this failure has at
least two explanations, and the report cannot separate them:

1. **The donor's own startup defect.** The cause of the alpha5/alpha6 boot loop is still not established
   ([fifth failure](OM5II-FIFTH-BOOT-FAILURE-2026-11-15.md)). Alpha8 and later changed the startup gating, and
   alpha8 to alpha12 start on a Mark II.
2. **The transplant itself.** The Mark II program may not drive E144 hardware. The open questions are in
   [the transplant note](OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md): the controller (010e) protocol,
   about 90 renumbered identifiers, one moved variable in on-chip SRAM, and the relocated resource addresses.

The symptom differs from alpha5/alpha6 on the Mark II, which went into a boot loop. It matches the two earliest
Mark II failures more closely: they never started, with a black screen and the lens hunting
([Safety](../docs/SAFETY.md#what-is-known)). This is an observation only. Nobody has shown that the causes are
related.

## Consequences

- No working original OM-5 build exists. Pre-alpha 1 is withdrawn and must not be flashed again.
- Pre-alpha 2 (alpha12 donor, `main` since 2026-11-17) removes explanation 1 as far as the Mark II can show it,
  because alpha12 starts there. It has not been built from OM's files and has no reference checksum. A failure of
  pre-alpha 2 would point more strongly at explanation 2. A success would not establish hardware compatibility.
- Useful next questions for the tester:
  - Did the lens or stabiliser make any sound or movement?
  - Did the restore work first time?
  - Would they build pre-alpha 2 and report its `build.json` before any flash?
