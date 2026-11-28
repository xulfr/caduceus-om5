# Phase 4 scoping: new image controls on the OM-5 Mark II (2026-11-28)

**Planning note. Nothing built.** Sources: the OM-3 project's notes (`androidfanman/caduceus-om3` `try/v0.41-beta4`,
research/NOTES.md), OMKit's E148 1.1 docs (CC BY 4.0) and this project's own notes. OM-3 results are for the OM-3
(E147); OMKit's are for OMKit's build. Neither is evidence for this build on the OM-5 Mark II.

## What phase 4 contains ([roadmap](../docs/OM3-PARITY-ROADMAP.md))

| Item | OM-3 (as built there) | What it needs here | Risk |
|---|---|---|---|
| **Sharpness −5 (off) .. +2** | v0.22 "Sharp": the stills capture read (key `0x8119`) is hooked; −5 is sent as −7 (off); the slider row gets 11 steps | E148's capture read of sharpness: OMKit records the shooting parameters' sharpness at `S+28694` (u16, camera, for OMKit) and the stills detail block `0x1800` (sharpening, noise filter) reading it. To trace: what range the detail block accepts and what "off" is on E148. UI: the Sharpness row's slider from 5 to 11 steps (our rows note lists the slider style / value-label lookups `0x60e4b02c` / `0x60e4b09d`) | Image path; small UI. Photos only (OM-3: live view keeps the camera's value) |
| **WB Compensation row** | A row; OK opens the camera's WB grid; each film keeps its A-B / G-M | Per-profile WB mode, Kelvin and shift exist here already (not camera-checked). Needs a row (the Split toning row shows how: OM's own editor reused, or a slider row) and the grid's entry from Picture Mode | UI; the per-profile WB itself is still unchecked on the camera |
| **RGB curves** | 5 points × R / G / B, −7..+7, in split toning's pass; model `research/rgbcurves/model.py` (test 4: points at 0 / 25 / 50 / 75 / 100 %, step 48) | The image side is our camera-proven R / G / B curve route (`tn_tables` / `st_tint`): add the curve to the same delta tables. 15 values per profile (45 cells), the storage question in the roadmap. A row with an editor for 15 values (OM-3: R / G / B by INFO, five points by the dials) | Mostly UI and storage; image side low (same route) |
| **Color Mix** | R, G, B moved toward their neighbours in linear light after the WB gains (ours × its colour matrix, before gamma), greys kept | Its own hook at the E148 colour matrix. OMKit documents the matrix builder `0x603e509a` and row normalisation `0x603e4f0c` (rows sum to 128), and its own matrix route (`ispdrv.c`, camera, for OMKit) | Image path, new hook site; needs a static trace first |

## Constraints found this session

- **Flash room is nearly gone.** After phases 2–3: `.ext2b` 31 bytes free, `.ext2c` ~50, `.ext3` 44, `.ext5` 56 after
  Balance, `.ext6` 33, `.ext7` 28, `.ext8` 38, `.ext9` ~10, `.ext10` ~90. Every phase 4 item needs more. UI and table
  code that runs only once armed should move into `OM5MOD/CADUCEUS.BIN` (64 KiB, PR #15). That is the enabler, and the
  first task of phase 4.
- **Rows.** The Split toning row showed that a row can be OM's existing editor listed twice, told apart by the panel's
  per-row state bytes (`+1068 + index`), with `row_match` keeping the remembered row on the first copy. New slider rows
  instead need a free slot in the 16-slot row-widget table (one left) or its lookup hooked
  ([rows note](OM5II-PICTURE-MODE-ROWS-2026-11-19.md)). The row list is now `cp_rows` (7 items); 8+ rows need paging
  checks in OM-Emu.
- **Storage.** 907 / 911 / 915 now hold Tone Balance. RGB curves need 45 more per-profile values: settings cells
  (which ids are free and signed is a research step), the card, or the heap with a card file.

## Suggested order

1. **Move armed-only UI code into `CADUCEUS.BIN`** (label helpers, `paint_strength`, tone hints, Split toning helpers),
   keeping in flash only hooks, entry stubs and code that must run unarmed. `run_page_graphics.py` and
   `run_boot_arm.py` already cover the block's load and refusal.
2. **RGB curves**: image side on the existing route (model from the OM-3, bit-exact test like `st_assert.mjs`); then
   storage; then the row.
3. **Sharpness −5..+2**: static trace of the detail block's input first; UI after.
4. **WB Compensation row.**
5. **Color Mix**: static trace of the matrix site first (OMKit's `ispdrv.c` route as a reference, not a copy).

Each step: targeted OM-Emu runners, commit; `check.py full` once per batch before a camera candidate.
