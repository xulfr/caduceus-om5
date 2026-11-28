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

## Step 3b-1: strength 0–10 (2026-11-28, emulator only)

- As the OM-3 v0.28 t2: the editor's own −5..+5 **is** the strength, s = w + 5. `tint_read` gives s − 5 on the tint's
  colour and −5 on the others; `tint_write` (via `tw_strength`) stores s, 0..10; OM's reset gives 0. The tables use
  T = s × colour >> 1, so 10 is the earlier 5 (a strength stored by earlier builds now applies at half).
- **The start of the count.** OM makes the editor's children through its own getter (Saturation values) and keeps the
  editor between the two rows, so the first value step on a tint page counted from the Saturation value (3 clicks →
  8). `wheel_value` wraps the editor's value-dial method (vtable `0x61211c90` + 96, pointer site `0x61211cf0`, stock
  `0x60e9c0a2`): off Saturation it re-reads the children before the step. This also covers Hue / Lightness after the
  focus comes back. The "short count" seen in 3a came from this.
- **The value label.** OM's value label has pictures for −5..+5 only: strengths 6..10 drew nothing in OM-Emu. Rather
  than push it past its range (an out-of-range picture lookup is the leading suspect for alpha10's restart), it shows
  the editor's position (s − 5), and `paint_strength` (`.ext5`) writes the strength 0..10 under the title. Hiding OM's
  label on these pages is a follow-up.
- **Room.** `.ext2b` and `.ext9` are full. `.ext2c` (`0x604ef064..0x604ef120`, the rest of setting 111's dead record
  table, set aside before for the shelved colour-grain row list, which `cp_rows` replaces) holds `tw_strength`,
  `wheel_value` and `cp_rows`.
- Tests: `run_wheel_keys.py` 16 (`split-strength-stops-at-10`, `split-strength-back-to-off`); `st_assert.mjs` checks
  T = ⌊s × colour / 2⌋ for s ≤ 10.

## Step 3b-2: Tone Balance (2026-11-28, emulator only)

- A third page on the Split toning row: INFO steps **Shadows → Balance → Highlights** (axes 3 → 6 → 5). On Balance
  every colour shows the profile's Tone Balance (−5..+5); the value dial sets it; OM's reset gives 0; OM's own value
  label shows it (in range). Title "Balance".
- Stored at **907 / 911 / 915** (Color Profile 1..3): the ids of the removed Color Profile grain, default 0, already in
  OM's reset and custom-mode copy lists ([Ghidra findings](OM5II-GHIDRA-FINDINGS-2026-11-18.md)). The shelved
  `claude/cp-grain-experiment` branch uses them too.
- Image: as the OM-3 v0.28 t1, b moves the hand-over point between the Shadow and Highlight tints, c = 128 − 16b of the
  256 output levels (OM-3: 2048 − 256b of 4096). The tint weights use u = (i − c) × 128 / c below c and
  (i − c) × 128 / (256 − c) from c up (truncating division); b = 0 gives u = i − 128. Black / White keep u = i − 128.
  `tn_pre` reads the profile's b into P+1540 (`ST_BAL`) before the tables; `tn_bal` maps u per index (`.ext5`).
- OM-Emu: `st_assert.mjs` models it and matched bit for bit at b = +3 (Shadows 5 / Highlights 7) and b = −5 (10 / 1)
  (`run_bw_tint.py` `cp1-balance-plus` / `-minus`); `run_wheel_keys.py` `split-balance`, `split-balance-limits`.
- Whether the balance shows as wanted in photos: camera only (OM-Emu develops no photos).

## Still to do (3b)

The row's own icon (both rows show "Color Vivid":
the icon comes from the item's picture record), hiding OM's value label on the tint pages, and the OM-3's "Split Tone" hint picture.

## Step 3c: the row's icon, OM's value group, the hint (2026-11-28, emulator only)

- **Icon.** The Picture Mode column draws each row through the item's slot in `0x611b7b28` (`(item − 6) & 31`); item
  5374's handler `0x60e4a3e0` (shared with 5373 / 5029 / 662) shows the row record's `+28` image (`0x2c85` "Color") and,
  when the row's value is not 0, the value text under it ("Vivid", mode 5 at `(6, slot)`). Its loop keeps the list
  index at `(24,sp)` (with paging), the shown row at `(96,sp)`, the rows' base at `(20,sp)`, the panel at `(28,sp)`.
  `col_icon` (`.ext10`, slot 24's word at `0x611b7bec`) shows the new image **`0x3e84` "Split / Tone"** on list index 2,
  image only (mode 1); every other row goes to the stock handler.
- **OM's value group.** The colour view (`0x610c14a0`) has labels at `+792 + 4i`: 1 / 2 the arcs, 3 "Color", 4 the
  swatch, 5 "Vivid", 6 the value (OM's −5..+5 pictures), 7 an alternative to 6 (hidden on every page seen), 10 the hint
  frame, 11 the hint. Its data-model handler **`0x60df1217`** (vtable slot `0x610c1630`, once per command) re-sets every
  label's image and visibility through `0x60df124a`, so a hide made earlier in the command (first tried from
  `pg_axis`) is undone. `view_upd` (`.ext10`) now takes that slot: OM's handler, then the card block's `tint_vis`
  (stub in `.ext6`): on Shadows / Highlights labels 2, 5, 6, 7 are hidden; elsewhere, when label 2 (never hidden by OM)
  is off, 2 / 5 / 6 are shown and 7 hidden again. Balance keeps OM's value (in range).
- **Hint.** OM's own hint for this editor is `0x3f7d` "Color Select [INFO]", 180 px (label 11's record,
  `0x610c103c`; `0x3f7c` "Color All [INFO]" is 175): the 128 px "limit" was only our tool's. **`0x3e85` "Split Tone
  [INFO]"** is composed in that font from OM's glyphs (S, l, t, o, e from `0x3f7d`; i from "Mid"; p = "Mid"'s d turned
  180°; n = the lower part of "Sh"'s h; T = l's stem and t's crossbar) with OM's INFO key copied as is, and outlined as
  OM's (rings 7, 9). Label 10's frame (about 142 px, narrower than the hint) is hidden on the three Split toning pages.
- **Tool.** `oly_ui_bitmap.compose_glyphs` (sprite `"glyphs"`): glyph cores (value ≥ `core`) placed on a canvas,
  turned 180° on request, raw places copied as they are, then outlined. `oly_resource_recipe.py --glyphs`.
- **Room** after this step (to the next range or the loaded section's end): `.ext10` 12 bytes, `.ext6` 15, `.ext7` 36,
  `.ext5` 56, `.ext2c` 52, `.ext3` 36, `.ext8` 26, `.ext9` 10, `.ext2` 1 (`.ext2b`'s figure is the dead table's, ~31).
- **Without the card block** the icon and the hint image still show (flashed / resource); OM's value group stays and
  the frame shows behind the wider hint.
- Tests: `run_page_graphics.py` 16 (new: `split-row-icon`, `split-value-group`, `split-hint`).
- Seen, not changed: after INFO to Highlights and back up to the wheel row, the Saturation page's value label read
  "Vivid −5" (OM-Emu) until the next command; it was the same before this step.
