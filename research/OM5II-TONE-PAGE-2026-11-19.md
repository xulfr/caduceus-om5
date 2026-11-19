# OM-5 Mark II 1.1 (E148): the Color Profile tone page and its Black/White state (v0.2.0-dev)

Static analysis (objdump) and OM-Emu traces, 2026-11-19. **Not camera-tested.** Addresses are runtime addresses of
the expanded E148 1.1 main program.

## How OM's tone page works (observation)

- The tone page is child 2 of the Picture Mode direct screen (shown by `pages_hook`). Its paint view has vtable
  `0x610d6560` (paint slot `0x610d6600` → `paint_tone`) and 17 label widgets at view+792+4k (k = 1..17):
  1 / 5 / 9 the dial icons above Sh / Mid / Hi, 2 / 6 / 10 the titles "Sh" / "Mid" / "Hi", 3–4 / 7–8 / 11–12 sign and
  digit, 13 / 14 "Reset OK Hold" frame and text, 15 the hint frame, 16 the hint ("Mid INFO" / "Hi/Sh INFO", one
  label switching images), 17 unused here. All are bitmaps (image ids such as 0x2aab, 0x0460.., 0x3f7f), not strings.
  Positions after `page_layout`: title 2 at (431, 85) 38 × 30, title 10 at (617, 85), hint at (270, 417) 180 × 50.
- The view's own label update is `0x60df862e` (a0 = view), called at `0x60df85f3` and `0x60df8626` (each followed by
  `ret [a2],8`). It sets every label's visibility and image after each change. The sidebar (vtable `0x610c5340`,
  child 1) has its own update `0x60df25b6`; do not confuse the two (an early build hid sidebar labels by asking
  `child_get` for d0 = 1).
- The editor is a stock "item" object whose handlers come from a 56-byte type record (table `0x6120e9dc`, 139
  records, searched by the u16 key at +0; constructor `0x60e9ba4c`): +4 / +8 → object +88 / +92, +12.. eleven
  handlers → object +44..+84 when non-zero. Color Profile 1 / 2 / 3 use keys **0x1531 / 0x1532 / 0x1533** (records
  `0x61210764`, `0x6121079c`, `0x612107d4`; seen at object +96). Dispatch `0x60e9c10e`: 0x9014 INFO → +76
  (`0x60e9e8ff`, record +44), 0x900c → +72; dial handlers `0x60e9c0a2` (main) → +60, `0x60e9c0d8` (sub) → +64.
- Object +120 child count (4), +124.. children: child 0 the Hi/Sh / Mid switch (setting 2189), children 1–3 the
  values with setting id at +80 (976 Hi, 978 Sh, 977 Mid for Color Profile 1), list count at +92 (15) and index at
  +94 = 7 − value. +122 = OM's state: **0 Hi/Sh, 1 Mid** (copied from child 0 by the INFO handler).
- The INFO handler sends 0x9004 then 0x900c to child 0 and stores its state at +122. In Hi/Sh, both dials go to
  Sh / Hi (in OM-Emu a lone `main-3` moved Sh), in Mid both go to Mid.
- Setting 2189 holds the switch's value: in OM-Emu it reads 3200 until INFO is first used, then 0 / 1. Treat "1" as
  Mid and anything else as Hi/Sh.
- Values are read and written through the hooked reader / writer (`read_hook` / `write_hook`, section 6): the
  children use them with the ids above.

## The Black/White state (built)

- Per-type INFO slots `0x61210790`, `0x612107c8`, `0x61210800` point to `tone_info` (ext2). On Color Profile 1–3
  once armed: Hi/Sh (+122 = 0, P+1178 = 0) → Black/White: consumed, P+1178 (`ST_TM`) = 1, OM's state stays Hi/Sh.
  Black/White → Mid: P+1178 = 0, then OM's own handler. Mid → Hi/Sh: OM's. Elsewhere: OM's handler only.
- `tone_alias` (from `ui_read` / `ui_write`, guarded by `ui_alias` in section 5): with P+1178 = 1 on profile p,
  976+3p (Hi) → Whites, 978+3p (Sh) → Blacks. `tone_refresh` sets the value children's +94 from the (aliased)
  values on each switch and sends 0x900c to the editor (its +72).
