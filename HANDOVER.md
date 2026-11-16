# OM-5 firmware development: current handover

## Known-good baseline

- **v0.1.0-alpha9** (`2e9777ce…fbc50`): the owner reported boot and a working CPU-drawn colour wheel on an
  OM-5 Mark II (E148, stock 1.1) on 16 November 2026; made with the branch installer while alpha9 was its newest release (owner confirmed),
  so the package is `2e9777ce…fbc50`. `camera_status: boot-confirmed`. research/OM5II-ALPHA9-CAMERA-2026-11-16.md.
- v0.1.0-alpha8 (`709ca9d4…3b68`): boot, Color Profiles, looks and Live ND32/64. research/OM5II-ALPHA8-CAMERA-2026-11-15.md.

## Active work: v0.1.0-alpha10 (17 November 2026)

Branch `claude/pensive-hamilton-pg8dpr`. **Emulator only; not camera-tested.** releases/v0.1.0-alpha10 re-cut with the
colour filter picker and the CP "any item" fix: package `056aefb3c3f40b7cf41728cd9f466ba161a52d887db6ecebd2f0377bb0a38454`
(`camera_tested` false; the earlier candidate `1530ca05…` is superseded). Owner opens the PR to main.

**Unfinished at handover (usage limit):** (1) the 19 look/menu cases (`tests/run_emulator.py`) were at 15/19 passed
on the re-cut build; (2) `unarmed_pcs.py` verdict; (3) host suite `python -m unittest discover -s tests` with
`OM5_STOCK`. Re-run these three, then fill `tests/alpha10-results.json` (fields marked PENDING). Everything else in
the suite passed on the re-cut build (startup, image stores = stock, gating, stale numbers, static rules, UI
activity, page graphics, tone/profile icons, profile rows, mono filter, Live ND labels 6/6, audits vs alpha9/alpha8).

New in this re-cut (research/OM5II-MONO-FILTER-CP-2026-11-17.md):
- **Colour filter picker**: the page (child 3, flag +246, view `0x610d9b20`) already stepped 1007+p in OM-Emu
  (the old note tested only the main dial). hsl.s `paint_filter`/`gfx_filter` draw an 8-block ring in the OM-3's
  dial order + "Level" text; `pg_axis` invalidates child 3. cp_nd.py hides image `0x107e` "Vivid" and moves the
  dial icon / "+n" 10 px. Test: `tests/run_mono_filter.py` (+ `tests/store_log.mjs`).
- **CP any item**: `cp_any_hook` 0x60d22357 → `cp_any_nd` (k 5, then k 6, 7 when armed). Static analysis only.
- OM-3 reference: E147 1.1 SHA-256 `8c133084…696d`; Creative Dial = UI_IN group 5 code `0x1906` (position 0 MONO).

Fixes from the alpha9 report (`49a85cf`):
- **Color Profile Shading** 912..914 had no setting descriptor (OM's 1589 static descriptors at `0x6050dad4`,
  stride 20: id, 0x80, value list, 0, list bytes, element size, flags), so the slider drew grey and the writer
  dropped changes. cp_nd.py adds copies of 1017's descriptor; `cp_nd_link` links 5 descriptors after arming;
  P grows 1024 → 1040 bytes (nodes P+988..1027).
- **CP button ND32/64**: the CP carousel (GUI `0x60e27d22`) lists the allowed values of setting 2228 (current
  item, 1 + k of table `0x60f7f57c`), stock 1..6, 14..17. Descriptor `0x60515694` now points at 1..8, 14..17
  (`0x604f2554`). Static analysis only (no CP button in OM-Emu). Still open: "any item ticked" `0x60d2230f` skips
  k 6..12.
- **Monochrome icons**: Film Grain value v uses `0x38e7+2v` (selected, also the sidebar) and `0x38e8+2v`; aliased to
  Off `0x2a2a`, Low `0x2a3b`, Std `0x2a3c`, High `0x2a3d`. Color Filter row `0x38cb` (one image for all values) is a
  sprite cropped from `0x216` ("Filter"). Type-14 image records point at their pixels (header +16); do not assume
  the pixels follow the header (my first contact sheet did, and picked neighbouring glyphs).
- Tools: `oly_resource_recipe.py --sprite`, record-37 recipe re-recording, greedy LZ4 window when OM's sequences
  overflow record 0 (span 764,928; now 764,852 packed). `audit_build.py` rebuilds the resource block from stock and
  patch.json and then accepts record-37 changes, so audits against alpha8 work.

Checks on the earlier candidate `1530ca05…` (re-cut status above): all 19 look/menu cases, startup (after fixing the probe's guard
band for the 1040-byte block), gating, unarmed PCs, stale numbers, UI activity, page graphics, tone icons, profile
icons, `run_profile_rows.py` (new), Live ND labels, static rules, audits vs alpha9 and alpha8, release reproduction.

## Investigated, not changed

- **Per-profile white balance** exists since alpha1 (wb.s): the camera's usual WB is stored per Color Profile and
  restored on selection. It is not a Picture Mode row. Emulator checks only; checklist step 18. README clarified.
- **Colour grain for Color Profiles**: deferred with the other effects (needs a row and storage); roadmap.

## Known defects (OM-Emu)

- ND64 shooting label digits squashed; ND32 gap between digits.
- Not a defect: the selected row loses its outline after a dial turn (stock does the same in OM-Emu).

## Next actions

1. Owner camera check of alpha10 (`056aefb3…8454`): docs/FIRST_FLASH.md steps 0–3, 9–20 (Shading, CP-button ND32/64, Monochrome
   icons, per-profile WB). Record the package hash with the report.
2. Owner: open the PR to main (release approval is the owner's).
3. Finish the pending checks above. ND digit artwork.

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
