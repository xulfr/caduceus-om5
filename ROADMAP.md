# Roadmap

Alpha8 and alpha9 booted on a physical OM-5 Mark II. [Alpha8 report](research/OM5II-ALPHA8-CAMERA-2026-11-15.md),
[alpha9 report](research/OM5II-ALPHA9-CAMERA-2026-11-16.md). Alpha10 booted and restarted on the filter page. [Alpha10 report](research/OM5II-ALPHA10-CAMERA-2026-11-17.md).
The owner performs any physical test; development sessions prepare and check files only.

## First priority: OM-5 Mark II (E148, firmware 1.1)

- Implemented: restored Color Profile 1–3 and Monochrome Profile 1–3, twelve-colour HSL,
  tone curve, per-profile white balance, ND32/ND64 menu entries, and looks from one `LOOKS.BIN`.
- Implemented: LookLab, Python card writer, strict source builder, hash-checked release patcher,
  safety gate, tour and guides. These do not establish hardware compatibility.
- Implemented: automated Python/JavaScript writer parity, release reproduction and emulator look regressions.
- Implemented in v0.1.0-alpha2 (emulator only): the title and values repaint on each look step; the
  trash button steps looks only on the Picture Mode row; the super control panel shows the look name
  while its Picture Mode cell is highlighted; the mounted-card, missing-file case is a regression test.
- Implemented in v0.1.0-alpha4 (emulator only): the look name remains visible after returning from the lower
  rows. Look names cannot inject camera display commands. Installer reruns preserve custom look banks.
- Fixed in v0.1.0-alpha5 (emulator only): the title restore no longer writes a 32-bit word into the camera's
  16-bit row descriptor fields; a look without a WB shift sets the shift to 0 instead of keeping the previous
  look's shift.
- Alpha9 is the camera-checked baseline. Alpha10 added Color Profile Shading, the Monochrome Film Grain
  and Color Filter sidebar icons, and ND32/64 selection in the CP carousel.
- Alpha11 is the camera-checked baseline. Its stock filter painter and the CP carousel artwork resolved both
  alpha10 defects. [Camera report](research/OM5II-ALPHA11-CAMERA-2026-11-16.md).
- Alpha12 restores the filter ring with the stock text and layout. Start the camera check on that page and turn
  both dials. Per-profile white balance still needs its camera check.
- Planned after the first alpha: **colour grain for Color Profiles** (Off / Low / Medium / High, as the
  Monochrome Profiles' Film Grain). The camera already applies grain through effective setting 998 for Monochrome
  Profiles; a Color Profile needs its own grain row, per-profile storage and a refresh entry (998 = 0 today).
  Then the other effects (Glow, Halation).
- Open: ND64 / ND32 digit artwork on the shooting screen.
- Physical validation remains open: boot, restart with a saved profile, settings persistence,
  custom-mode recall, JPEG colour output, real ND32/64 capture and recovery. Use the
  [camera test checklist](docs/FIRST_FLASH.md) and record the exact package hash.

## Second stage: original OM-5 (E144, firmware 1.2)

The [E148-program transplant builder](patches/ports/om-5-i-from-ii/README.md) is included and rebuilt
using this project's donor patch. Fitting and checksum validation do not show that
the E148 program can drive E144 hardware. This is not the Mark II patch applied to E144 stock.
Since 2026-11-14 it is offered as a **pre-alpha for testers** ([docs/OM5_PREALPHA.md](docs/OM5_PREALPHA.md)): built
by the tester with the developer builder, never run on a camera, with a step 0 that checks the card update with
OM's own firmware first. It stays out of the one-step patcher. No recommendation to install it until camera
reports exist.
Emulator and static work reached so far (2026-11-14): look regressions and a menu tour pass in OM-Emu's
Mark II model; OM-Emu's OM-5 model cannot run Mark II code; open questions are the controller (010e) protocol,
renumbered identifiers, one SRAM layout shift and the relocated resource addresses. See
`research/OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md`.

## Deferred

Dedicated FILM carousel entries, more than three active slots, film metadata in EXIF, Blacks/Whites,
split toning, extra grain, Glow and Halation. Looks, HSL, tone and ND64 take priority. Do not remove
native features to gain room without measuring the need and documenting the exact tradeoff.

## Community handover

Keep builds reproducible, upstream attribution intact and the emulator's limits visible. Contributions
should include commands, hashes and evidence. Report camera observations separately from emulator
observations. The `UNTESTED` patcher gate and site warnings remain until documented validation supports
a deliberate change.
