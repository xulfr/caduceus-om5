# Roadmap

All current firmware work is **emulator only**. No successful camera run of this project is recorded.
The owner performs any physical test; development sessions prepare and check files only.

## First priority: OM-5 Mark II (E148, firmware 1.1)

- Implemented: restored Color Profile 1–3 and Monochrome Profile 1–3, twelve-colour HSL,
  tone curve, per-profile white balance, ND32/ND64 menu entries, and films from one `LOOKS.BIN`.
- Implemented: LookLab, Python card writer, strict source builder, hash-checked release patcher,
  safety gate, tour and guides. These do not establish hardware compatibility.
- Implemented: automated Python/JavaScript writer parity, release reproduction and emulator film regressions.
- Implemented in v0.1.0-alpha2 (emulator only): the title and values repaint on each film step; the
  trash button steps films only on the Picture Mode row; the super control panel shows the film name
  while its Picture Mode cell is highlighted; the mounted-card, missing-file case is a regression test.
- Open, cosmetic: after returning from the lower rows the stock title reads "Picture Mode" rather than
  the film name; in the emulator the super control panel's Picture Mode cell draws no icon for a
  Color Profile.
- Physical validation remains open: boot, restart with a saved profile, settings persistence,
  custom-mode recall, JPEG colour output, real ND32/64 capture and recovery. Use the
  [first camera test plan](docs/FIRST_FLASH.md) and record the exact package hash.

## Second stage: original OM-5 (E144, firmware 1.2)

The [E148-program transplant builder](patches/ports/om-5-i-from-ii/README.md) is included and rebuilt
using this project's donor patch. It remains developer-only: fitting and checksum validation do not show that
the E148 program can drive E144 hardware. This is not the Mark II patch applied to E144 stock.
No consumer E144 release or installation recommendation until its hardware assumptions are resolved.
Emulator and static work reached so far (2026-11-14): film regressions and a menu tour pass in OM-Emu's
Mark II model; OM-Emu's OM-5 model cannot run Mark II code; open questions are the controller (010e) protocol,
renumbered identifiers, one SRAM layout shift and the relocated resource addresses. See
`research/OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md`.

## Deferred

Dedicated FILM carousel entries, more than three active slots, film metadata in EXIF, Blacks/Whites,
split toning, extra grain, Glow and Halation. Films, HSL, tone and ND64 take priority. Do not remove
native features to gain room without measuring the need and documenting the exact tradeoff.

## Community handover

Keep builds reproducible, upstream attribution intact and the emulator's limits visible. Contributions
should include commands, hashes and evidence. Report camera observations separately from emulator
observations. The `UNTESTED` patcher gate and site warnings remain until documented validation supports
a deliberate change.
