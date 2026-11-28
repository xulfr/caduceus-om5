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
