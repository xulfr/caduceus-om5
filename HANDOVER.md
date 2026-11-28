# OM-5 firmware development handover

## Camera baseline

- **v0.2.0-alpha1, OM-5 Mark II 1.1**: the owner reports the candidate from c3bc45c works perfectly (20 November). See [release notes and package checksum](releases/v0.2.0-alpha1/README.md).

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
  tint axis still selectable but only one colour moves. The same source plus cg1 (`f7f1db5d…2c51`) boot-looped after an unchecked card copy;
  its cause is uncertain. **Owner: colour grain shelved; this branch is the base for the next alpha.**
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
- **Fixes on `claude/wizardly-feynman-wejd65`** (dev package `4f7aeb6c…4636`, owner flash reported above):
  - Black / White now go into the split-tone R/G/B delta tables (the route the camera showed working); the
    brightness-curve hooks are removed. [Note](research/OM5II-BLACKS-WHITES-2026-11-18.md).
  - That build kept tint axes on one colour. The current INFO group switch supersedes its INFO handling.
  - Picture Mode stays open 30 s after the last key, dial or tap (9 stock timer arms + Caduceus's own re-arm;
    `firmware/om5ii/pm_timeout.py`; OM-Emu `tap:X,Y` in tools/dev/sess.mjs).
  - Black / White labelled Blk / Wht (superseded 2026-11-20 by Bl / Wh images).
  - **Color Profile grain removed** (owner): it showed no grain on the camera; stock grain is monochrome-only.
    Image-pipeline work continues on `claude/cp-grain-experiment`. [Note](research/OM5II-CP-GRAIN-2026-11-18.md).
- Black / White on the tone page: INFO steps Hi/Sh → Black/White → Mid on Color Profile 1–3; −7..+7 per profile.
  [Tone page internals](research/OM5II-TONE-PAGE-2026-11-19.md). Split tone: INFO enters Tint and trash cycles Shadow / Midtone /
  Highlight Tint; one of 12 colours, strength 1..5. [Note](research/OM5II-SPLIT-TONE-2026-11-19.md).
- At `c3bc45c` the linker leaves 15 bytes in ext2 before the WB gate, 16 in ext7, and 18 in ext8 before the WB helper.
  The build also uses the FF tails of sections 3 and 9. The 15 new descriptors are built in the heap at arming.
- Clarity is blocked on the Soft Focus weight getter. Free space is nearly gone (see [the plan](docs/V0.2.0-PLAN.md)).
- Ghidra is not set up in the current container; rebuild per tools/ghidra/README.md (about 15 minutes). OM-Emu
  `xulfr/om-emu` branch `fix/e148-ipi-stride` (`bdb3347`) and binutils 2.42 rebuild as in docs/OM5_PREALPHA.md.
- Codex's Ghidra tooling and findings are merged from main
  ([findings](research/OM5II-GHIDRA-FINDINGS-2026-11-18.md)). The stock reset, init and custom-mode copy lists
  include 907/911/915 (used by the removed Color Profile grain); all default to 0.
- `firmware/om5ii` on this branch is no longer the alpha12 source. The original OM-5 builder's donor on this
  branch is therefore not alpha12; use `main` for E144 work.

## Background arming and the card block (branch `ccr-568c4ae0-gogwt3`, 2026-11-27, emulator only)

