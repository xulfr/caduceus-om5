# OM-5 firmware development handover

## Camera baseline

- Alpha11 booted on the owner’s OM-5 Mark II (E148, stock 1.1). The owner confirmed
  the ND32/64 CP carousel icons and that Monochrome Color Filter stays open and
  accepts dial changes. The stock filter page has a blank centre.
  [Alpha11 camera report](research/OM5II-ALPHA11-CAMERA-2026-11-16.md).
- Use alpha11 until alpha12 has been checked on the camera.
  Run `python3 patch.py --release v0.1.0-alpha11`.
- Alpha10 had empty CP icons and restarted on the filter page.
  The out-of-range `0xffff` image lookup remains the leading hypothesis for that restart.
  [Alpha10 camera report](research/OM5II-ALPHA10-CAMERA-2026-11-17.md) and
  [static analysis](research/OM5II-MONO-FILTER-CP-2026-11-17.md#alpha11-follow-up).

## Alpha12 on `claude/pensive-hamilton-pg8dpr`

- Restores the swatches, selection outline and centre colour via the armed filter
  paint hook at `0x610d9bc0`. Reuses the existing pen functions and invalidates
  child 3 in `pg_axis` while the Color Filter page is active.
- Preserves alpha11’s stock word image `0x107e` and native layout. The ring painter
  uses a 44-byte call frame and makes pen calls. The “Level” label remains postponed.
  The native filter header, “Vivid” word, and level stay visible.
- Package SHA-256 `cddd7a1f1320e7680bec9e8430e25c69857c2f4bf764e571d6bfffb775acd3fa`.
  `camera_tested: false`. [Manifest](releases/v0.1.0-alpha12/patch.json),
  [results](tests/alpha12-results.json), and [build audit](tests/alpha12-build-audit.json).

## Next camera checks

1. After startup, open Monochrome Color Filter and turn both dials. Verify that the
   ring follows the header and that changing the level leaves the selected filter
   visible. Leave and re-enter. [Checklist](docs/FIRST_FLASH.md#alpha12-camera-checks).
2. Recheck ND32/64 icons and selection with both items ticked and with each ticked
   alone. Per-profile WB and ND exposure still need their camera checks.
3. Record the camera model, stock version, package SHA-256, steps and observations.

## Development

- Official E148 1.1 SHA-256 starts `9de5d77e`. Use GNU `mn10300-elf` tools and
  OM-Emu `xulfr/om-emu` branch `fix/e148-ipi-stride`, commit
  `bdb33470705b3be28db52cbe080c31d74db727d8`.
- [AGENTS.md](AGENTS.md), [docs/INDEX.md](docs/INDEX.md), and [docs/TESTING.md](docs/TESTING.md).
  The owner performs all camera updates.