- `tone_labels` (each layout via `pg_tone`, and after OM's view update via `tv_upd` at `0x60df85f3` /
  `0x60df8626`): in Black/White it hides labels 2–4 and 10–12 and shows 16 ("Mid INFO" is right: Mid is next); in
  Hi/Sh it hides 16; then it invalidates the view. Without the `tv_upd` hook OM's update showed "Sh" / "Hi" again
  after every change (emulator).
- `tone_text` (end of `gfx_tone`) draws "Black n" / "White n" (stock font through `stock_text`, box 110 wide at
  (395, 84) and (600, 84)) in Black/White, and "Black/White" in the hint frame in Hi/Sh.
- The state lasts until INFO leaves it or power-off (P is heap), like OM's own Hi/Sh / Mid choice. A screen that
  reopens on the tone row in that state reads Blacks / Whites into its children at once (consistent).

## Space and load order

- Code reachable from the GUI before arming must sit in a section that loads before section 7: the loader runs
  sections **1, 8, 2, 3, 4, 5, 6, 7, 9, 10** ([brick-risk table](OM5II-BRICK-RISK.md)). `tone_info` is in ext2,
  `tv_upd` in ext3, `ui_alias` in ext5; they enter ext9 / ext10 code only after `st_ptr` says armed.
- New this build: the FF tails of **section 3** (`0x60621e80..0x60622000`, `ext3`) and **section 9**
  (`0x615ee5c8..0x615ee800`, `ext9`). Section 9's tail start is named by the constructor-table walker at
  `0x601ae8d8` with a count of 0 (the same pattern as section 4's tail, which wb.s has used since alpha builds).
  Neither section's tail has been used on a camera before: part of the camera check.
- Assembler pitfall (again): `call` / `calls` to an address given as an `=` equate in the .s file links as a raw
  displacement (an OM-Emu jump to `0xc13a1c78`). Absolute targets go in `layout.ld`.
- A 5-byte `call` hook cannot reach ext code (it needs the 7-byte far form); hook a `call` site with `jmp` to a
  trampoline that makes the call and then replays the instruction after it (`tv_upd`).
- Halfword data after odd-sized code needs `.balign 2` (an OM-Emu misalignment fault at `tt_copy`).

## Tests

`tests/run_bw_tint.py` (7 cases, all passed on the build recorded with this note): Black / White values, OM's tone
values untouched in Black/White, the INFO cycle back to Hi/Sh, Color Profile 2, a stock mode afterwards, and the
tints. Screens are saved per case.

## Open: Black / White labels larger than Sh / Hi (camera report 2026-11-19)

Owner: "Black n" / "White n" are drawn noticeably larger than the stock "Sh ±n" / "Hi ±n". OM-Emu shows the same.
Findings so far (emulator and static, not fixed):

- `tone_text` draws through `tx_draw` (ext6): `stock_font(1)` (`0x60d51f07`) then `stock_text` (`0x60d4b7bc`). E148 has
  one font record per language: `font_record` `0x60d52e6b` (d0 = id → table `0x61e53d7c`[language] + 74 × id); only
  id 1 ("Olym…", size byte +66 = 50) is filled. Ids 0, 2 and 3 return no font (nothing drawn).
- The stock Sh / Mid / Hi labels do not go through `stock_text` (traced: only Caduceus text calls it on that page).
- Copying record 1 with +66 = 34 and building the font with `stock_font`'s body (`0x60d51f18`) gave font attributes
  `22 00 22 00 …` but the **same-size** glyphs, and with +66 = 20 or 4 the next string ("White") came out garbled.
  The font object (`0x6220338c`) is the same shared object either way, so its size is global and appears to be
  cached by the glyph engine. Not safe to change on the camera; reverted.
- Next: find how the stock label widgets (view +792 + 4k, labels 2..4 / 10..12) render their text (they may be
  resource images or a second font path), and draw Black / White that way, or reuse the stock title labels.
