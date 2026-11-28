# Where RGB curves can live: settings storage on E148 (2026-11-28)

**Static analysis of pinned stock E148 1.1 plus one OM-Emu trace (`xulfr/om-emu` `bdb3347`). No storage chosen or
built; nothing camera-tested.** Phase 4 needs 15 values per Color Profile (R / G / B × 5 points, −7..+7). Packed as
5 × 4 bits, that is one 32-bit cell per channel: **3 cells per profile, 9 in all**.

## How E148 keeps a setting (observation)

- **Two stores.** The *working cells* (`wc_get` `0x602f514d` / `wc_set` `0x602f5173`: object `(0x620e854c)`, key
  35668, one value per id 0..2264) and the *active store* (`active_read` `0x602f50f8` / `active_write` `0x602f5121`:
  object `(0x620e8548)`, key 35684, index **part × 2265 + id**, d1 = part). Both hold any 32-bit value for any id
  (writer checked earlier: [rows note](OM5II-PICTURE-MODE-ROWS-2026-11-19.md)).
- **Store-save `0x602e1153`.** Walks list A `0x604df6a0` (**1464 ids**, when `0x602d2e97` returns 1) or list B
  `0x604e0210` (**1463 ids**). For each id it reads the working cell and writes the active store, **part 0**, unless the
  id is in an override table (`0x604daf50`, `{u16 id, u8 part, …}` × `(0x604daf4c)`), which gives another part
  (`0x602e11d5..0x602e1222`).
- **Init `0x602e131b`** writes every list-B id's default (`0x604db258 + 4·id`) to **parts 0 and 1**; **reset
  `0x602e0cea` → `0x602e0ef3`** does the same over the 2406-id list `0x604dde2e` ([Ghidra findings](OM5II-GHIDRA-FINDINGS-2026-11-18.md)).
  So part 1 is not out of OM's reach: it is set to the default at init and reset.
- **Every id 890..1057 near our cells is in A, B and the reset list** except 893, 894, 897, 899 (reset only), 903,
  989 and 1058+ (reset only). Defaults: 0 for most; 940/941/946/947/950/951 = 1, 952..963 = 3..4, 964/975 = −4,
  968..970 = −1 (the colour and tint families).

## What is taken (this project)

| Ids | Part 0 | Part 1 |
|---|---|---|
| 904–915 | Sharpness 904+p, Contrast 908+p, Shading 912+p; **Tone Balance 907 / 911 / 915** | per-profile WB records (4 cells each) |
| 916–927 | effective Saturation (refresh writes them) | look-slot names 916–919, 924–927; non-COLOR WB 920–923 |
| 928–963 | Saturation, 12 per profile | Hue / Lightness (`0x4831` tag) |
| 964–975 | tints 964 / 968..975, Black / White 965..967 | tone save 964–971, look-slot name 972–975 |
| 976–984 | tone curve 976+3p .. 978+3p | **nothing found** |
| 993 / 997 / 1020 | Black / White | — |

## Leads for 9 cells

1. **Part 1 of the tone cells 976–984 (leading).** Exactly 3 per profile (976+3p → R, 977+3p → G, 978+3p → B).
   Init and reset write the default 0 there, which is a flat curve, as wanted. In OM-Emu, a session that edits the
   tone page, switches profiles and returns to shooting made **no `active_read` / `active_write` call on 976–984 at all**;
   stock reached them only through the context getter (`0x602d000d`), `raw_get` (`0x602f4c5b`, id only) and `wc_set`
   (working cell, no part). Part 0 holds the tone values, so part 1 sits beside data we already own.
2. **Part 0 of ids with no known owner in the same lists**, e.g. 990, 991, 994, 995, 996 (default 0, in A, B and
   reset). Weaker: the immediate-load scan of stock code is too noisy to show they are unused (family members are
   reached as base + p, so zero immediates prove nothing, and misdecoded data gives false hits).
3. **The card** (a per-look file) or the heap with a card file: no settings risk, but values would not follow C1–C5 or
   survive a card swap.

## Still to establish for lead 1 (before building)

- **C1–C5.** Whether custom-mode save / recall copies part 1. The C-mode copy (`0x602e1237`, through `0x602f52ea`, then
  `active_write` at `0x602e12e0` / `0x602e1306`) needs reading for the part it writes; our `creset` notes say the
  custom-mode reset clears both parts of live cells. OM-Emu: write sentinels to part 1 of 976–984, then Assign to C1,
  change, recall C1, read back.
- **Power-off.** OM-Emu does not model the NAND save. The per-profile WB records in part 1 rely on the same
  assumption and are themselves not yet camera-checked: one camera check of a WB record across power-off answers both.
- **Override table.** Whether `0x604daf50` routes any of 976–984 to a non-zero part (would make part 1 OM's).
- **All writers.** A wider OM-Emu watch (menus, playback, capture, Reset, C-modes) on parts 0 and 1 of 976–984.
