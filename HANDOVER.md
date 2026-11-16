# OM-5 firmware development: current handover

## Known-good baseline

The owner reported that v0.1.0-alpha8 boots on an OM-5 Mark II (E148, stock firmware 1.1), with selected
colour-profile, HSL, tone and Live ND functions. It is not a general safety or compatibility certification.

- research/OM5II-ALPHA8-CAMERA-2026-11-15.md
- releases/v0.1.0-alpha8/patch.json
- tests/alpha8-results.json

The UI candidate `ae96e94` (package `7ba9aba0…b92508`) was also flashed by the owner (icons and ND labels).

## Active work: v0.1.0-alpha9 (16 November 2026)

Branch `claude/pensive-hamilton-pg8dpr` (main merged at `96d2c5c`). **Emulator only; not camera-tested.** Release
files are in releases/v0.1.0-alpha9 (`camera_tested` false, no `camera_status`); the installer's default is now
alpha9 and asks for `UNTESTED`. Not merged to main; no PR opened yet. Package SHA-256
`2e9777ce08163fa6e4a97930683cd8eb0ce73197dfd5ac4a64d8928af98fbc50`. Main program identical to candidate 3.

On top of alpha8: UI candidate fixes, WIP UI candidates 2 and 3 (colour wheel and tone curve drawn on the OSD
plane), the Tone Curve row icon in all 27 tone states (`7f53058`) and the edited-profile shooting-screen icon
(`96bd3c0`). Details of candidates 2 and 3: docs/archive/HANDOVER-ui-candidates-2026-11-16.md,
research/OM5II-WIP-UI2-2026-11-16.md, OM5II-WIP-UI3-2026-11-16.md.

### Edited-profile icon (`96bd3c0`)

- Traced with `tools/dev/imgwatch.mjs`: once a profile is edited the Picture Mode screen and the shooting screen
  ask for `0x3d66..0x3d68` (Color 1–3) and `0x3d5e..0x3d60` (Monochrome 1–3) instead of `0x3d62..0x3d64` /
  `0x3d5a..0x3d5c`. All six are stock placeholders. Carousel positions: `right` ×8..13 after `s1 ok ok`.
- Added to the existing artwork sprites (same bitmap as the unedited ID). Record-0 recipe re-recorded with
  `tools/oly_resource_recipe.py --artwork ANCHOR=TARGET` (new option): packed 764,886 bytes, same window.
- `tests/audit_build.py` now accepts artwork sprite IDs, and requires all IDs of one sprite to share a bitmap.
- `tests/run_profile_icons.py`: passes on alpha9, fails on `43b0e367` as intended.

### Checks (alpha9 build, OM-Emu `bdb3347`): tests/alpha9-results.json

All passed: strict build, 19 look/menu cases (no image stores beyond stock), startup probe (stores equal stock),
inert / applied gating, unarmed PC scan, stale numbers, UI activity 10/10, page graphics 10/10, tone icons 27/27,
profile icons 6/6, Live ND labels 6/6, static rules, host suite with `OM5_STOCK` (alpha1–alpha9 reproduce),
`audit_build.py` against candidate 3 (tests/alpha9-build-audit.json).
**Not a pass:** `audit_build.py` against alpha8 refuses by design (record 37 artwork added since alpha8; candidate 3
fails the same way). Extending the audit to verify record 37's appended artwork would close this.

### Site and docs

README, CHANGELOG, Install, Safety, FAQ, Roadmap, the camera checklist (steps 9–14 for alpha9) and all banners say
alpha9 has not run on a camera and how to make alpha8 (`python3 patch.py --release v0.1.0-alpha8`). Tour and guide
pages restyled after androidfanman/caduceus-om3 (`3e5c7e5`); screenshots in pages/showcase/img from the alpha9
build with the starter LOOKS.BIN (`38bd927`). LookLab still uses pages/site/site.css.

## Known defects (OM-Emu)

- Monochrome Profiles: Color Filter row icon (`0x38cb`) and Film Grain row / strip icons (`0x38e7..0x38ee`) are
  placeholders; the Color Filter page shows a stray "Vivid" label. Present since alpha8.
- ND64 shooting label digits are squashed (resampled artwork). ND32 has a gap between digits.
- Not a defect: the selected row loses its outline after a dial turn; stock does the same in OM-Emu.
- Wheel and curve are block graphics, not OM-3's artwork. Palette and OSD command budget unverified on camera.

## Next actions

1. Owner review; then open the PR to main (owner approval needed to publish the release).
2. Owner camera check of the alpha9 package: docs/FIRST_FLASH.md steps 0–3, then 9–14. Record the result with the
   package hash before changing any release status.
3. Monochrome Color Filter / Film Grain icons; ND64 / ND32 digit artwork.
4. Optional: let `audit_build.py` verify record 37's appended artwork so builds can be audited against alpha8.

## Workspace

- Stock E148 1.1 (`9de5d77e…d637`): cloud sessions on 16 November 2026 could fetch it with `patch.fetch_stock`
  (OM's server) and binutils from ftp.gnu.org. Also in the owner's lab folder (`CameraFirmwareLab/...`).
- binutils: `configure --target=mn10300-elf --disable-nls --disable-werror --disable-gdb`, then
  `make MAKEINFO=true` and `make MAKEINFO=true install` (the variable must be a make argument).
- OM-Emu: `xulfr/om-emu`, branch `fix/e148-ipi-stride`; Node 22 works.
- `IMG_LO=3800 IMG_HI=3a00 PRE=tools/dev/imgwatch.mjs bash tools/dev/run.sh BUILD OUT 'keys'` prints every
  image-table read (`IMG id pc`) before each step line; pc `0x60d8e57e` is a draw.

## Workflow and evidence rules

AGENTS.md, docs/INDEX.md, docs/TESTING.md. `python scripts/check.py fast|integration|full`.
Emulator-tested does not mean camera-tested. The owner performs all camera updates. Do not change release
safety status without a camera report linked to the exact package hash.
