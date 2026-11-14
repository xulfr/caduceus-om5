# Roadmap

All current firmware work is **emulator only**. No successful camera run of this project is recorded.
The owner performs any physical test; development sessions prepare and check files only.

## First priority: OM-5 Mark II (E148, firmware 1.1)

- Implemented: restored Color Profile 1–3 and Monochrome Profile 1–3, twelve-colour HSL,
  tone curve, per-profile white balance, ND32/ND64 menu entries, and films from one `LOOKS.BIN`.
- Implemented: LookLab, Python card writer, strict source builder, hash-checked release patcher,
  safety gate, tour and guides. These do not establish hardware compatibility.
- Implemented: automated Python/JavaScript writer parity, release reproduction and emulator film regressions.
- Firmware gaps: refresh the title and values immediately after a film change; restrict film stepping
  to the Picture Mode selector; show film names on the super control panel; repeat the mounted-card,
  missing-file check.
- Physical validation remains open: boot, restart with a saved profile, settings persistence,
  custom-mode recall, JPEG colour output, real ND32/64 capture and recovery. Use the
  [first camera test plan](docs/FIRST_FLASH.md) and record the exact package hash.

## Second stage: original OM-5 (E144, firmware 1.2)

Bring the existing E148-program transplant builder into this repository and rebuild using this
project's donor patch. Keep this developer-only: fitting and checksum validation do not show that
the E148 program can drive E144 hardware. This is not the Mark II patch applied to E144 stock.
No consumer E144 release or installation recommendation until its hardware assumptions are resolved.

## Deferred

Dedicated FILM carousel entries, more than three active slots, film metadata in EXIF, Blacks/Whites,
split toning, extra grain, Glow and Halation. Films, HSL, tone and ND64 take priority. Do not remove
native features to gain room without measuring the need and documenting the exact tradeoff.

## Community handover

Keep builds reproducible, upstream attribution intact and the emulator's limits visible. Contributions
should include commands, hashes and evidence. Report camera observations separately from emulator
observations. The `UNTESTED` patcher gate and site warnings remain until documented validation supports
a deliberate change.
