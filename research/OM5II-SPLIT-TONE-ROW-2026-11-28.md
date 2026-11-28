# Split toning on its own row, step 3a (2026-11-28)

**OM-Emu only (`xulfr/om-emu` `bdb3347`), strict build. Not camera-tested.** Roadmap phase 3, first step: the row and
its pages. Strength 0–10, Tone Balance and the row's own icon are step 3b.

## What the row is

- The Color Profile row list (stock `0x6119a0f0`: 111, 5374, 5375, 5376, 7, 8; taken at `0x60e376c3`) is replaced by
  `cp_rows` in `.ext2b`: **111, 5374, 5374, 5375, 5376, 7, 8**. The pointer at `0x60e376c5` and the count byte at
  `0x60e376ca` (6 → 7) are patched. Monochrome Profiles keep their list.
- The second 5374 is the Split toning row, as on the OM-3 v0.41 ("the wheel's row a second time"). Both rows open
  OM's colour editor. P+0 decides what it edits: 0..2 Saturation / Hue / Lightness, 3 / 5 the Shadow / Highlight tint
  (`tint_read` / `tint_write`, unchanged from the wheel's former Tint group).
- INFO on the Split toning row: Shadows ↔ Highlights. The Midtone tint (axis 4) is not offered. Hint "Split [INFO]";
  "Split Tone" did not fit OM's 62-px blank in front of the INFO key.

## Findings (OM-Emu)

1. **An item can be listed twice.** With 5374 in place of 5376 (a run-time edit, before building), the second row
   drew, opened the wheel page, took dial steps and INFO, and moving on to the tone row worked. Both rows edit the
   same cells.
2. **Which row has the focus.** The Picture Mode panel (`(scr_obj 0x61e588f4)->+4`, `0x61ad0730` in the runs) keeps one
   state byte per row at `+1068 + index`: 0, 3 on the focused row, 4 on the focused row once a dial changed it.
   `st_split` reads index 2.
3. **The editor is kept between the two rows.** Moving from one 5374 row to the other does not rebuild it, so its
   children still hold the other row's values (seen: "Vivid +3" from the tint on the Saturation page). `pg_rows`
   (from `pages_hook`) therefore sets the row's own page when the axis belongs to the other row (Split toning opens
   on Shadows, the wheel on Saturation) and re-reads the children. It finds the editor as `hsl_container` does
   (colour page = child 4, editor at +76).
4. **Reopening Picture Mode.** OM's column builder (`0x60e377a5..`, a `setlb` loop) marks the row whose item equals the
   remembered one (2148) and keeps looking, so the last match wins: it reopened on the Split toning row. The 5-byte hook
   `row_match` at `0x60e377ed` (replacing `cmp d0,d2; bne 0x60e377f5; mov (16,sp),a0`) skips a 5374 at index 2, so
   Picture Mode reopens on the colour wheel row.
5. **Midtone tint cleared.** `mid_clear` (from the arming fix-up, `arm_fix_done`) writes 0 to 971..973 when an earlier
   build left a value there. A seeded 0x30 reads 0 after arming and the split-tone flag stays 0.

## Known, not new

- After the colour cursor moves on a tint page, the next dial steps count short (OM-Emu: 3 clicks → strength 1). The
  earlier tint test encoded the same (`main+2` → strength 1). To be fixed with the 0–10 strength in 3b.
- `run_tone_icons.py` fails identically on `main` (11 different icons for 27 states). `run_ui_activity.py` `idle`
  fails on `main` too.

## Tests

- `tests/run_wheel_keys.py`: 14 cases (5 new: the wheel row, Split toning opens on Shadows, INFO steps, back to the wheel,
  reopening on the wheel row).
- `tests/run_bw_tint.py`: 12 cases (`cp1-split-row`, `cp1-split-then-wheel`, `cp3-midtone-cleared`).
- Rows below the wheel moved down one in `run_emulator.py`, `run_look_defaults.py`, `run_page_graphics.py`,
  `run_profile_rows.py`, `run_profile_icons.py`, `run_tone_icons.py`, `run_ui_activity.py`.

## Still to do (3b)

Strength 0–10 in half steps (the editor's −5..+5 list read as 0..10, OM's value label shown as the strength), Tone
Balance −5..+5 as a third page (storage and the OM-3's definition), the row's own icon (both rows show "Color Vivid":
the icon comes from the item's picture record), the short-count quirk above, and the OM-3's "Split Tone" hint picture.