- **Owner priority:** fast start-up and no half-press. `boot.s` hooks `FastEndCb` (`0x601b1362`, OMKit's site),
  which only creates a low-priority task. The task waits for `0xa26e2694`, allocates P, reads `LOOKS.BIN` and then
  `OM5MOD/CADUCEUS.BIN`. The settings-writing refresh stays at the first half-press. OK held at switch-on skips it.
  **This replaces alpha7's "nothing before the first half-press" rule**, so it needs a careful camera check of
  start-up (with and without a card, Wi-Fi, USB, sleep).
  [Note](research/OM5II-BACKGROUND-ARM-2026-11-27.md).
- **Card block:** the page graphics (about 1 KB) moved to `CADUCEUS.BIN`, loaded into the unused DRAM gap past
  resource record 0 (`0xa3700000`, OMKit's camera-tested arena) and checked against the build.
  `patch.py` / `mkrelease.py` ship it. [Note](research/OM5II-CARD-BLOCK-2026-11-27.md).
- **Tests:** `tests/run_boot_arm.py` 11/11, page graphics 11/11, mono filter pass (OM-Emu).

## OM-3 parity, phases 1–2 (branch `ccr-6992778b-4fybdu`, 2026-11-28, emulator only)

- **Phase 1 research:** borrow Color Creator's GPU drawing as OMKit does; go as a switchable probe (g1: a calibration
  picture behind `OM5MOD/GPU.ON`). OM-Emu shows our pages order the drawing after one panel write.
  [Note and build plan](research/OM5II-OMKIT-GPU-EDITORS-2026-11-28.md). Supersedes the c3d note's "keep CPU drawing".
- **Phase 2 keys:** INFO steps H → S → L, Sat. All on the colour (rear) dial past colour 1, skipped on Hue / Lightness,
  Delete inert on the wheel, "H/S/L [INFO]" hint. New pointer site `0x61211cf4`. `tests/run_wheel_keys.py` 9/9.
  **The tints have no key until phase 3** (stored tints still apply): do not flash phase 2 without phase 3.
- Pre-existing: `run_ui_activity.py` case `idle` fails on `main` too (the screen stays open past 17.5 s).

## Look defaults (merged, PR #14; emulator only)

- Hold OK returns a look slot's values to the look, and the Reset OK Hold hint follows the look
  ([note](research/OM5II-LOOK-DEFAULTS-2026-11-27.md)). GPU wheel: keep CPU drawing
  ([note](research/OM5II-C3D-GPU-WHEEL-2026-11-27.md)). More room: [options](research/OM5II-CARD-CODE-OPTIONS-2026-11-27.md).

## Current priorities (owner, 2026-11-20)

1. **Intermittent boot loop on `0565540a`**. Power cycling recovers it. The old gamma hook demonstrably entered
   section 8 before checking readiness. The candidate keeps the unarmed gamma path in section 2 and the tone-view
   gate in section 7. The cause of the physical reset remains unconfirmed.
   [Comparison and boot evidence](research/OM5II-DEV0565-CAMERA-2026-11-20.md#startup-comparison-and-wheel-fix-2026-11-20-emulator-only).
2. Wheel keys: superseded 2026-11-28 by the OM-3 v0.41 key map (see above).
3. Colour grain is shelved. The separate split-tone row is abandoned. Keep this work on
   `claude/wizardly-feynman-wejd65`. Main is the alpha12 donor for the original OM-5.

## Next camera checks

- **E148 1.1 alpha1 `c3bc45c`, owner reports overall success**. Verify the SHA-256 of **the file on the card** before flashing:
  `2b3fd53ce24433edb662036a29e1f4ea3988c61f9a15d681f0998ebe7b4a21e6`.
  The owner confirmed `9b14e1ce…95c9` was never flashed.
- Candidate validation: `check.py full` passed (48 host tests passed, one E144-only skip, strict build,
  19/19 emulator cases and build audit). Tone/tint 14/14, page graphics 11/11, startup fault injection
  and the no-half-press PC trace passed. Firmware behaviour is emulator only.
- Record successful and failed starts, the mode at shutdown, and any power-cycle recovery. Check live view
  after Black / White and tint edits and after clearing them. Record whether a half-press was needed.
- On the wheel, check the INFO label in both groups, all three trash positions in each, and the 12-colour
  swatch. Check Highlight Tint on a bright subject and the Bl/Wh hint on the tone page.
- Prior checks still open include Black / White in JPEGs at both limits and zero, the 30-second Picture Mode
  timeout versus 8 seconds elsewhere, and persistence across Reset, C1–C5 and power-off.

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
  Those allocator findings came from a read-only investigation.

- Official E148 1.1 SHA-256 starts `9de5d77e`. Use GNU `mn10300-elf` tools and
  OM-Emu `xulfr/om-emu` branch `fix/e148-ipi-stride`, commit
  `bdb33470705b3be28db52cbe080c31d74db727d8`.
- [AGENTS.md](AGENTS.md), [docs/INDEX.md](docs/INDEX.md), and [docs/TESTING.md](docs/TESTING.md).
  The owner performs all camera updates.
