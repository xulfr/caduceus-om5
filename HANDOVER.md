# OM-5 firmware development: current handover

## Known-good baseline

The owner reported that v0.1.0-alpha8 boots on an OM-5 Mark II (E148, stock firmware 1.1), with selected
colour-profile, HSL, tone and Live ND functions. It is not a general safety or compatibility certification.

- research/OM5II-ALPHA8-CAMERA-2026-11-15.md
- releases/v0.1.0-alpha8/patch.json
- tests/alpha8-results.json

The UI candidate `ae96e94` (package `7ba9aba0…b92508`) was also flashed by the owner (icons and ND labels).

## Active work: alpha9 candidate (16 November 2026)

Branch `claude/pensive-hamilton-pg8dpr`, with `main` merged (`96d2c5c`). **Emulator only; not camera-tested.
Not released.** The owner asked for this to become the next official alpha (v0.1.0-alpha9) with a PR to main,
README and Pages refresh and new screenshots. That work is **not done**; see Next actions.

Strict source build package SHA-256: `43b0e367a7fed8ac968041f4fc9837a9786c4684456c0b70dd195d68ad962c1d`.

Contents on top of alpha8: UI candidate fixes, WIP UI candidates 2 and 3 (colour wheel and tone curve drawn on
the OSD plane), and `7f53058`: the Tone Curve row icon in all 27 tone states. Details of candidates 2 and 3:
docs/archive/HANDOVER-ui-candidates-2026-11-16.md, research/OM5II-WIP-UI2-2026-11-16.md, OM5II-WIP-UI3-2026-11-16.md.

### Tone Curve row icon (`7f53058`)

- The row asks for image `0x38cc` when Shadows / Midtones / Highlights are 0 and `0x38cd..0x38e6` otherwise
  (traced per state with `tools/dev/imgwatch.mjs`). Only `0x38cc` was aliased, so the icon vanished after any edit.
- Order: Midtones 0, then +, then −; within each (Sh, Hi) = (+,+) (+,−) (−,+) (0,+) (−,−) (0,−) (+,0) (−,0),
  then (0,0) last in the two Midtones groups. E148's Highlight & Shadow glyphs `0x2ae0..0x2af9` have the same order.
- Aliases: `0x38cd+k → 0x2ae0+k` (k = 0..25), `0x38cc → 0x20a` (stock gradation "Norm" icon).
- Resource record 0 pointer words only (packed 764,848 bytes, length rule passes). The main program is
  byte-identical to candidate 3.

### Checks

On candidate 3 (`62ff6d21…1425`, same main program), OM-Emu `bdb3347`, all passed: strict build, static rules,
`tests/run_emulator.py` (all cases, no image stores beyond stock), startup probe (image stores equal stock),
inert / applied gating, unarmed PC scan, stale profile number, `run_ui_activity.py` 10/10,
`run_page_graphics.py` 10/10 (after correcting one expectation: a block's edge hides the next scale dot),
six Live ND label cases, host suite with `OM5_STOCK`, `audit_build.py` against candidate 2.

On the current build (`43b0e367…2c1d`): strict build, `tests/run_tone_icons.py` (27 states, 27 icons; fails on
candidate 3 as intended). **Not yet run on it:** the full suite above and `audit_build.py` against candidate 3
and alpha8. Run them before any release or camera test.

## Known defects (OM-Emu)

- **Shooting screen shows no Picture Mode icon once a profile is edited or holds a look.** Unedited Color
  Profile 1 asks for `0x3d62` (artwork, shown); edited it asks for `0x3d66` (placeholder). Expected, unconfirmed:
  `0x3d66..0x3d68` for Color 1–3 and `0x3d5e..0x3d60` for Monochrome 1–3. Fix: add them to the artwork sprite
  `ids` in firmware/om5ii/patch.json; record 0 then needs a new LZ4 recipe (`oly_resource_recipe.py` only handles
  `aliases`, so extend it), re-record, rebuild, audit.
- Monochrome Profiles: Color Filter row icon (`0x38cb`) and Film Grain row / strip icons (`0x38e7..0x38ee`) are
  placeholders; the Color Filter page shows a stray "Vivid" label. Present since alpha8.
- ND64 shooting label digits are squashed (resampled artwork). ND32 has a gap between digits.
- Not a defect: the selected row loses its outline after a dial turn; stock does the same in OM-Emu.
- Wheel and curve are block graphics, not OM-3's artwork. Palette and OSD command budget unverified on camera.

## Next actions

1. Fix the edited-profile shooting icon (above); decide on the Monochrome icons.
2. Run the full suite on the final build; record results in tests/alpha9-results.json and a build audit.
3. Release: `tools/mkrelease.py v0.1.0-alpha9 BUILD STOCK`, `camera_tested` false, no `camera_status`, copy
   LOOKS.BIN, update tests/test_release.py, CHANGELOG.md, README.md, docs, site banners; keep the warnings and say
   plainly that alpha9 has not run on a camera and alpha8 is the last boot-confirmed build.
4. New screenshots in pages/showcase/img from the release build with the starter LOOKS.BIN (frames are Y/Cb/Cr
   in the PNG's R/G/B: convert with PIL `Image.merge('YCbCr', …)`). Current images are outdated.
5. Restyle index.html and tools/mksite.py output after androidfanman/caduceus-om3's current site, then `python
   tools/mksite.py`.
6. Open the PR to main. Owner camera checklist: docs/archive/HANDOVER-ui-candidates-2026-11-16.md, plus the Tone
   Curve icon in several states and the shooting-screen icon after loading a look.

## Workspace

- Stock E148 1.1 (`9de5d77e…d637`) and `binutils-2.43.tar.xz` are in the owner's lab folder
  (`CameraFirmwareLab/firmware/user-om5ii`, `tools-local/mn103`); cloud sessions cannot reach OM's or GNU's servers.
- binutils: `configure --target=mn10300-elf --disable-nls --disable-werror --disable-gdb`, then
  `make MAKEINFO=true` and `make MAKEINFO=true install` (the variable must be a make argument).
- OM-Emu: `xulfr/om-emu`, branch `fix/e148-ipi-stride`; Node 22 works.
- `IMG_LO=3800 IMG_HI=3a00 PRE=tools/dev/imgwatch.mjs bash tools/dev/run.sh BUILD OUT 'keys'` prints every
  image-table read (`IMG id pc`) before each step line; pc `0x60d8e57e` is a draw.

## Workflow and evidence rules

AGENTS.md, docs/INDEX.md, docs/TESTING.md. `python scripts/check.py fast|integration|full`.
Emulator-tested does not mean camera-tested. The owner performs all camera updates. Do not change release
safety status without a camera report linked to the exact package hash.
