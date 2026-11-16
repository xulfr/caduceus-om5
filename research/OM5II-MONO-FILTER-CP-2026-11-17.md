# OM-5 Mark II: Monochrome colour filter page and CP "any item" test (17 November 2026)

**Emulator and static analysis only.** Nothing here has run on a camera. Addresses are runtime addresses of the
expanded main program (base `0x60021020`), E148 1.1 unless marked E147.

## OM-3 reference (E147 1.1)

- Stock file `OLY_E_147_1100_0000_0000.BIN`, 240,517,120 bytes, SHA-256
  `8c133084414533159f587bf46bfb4152714c4074312a47c8d8503e33d605696d` (OM's server via `patch.fetch_stock`,
  model code E147). Not committed.
- OM-Emu (`bdb3347`) has no key for the OM-3's Creative Dial. Its UI_IN group 5 holds code `0x1906` on bits
  0..4 (five positions); the idle position 1 is COLOR. A PRE module that sets the bits in `session.images[5]`
  and calls `session.push_group(5)` turns it: 0 MONO, 1 COLOR, 2 standard picture modes, 3 ART, 4 Color Creator.
  (Group 4 `0x1909`, three positions, is the stills / S&Q / movie switch.)
- In MONO the image planes use `PLANC 0x1100` (format 3, monochrome live view), which OM-Emu's compositor
  refuses; a scratch copy that skipped those planes was used to view the OSD. That copy is not the OM-Emu
  checkout the results name.
- Monochrome Profile 1, first sidebar row: header "⌒ Color Filter / None", bottom "⌣ Level +2". The sub dial and
  the arrows step None → Yellow → Orange → Red → Magenta → Blue → Cyan → Green → Yellow-Green → None. The sidebar
  icon is one fixed "Color / Level" image for every value. OM-Emu's main dial did not reach this page, so the
  level's range was not stepped there.
- Not observable: the OM-3's graphic. It is drawn through the GPU layer (`DRAW_PROFILE`, WIP UI3 note), which
  OM-Emu does not model. What the OM-3 draws on this page is therefore unknown.

## E148 filter page (child 3 of the direct screen)

- View vtable `0x610d9b20` (built at `0x60dfa4d2`), paint entry `0x610d9bc0` (stock `0x60d47232`). Shown by
  pages_hook from flag **+246** of the data struct (not +244: that flag is set on the Picture Mode row).
- It already worked in OM-Emu on alpha10: the sub dial steps setting 1007+p through list `0x6050cb23`
  (5,0,1,2,3,6,7,8,4 = Yellow-Green, None, Yellow, Orange, Red, Magenta, Blue, Cyan, Green, so from None the
  dial gives the OM-3's order) and the main dial steps the level (1011, saved to 1012+p, values 0..3, shown as
  "+n"). Values are kept after leaving the screen. Value names (table `0x611b46c8`): 0 None, 1 Yellow, 2 Orange,
  3 Red, 4 Green, 5 Yellow-Green, 6 Magenta, 7 Blue, 8 Cyan (strings 2763..2771).
  **Correction:** the alpha9/alpha10 handover said the dials did not change 1007+p. Only the main dial had been
  tried. Also, the lab reader `0x602f50f8` (part 1, as `sess.mjs --cells`) does not show the change; the store
  `0x602d19b6` (logged by `tests/store_log.mjs`) and the page after re-entry do.
- Its widgets (descriptors `0x610d9830..`, rectangles {x, y, w, h} twice, second layout x + 80):
  `0x3e2` "+n" value (`0x610d979e`), `0x181` front-dial icon `0x2aaa`, `0x3d8` rear-dial icon `0x2aab`
  (`0x610d97be`), `0x3e0` header image `0x107f` "Color Filter", `0x184` word image `0x107e` "Vivid"
  (record `0x610d972c`, image id at `0x610d9738`), `0x185` image `0x1081`.
- The word is an image, not a string; E148 has no "Level" word image (searched all 36..80 x 18..34 images).
- Fonts 0, 2 and 3 of `stock_font` draw nothing in OM-Emu; font 1 draws "Level" about 66 px wide, wider than the
  58 px between the icon and "+n".

## What alpha10 does

- Data edits (cp_nd.py): word image `0x107e` → `0xffff`; rear-dial icon 10 px left; "+n" 10 px right.
- hsl.s: `paint_filter` on `0x610d9bc0` (section 6, armed only) → `gfx_filter` (section 5): Monochrome
  Profile p only (111 = 57..59), reads 1007+p with `stock_get`, draws "Level" (font 1, as paint_axis) and a ring
  of eight 26 px blocks (radius 80 round (556, 236), Yellow at the top, clockwise in dial order), a 34 px white
  block behind the selected one and a 46 px centre block in its colour (grey for None): 11 OSD commands.
  Palette indices from gfx_wheel: 123, 92, 122, 89, 105, 107, 22, 116.
- `pg_axis` also invalidates child 3 when flag +246 is set; without it OM repaints only the header's rectangle
  and the ring stayed on the first value (seen in OM-Emu).
- Sidebar icon `0x38cb`: kept as one "Filter" image for every value, as the OM-3 shows one fixed icon.
- `tests/run_mono_filter.py`: 12 dial steps (all nine filters and the wrap) with the stored value, graphic and
  header per step; level; persistence after leaving; Monochrome Profile 2 unchanged. Fails on the alpha10
  candidate (`1530ca05…`), passes on the release build.

## CP button "any item ticked" (0x60d2230f)

