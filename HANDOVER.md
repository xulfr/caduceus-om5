# OM-5 firmware development handover

## Camera baseline

- Alpha11 booted on the owner’s OM-5 Mark II (E148, stock 1.1). The owner confirmed
  the ND32/64 CP carousel icons and that Monochrome Color Filter stays open and
  accepts dial changes. The stock filter page has a blank centre.
  [Alpha11 camera report](research/OM5II-ALPHA11-CAMERA-2026-11-16.md).
- Alpha12 is the current experimental build. The owner reports that the remaining
  Monochrome Color Filter graphic issue is fixed. [Alpha12 camera findings](releases/v0.1.0-alpha12/README.md).
- Alpha10 had empty CP icons and restarted on the filter page.
  The out-of-range `0xffff` image lookup remains the leading hypothesis for that restart.
  [Alpha10 camera report](research/OM5II-ALPHA10-CAMERA-2026-11-17.md) and
  [static analysis](research/OM5II-MONO-FILTER-CP-2026-11-17.md#alpha11-follow-up).

## Alpha12 (merged to `main`)

- Restores the swatches, selection outline and centre colour via the armed filter
  paint hook at `0x610d9bc0`. Reuses the existing pen functions and invalidates
  child 3 in `pg_axis` while the Color Filter page is active.
- Preserves alpha11’s stock word image `0x107e` and native layout. The ring painter
  uses a 44-byte call frame and makes pen calls. The “Level” label remains postponed.
  The native filter header, “Vivid” word, and level stay visible.
- Package SHA-256 `cddd7a1f1320e7680bec9e8430e25c69857c2f4bf764e571d6bfffb775acd3fa`.
  The installer retains `camera_tested: false` and its acknowledgement pending
  a per-step report with the flashed package hash. [Manifest](releases/v0.1.0-alpha12/patch.json),
  [results](tests/alpha12-results.json), and [build audit](tests/alpha12-build-audit.json).

## Original OM-5 builder (`claude/tender-pascal-momfaz`)

- `patches/ports/om-5-i-from-ii/build.py` now uses the alpha12 donor (`firmware/om5ii`). The tester page no longer
  pins the alpha2 revision. The transplant repacks main with the donor's `stock-page` stream-length rule.
- Not yet built from OM's files. Pre-alpha 2 needs a first reference `build.json` before a checksum can be
  published. Any repack span or length fault from the E144 edits will show up there. [Tester page](docs/OM5_PREALPHA.md).

- **Pre-alpha 1 failed on a tester's original OM-5** (17 Nov 2026): black screen, silent. OM's 1.2 was restored
  from the card. The alpha2 donor's startup defect and the transplant itself are both possible causes.
  [Report](research/OM5I-PREALPHA1-CAMERA-2026-11-17.md).

## v0.2.0 development (`claude/sharp-cray-0up4d3`)

- Plan: [docs/V0.2.0-PLAN.md](docs/V0.2.0-PLAN.md).
- **Film Grain for Color Profiles (emulator only).** Current dev package `24f243a0…a373` (grain + inert
  Blacks/Whites; not a release, never flashed). [Note](research/OM5II-CP-GRAIN-2026-11-18.md). Open on the
  camera: grain in colour JPEGs; Reset turns it Off; C1..C5 keep it.
- **v0.2.0 priorities (owner): Blacks / Whites, split toning, Clarity**, each per Color Profile, all in one
  tested build before an alpha. Blacks / Whites image side is built and emulator-checked (`tests/bw_assert.mjs`)
  but inert: no storage, refresh or camera controls yet. Next steps are in [the plan](docs/V0.2.0-PLAN.md).
  [Note](research/OM5II-BLACKS-WHITES-2026-11-18.md).
- Codex's Ghidra tooling and findings are merged from main
  ([findings](research/OM5II-GHIDRA-FINDINGS-2026-11-18.md)). The stock reset, init and custom-mode copy lists
  include 907/911/915, which grain uses; all default to 0 (= Off).
- `firmware/om5ii` on this branch is no longer the alpha12 source. The original OM-5 builder's donor on this
  branch is therefore not alpha12; use `main` for E144 work.

## Next camera checks

1. Capture per-step filter and CP results with the installed package SHA-256.
   [Checklist](docs/FIRST_FLASH.md#alpha12-camera-checks).
2. Per-profile WB, JPEG colour output and ND exposure still need documented camera checks.

## Development

- Read-only analysis tooling is on `codex/ghidra-analysis`, from tooling commit
  `3803ff8`. [Setup and queries](tools/ghidra/README.md). The private saved project
  is `generated/ghidra/projects/E148-1100.gpr`: full analysis took 637 seconds
  including startup/fix/save; 50,430 functions after six follow-up callback seeds.
  Space-map pointer hits now reserve target byte ranges, preserving ext5/ext10
  tails; pointee extents and runtime ownership still need review.
- [Ghidra findings](research/OM5II-GHIDRA-FINDINGS-2026-11-18.md): gamma stage
  `0x603e69ae`, RGB setter `0x603e6974`, luma LUT stage `0x603e863e` identified
  statically. Stock reset/store-copy paths write IDs 907/911/915. Soft Focus flag
  reader `0x6038d263` located; its weight getter remains unidentified.
- [Static heap findings](research/OM5II-HEAP-ALLOCATOR-2026-11-18.md): E148
  allocation `0x60023818`, free entry `0x6002384a`; the existing linker comment's
  `0x6002385f` is an interior instruction. A pinned Ghidra import/xref smoke test
  passed; full auto-analysis is complete, heap runtime validation remains pending.
  This branch changes no firmware, installer or release files.

- Official E148 1.1 SHA-256 starts `9de5d77e`. Use GNU `mn10300-elf` tools and
  OM-Emu `xulfr/om-emu` branch `fix/e148-ipi-stride`, commit
  `bdb33470705b3be28db52cbe080c31d74db727d8`.
- [AGENTS.md](AGENTS.md), [docs/INDEX.md](docs/INDEX.md), and [docs/TESTING.md](docs/TESTING.md).
  The owner performs all camera updates.
