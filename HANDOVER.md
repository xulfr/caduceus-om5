# OM-5 firmware development handover

## Camera baseline

- **Alpha9** booted on the owner's OM-5 Mark II (E148, stock 1.1). The colour wheel
  worked and the Monochrome Color Filter page opened with no filter graphic.
  Package `2e9777ce08163fa6e4a97930683cd8eb0ce73197dfd5ac4a64d8928af98fbc50`.
  [Alpha9 camera report](research/OM5II-ALPHA9-CAMERA-2026-11-16.md).
- **Alpha10** booted. Opening the Monochrome Color Filter page caused a restart.
  It booted normally afterwards. ND32 and ND64 worked from the CP carousel with
  empty icons. Package `056aefb3c3f40b7cf41728cd9f466ba161a52d887db6ecebd2f0377bb0a38454`.
  [Alpha10 camera report](research/OM5II-ALPHA10-CAMERA-2026-11-17.md).
- Use alpha9 until alpha11 has been checked on the camera.
  Run `python3 patch.py --release v0.1.0-alpha9`.

## Alpha11 on `claude/pensive-hamilton-pg8dpr`

Package `5384eafef3cb06de4761dba50a09112135fa2cdfacb6716d9e4d0423f5b7072a`.
`camera_tested: false`. [Release manifest](releases/v0.1.0-alpha11/patch.json).

- **D2** restores alpha9 rendering. Reverted the `0xffff` word-image edit, both 10 px
  rectangle changes, the paint hook with the ring and “Level” text, and the extra
  child 3 invalidation. Alpha11 uses the stock painter and “Vivid” word. The
  picker is postponed because the painter and invalidation have no camera validation.
  The native header, filter and level controls remain. Kept the separate Filter sidebar icon.
- Alpha10 looked up `0xffff` beyond the image-table record with no bounds check on the
  traced path. This remains the leading crash hypothesis. The physical root cause
  has not been proved. OM-Emu tolerated the read.
- **D1** adds the CP carousel images `0x2358` and `0x2c84` by reusing the existing
  ND32/ND64 artwork. The stock viewer tables and resource pointers were verified.
  The emulator ran the constructor but did not draw a carousel frame. Kept the
  alpha10 CP any-item hook for cases where only ND32 or ND64 is ticked.
- [Static analysis](research/OM5II-MONO-FILTER-CP-2026-11-17.md#alpha11-follow-up),
  [results](tests/alpha11-results.json) and [build audit](tests/alpha11-build-audit.json).
  The Monochrome regression checks setting 1007, native header and level updates,
  persistence on re-entry and Profile 2 isolation. The ring and “Level” text checks
  were removed with the picker.

## Next camera checks

1. After the startup checks, **open Monochrome Color Filter and turn both dials first**.
   Stop and record the exact behaviour if the camera restarts. Use
   [the alpha11 checklist](docs/FIRST_FLASH.md#alpha11-camera-checks).
2. Check the ND32/ND64 carousel icons and selections with both items ticked, then
   with only one ticked. Check the shooting label and exposure separately.
3. Recheck Color Profile Shading, the Monochrome Film Grain and Filter sidebar
   icons, and per-profile white balance. ND64 digits remain compressed and ND32
   has a gap on the shooting display in OM-Emu.
4. Record the camera model, stock version, exact package SHA-256, steps and results.

## Development

- Official E148 1.1 SHA-256 starts `9de5d77e`. Use it with the GNU
  `mn10300-elf` tools. OM-Emu checkout `xulfr/om-emu`, branch
  `fix/e148-ipi-stride`, commit `bdb33470705b3be28db52cbe080c31d74db727d8`.
- See [AGENTS.md](AGENTS.md), [docs/INDEX.md](docs/INDEX.md) and
  [docs/TESTING.md](docs/TESTING.md). The owner performs physical-camera updates.