- Called only by `0x60d222d3` when the current item (2228) is 17 (none). It asks `0x60d223d5(k)` (CP table
  `0x60f7f57c`, stride 16 {mask, index, enable id, control id}: is item k ticked) for k 0,1 → function 125;
  k 2..5 → 109; k 13 → 124; k 14,15 → 17; k 16 → 134 (`0x60d044be` availability). k 6, 7 (ND32/ND64, enable
  2217/2218, mask 109) and k 8..12 (mask 35, not on the CP Button page) were skipped.
- Fix: `cp_any_hook` at `0x60d22357` (7 bytes, `mov 5,d0; call 0x60d223d5`) → `call cp_any_nd` (section 7):
  k 5, then when armed k 6 and 7; the stock 109 check follows. Unarmed: k 5 only.
- Other carousel paths: GUI `0x60e27d22` lists 2228's allowed values (alpha10's descriptor edit adds 7, 8); the
  switch at `0x60e27f92` (jump table `0x61190d84`) sends values 3..8 to the same Live ND case.
- Not run: OM-Emu has no CP button for E148, and calling `0x60d2230f` from the lab task faults in its setting
  read (SCPU command, as `stock_get` does). Result is static analysis plus a disassembly of the built image.

## Alpha11 follow-up

The owner saw a restart on entering the alpha10 Color Filter page. Alpha9 opened the same page with
no filter graphic. See the [alpha10 camera report](OM5II-ALPHA10-CAMERA-2026-11-17.md).

### D2. Color Filter page restart

- In stock E148, the widget at `0x60d8e4e0` reads the 16-bit image ID at layout offset +12 and passes
  it to `0x60d52e84`. This helper special-cases zero and computes `table + 4 * (uint16_t)id` for
  every other value. It performs no upper-bound or `0xffff` check. The widget's signed `-1` check at
  `0x60d8e4f9` reads offset +0 of the layout record, a separate field.
- Record 0's loaded image-table base is `0xa3435ccc`. The record ends at `0xa3456d74`, at most
  `0x842a` four-byte entries from the base. ID `0xffff` produces `0xa3475cc8`, outside that record.
  The draw path reads the slot at `0x60d8e57e`. `0x60d4e1c2` also reads it and checks the
  returned pointer for zero after the read. The scan of 8,268 stock records matching the filter layout's
  `{0xffff, 7, 7, image}` prefix found zero with `0xffff` in the image field.
- With the exact alpha10 package reproduced, OM-Emu observed image ID `0xffff` at
  `0x60d8ebf5`, `0x60d8ec97`, `0x60d8e57e`, `0x60d8e5d4` and `0x60d4e1c2` on entry.
  The emulator continued to draw and accept a dial turn. The out-of-range lookup is established.
  Its role in the physical restart remains the leading hypothesis.
- `paint_filter` uses the same wrapper as `paint_tone`. It saves d2/d3/a2/a3, reserves 12 bytes,
  saves a1 at sp+8 during stock paint, preserves the stock d0 result in that slot and restores the
  frame at exit. It uses the same paint event and arming gates. `gfx_filter`'s 72-byte call frame
  includes the 16 saved-register bytes and fits the local slots through sp+47. The font call and
  style/font restoration follow `paint_axis`. The wrapper shows no evident mismatched return or
  register-save error. Stack headroom in the camera's filter-page caller, the extra text and pen
  operations, and child 3 invalidation remain unverified on camera.
- Alpha11 restores image `0x107e`, both stock rectangles and the stock paint entry at `0x610d9bc0`.
  It removes the ring, “Level” text and flag +246 invalidation. The page uses alpha9 rendering
  with the native “Vivid” word. The Filter sidebar artwork survives from alpha10. The picker is
  postponed. The CP any-item hook is reached from the CP button path and remains in place.

### D1. CP carousel artwork

- GUI `0x60e27d22` enumerates 2228. Values 7 and 8 use enable settings 2217 and 2218,
  respectively. Their jump slots `0x61190d84 + 4 * (value - 3)` go to the shared ND case
  `0x60e27f92`. The third field of the 12-byte records at `0x6118fe6c` gives display
  string IDs `0xf9` and `0xfa`.
- The direct viewer's CP entry `0x5c` at `0x611b3eac` points to the 18 icon rows at
  `0x611b3598`, stride 12, with the image halfword at +6. Values 3–6 use
  `0x2354..0x2357`. Values 7 and 8 use `0x2358` and `0x2c84`.
  The second table at `0x611b3670` supplies type-4 caption IDs `0xfc9` and `0xfca`.
- Both icon slots point to stock's zero-size placeholder `0xa3435cb8` in alpha10.
  Alpha11 shares the type-14 bitmaps already made for shooting labels, using
  `--artwork 2062=2358 --artwork 205d=2c84`. This changes two resource pointer
  words and reuses the existing 58×28 and 56×28 artwork. Decoding the stock type-14
  pointer at header +16 shows ND8 and ND16 in `0x2060` and `0x2061`, respectively.
- OM-Emu ran the carousel constructor and enumerated 7 and 8. The raw key and CP event
  probes did not produce a carousel frame. Icon validation is static pending the owner's check.

## Alpha12 filter graphic

The owner confirmed alpha11 boots, the CP icons appear and the filter page stays
open and responds to the dial. The centre remained blank with the stock painter.
[Alpha11 camera report](OM5II-ALPHA11-CAMERA-2026-11-16.md).

Alpha12 restores the graphic part of the paint hook at `0x610d9bc0` and the child 3
invalidation for flag +246. The hook calls the stock painter first and draws
only on an armed type-2 paint event in Monochrome Profiles 1–3. The renderer
takes a 44-byte frame, validates the profile and filter indices, and uses the
same pen save and restore as the colour wheel and tone curve. The stock header,
word image `0x107e` and widget rectangles stay in place. The font and text calls
from alpha10 are omitted. The physical cause of the alpha10 restart remains a
hypothesis pending camera results for the reduced paint path.
