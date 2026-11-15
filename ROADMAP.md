# Roadmap

All current firmware work is **emulator only**. No successful camera run of this project is recorded.
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
- Open, cosmetic: in the emulator the super control panel's Picture Mode cell draws no icon for a Color Profile.
- Physical validation remains open: boot, restart with a saved profile, settings persistence,
  custom-mode recall, JPEG colour output, real ND32/64 capture and recovery. Use the
  [first camera test plan](docs/FIRST_FLASH.md) and record the exact package hash.

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
