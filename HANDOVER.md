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

## v0.2.0 development (`claude/sharp-cray-0up4d3`, fixes on `claude/wizardly-feynman-wejd65`)

- Plan: [docs/V0.2.0-PLAN.md](docs/V0.2.0-PLAN.md).
- **Camera, 2026-11-20, dev package `4f7aeb6c…4636`: boots and works** (owner). Black / White work in pictures but,
  like the tints, reach live view only after a half-press; labels still too large, hint text overflowed; "all" on a
  tint axis still selectable but only one colour moves. The same source plus cg1 (`f7f1db5d…2c51`) boot-looped, so
  cg1 / its carousel edit caused that. **Owner: colour grain shelved; this branch is the base for the next alpha.**
  [Report](research/OM5II-DEV4F7A-CAMERA-2026-11-20.md), cg1 report on `claude/cp-grain-experiment`.
- **Camera, 2026-11-20, package `0565540a…de73`: works** (labels, live view). The first flash attempt failed (file on
  the card not SHA-checked; suspected copy corruption, unconfirmed); the second, after a SHA-256 check, worked. The cg1
  boot loop was also flashed unchecked, so its cause is not certain. Remaining: Highlight Tint showed nothing; the
  colour wheel's selected-colour swatch changed every second colour; "Bl/Wh" drawn over OM's "Hi/Sh INFO".
  [Report and fixes](research/OM5II-DEV0565-CAMERA-2026-11-20.md) (dev package `9b14e1ce…95c9`, not flashed).
- **Fixes since (emulator only, not flashed):** Bl / Wh title images from OM's glyphs + OM's own ±n images + "Bl/Wh
  INFO" hint ([tone page note](research/OM5II-TONE-PAGE-2026-11-19.md)); live view: `gs_hook` makes each gamma-stage
  cache miss once after Black / White or tint tables change ([note](research/OM5II-LIVEVIEW-GAMMA-CACHE-2026-11-20.md)).
- **Camera, 2026-11-19, package `7d611008…1c7f`** (the earlier `…8c7f` was a typo): boots and works. Split tone
  works (live view and JPEG). Black / White: UI only, no effect in pictures. Colour grain: no grain at any level,
  carousel order reversed. "All" on a tint axis changed a seemingly random colour. Black / White labels larger than
  Sh / Hi. [Report](research/OM5II-V020DEV-CAMERA-2026-11-19.md).
- **Fixes on `claude/wizardly-feynman-wejd65`** (dev package `4f7aeb6c…4636`, emulator only, never flashed):
  - Black / White now go into the split-tone R/G/B delta tables (the route the camera showed working); the
    brightness-curve hooks are removed. [Note](research/OM5II-BLACKS-WHITES-2026-11-18.md).
  - Tint axes stay on one colour: arriving with "all" switches back, INFO there does nothing.
  - Picture Mode stays open 30 s after the last key, dial or tap (9 stock timer arms + Caduceus's own re-arm;
    `firmware/om5ii/pm_timeout.py`; OM-Emu `tap:X,Y` in tools/dev/sess.mjs).
  - Black / White labelled Blk / Wht (superseded 2026-11-20 by Bl / Wh images).
  - **Color Profile grain removed** (owner): it showed no grain on the camera; stock grain is monochrome-only.
    Image-pipeline work continues on `claude/cp-grain-experiment`. [Note](research/OM5II-CP-GRAIN-2026-11-18.md).
- Black / White on the tone page: INFO steps Hi/Sh → Black/White → Mid on Color Profile 1–3; −7..+7 per profile.
  [Tone page internals](research/OM5II-TONE-PAGE-2026-11-19.md). Split tone: trash steps on to Shadow / Midtone /
  Highlight Tint; one of 12 colours, strength 1..5. [Note](research/OM5II-SPLIT-TONE-2026-11-19.md).
- Space is used up again (about 30 bytes left in the tails). This build also uses the FF tails of sections 3 and 9
  for the first time; the 15 new descriptors are built in the heap at arming.
- Clarity is blocked on the Soft Focus weight getter. Free space is nearly gone (see [the plan](docs/V0.2.0-PLAN.md)).
- Ghidra is not set up in the current container; rebuild per tools/ghidra/README.md (about 15 minutes). OM-Emu
  `xulfr/om-emu` branch `fix/e148-ipi-stride` (`bdb3347`) and binutils 2.42 rebuild as in docs/OM5_PREALPHA.md.
- Codex's Ghidra tooling and findings are merged from main
  ([findings](research/OM5II-GHIDRA-FINDINGS-2026-11-18.md)). The stock reset, init and custom-mode copy lists
  include 907/911/915 (used by the removed Color Profile grain); all default to 0.
- `firmware/om5ii` on this branch is no longer the alpha12 source. The original OM-5 builder's donor on this
  branch is therefore not alpha12; use `main` for E144 work.

## Current priorities (owner, 2026-11-20)

1. **Intermittent boot loop on `0565540a`** (power cycle recovers; not reproducible on demand). Find the cause
   before more features. [Report](research/OM5II-DEV0565-CAMERA-2026-11-20.md#later-the-same-day-owner).
2. Colour wheel INFO: switch between HSL and Tint axes (with its hint label), instead of the misleading "Color All".
3. Separate split-tone row abandoned (`claude/split-tone-row`, note only). Work continues on this branch, not `main`
   (main is alpha12, the original OM-5 builder's donor).

## Next camera checks

000. **Dev package `9b14e1cea7a30826628a7914468b1f350a42174754aedd67f3739264abf295c9`** (check the card file's
   SHA-256 before flashing). Highlight Tint visible on bright areas; shadow / midtone tints and Black / White now act by
   output brightness (different feel); swatch top right follows every colour; tone hint "Bl/Wh INFO" in Hi/Sh, OM's
   "Hi/Sh INFO" untouched in Mid.
00. **Dev package `0565540a52e09e483573bf59e1d4a62946db944a6364a9a605c4ee8b4a94de73`** (works, 2026-11-20) (branch
   `claude/wizardly-feynman-wejd65`; `4f7aeb6c` + labels + live-view fix; new: hook at `0x603e6a3b` in the gamma stage,
   ext8 code, resource images `0x3e80..0x3e82`, P 1544 bytes). Boots? Then: Black / White and each tint change live
   view **without** a half-press (also back to 0, and leaving to a stock mode clears the tint at once); tone page shows
   "Bl ±n" / "Wh ±n" at the size of Sh / Hi and "Bl/Wh INFO" fits its frame; Sh / Hi / Mid unchanged; no slowdown or
   flicker in live view. `check.py full` passed (base emulator suite 19/19, build audit), `run_bw_tint.py` 13/13.
0. **Dev package `4f7aeb6c…4636`** (flashed 2026-11-20: boots; see the report). Black / White −7 / +7 visibly change
   live view and JPEGs (both ends; no colour cast) and nothing at 0, alone and together with a tint. Colour wheel:
   INFO on a tint axis stays on one colour; "all" on Saturation then trash to a tint returns to one colour. Picture
   Mode stays open about 30 s after the last key, dial or tap, on the strip, tone page and colour wheel; other menus and
   the super control panel still close after 8 s. Color Profiles show six sidebar rows (no Film Grain);
   Monochrome Film Grain still works. Then: Reset, C1–C5 and power-off keep / clear values as expected.

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
