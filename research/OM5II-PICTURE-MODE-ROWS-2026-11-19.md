# OM-5 Mark II 1.1 (E148): how a Picture Mode sidebar row is defined

Static analysis (objdump) and OM-Emu, 2026-11-19. Emulator and static only.

**Status (2026-11-19, later):** the Black, White and Split Tone rows built from this model were removed (Black / White
moved to the tone page, split toning to the colour wheel; their hooks and data edits are gone). The findings below
still describe how E148 defines a row.

## The pieces of a row (observation)

1. **Row list per picture-mode family**: chosen at `0x60e37600..0x60e376d5` (`mov list,a3` + `mov count,d0`).
   Lists at `0x6119a0xx`, u32 items. Color Profiles use `0x6119a0f0` (6), and Caduceus's `cp_grain_rows` (7).
   Monochrome Profiles use `0x6119a0d0` (8). Monotone uses `0x6f,7,8,0x82,0x83,0x69`; i-Enhance-like modes
   `0x6f,0xd3,7,8,0x3b,0x69,0x132`; Art uses `0x6f,0x363`. Every item in the record table is used by some mode.
2. **Setting resolver**: `0x60e3ccba`, keyed `item − 6` into the 32-slot open-addressed table `0x611a0a98`
   `{u32 key, u32 handler}` (empty slots key 0: 0, 4–8, 10, 11, 14, 15, 17–20, 22). Slider handlers end with the
   setting id in d0 and `bra 0x60e3cd53` (type 0). Carousel/page handlers use `0x60e3cd6e` / `0x60e3cd8a` (type 7).
3. **Row record**: table `0x611b50f8`, 17 × 40 bytes, searched linearly by item at `0x60e49d6f` (stores the record
   at `(4452,a3)`) and `0x60e4a1a4` (stores at `(16,sp)`); both loops end with `cmp 17,d1`.
   Items: `0x6f, 7, 8, 0x3b, 0x69, 0x132, 0x82, 0x83, 0xd3, 0x13a5, 0x363, 0x296, 0x14fe, 0x14fd, 0x14ff,
   0x1501, 0x1500`. Layout: `+0` item; `+4` title descriptor (carousels); `+8` value-label list; `+12` count;
   `+16` slider title descriptor; `+20` icon list; `+24` slider kind `<< 16` (Sharpness 1, Contrast 2,
   Saturation 3, Shading 4); `+28` second icon list; `+32` count.
4. **Descriptors** are `{u16 type, u16 id, u32 0x611b42ac}`: type 4 is a string id, type 3 an image. Sharpness
   uses string 256, Contrast 91, Saturation 227, Shading Effect 4803, Film Grain Effect 2772 (+ 2773.. "… Off" etc.).

## Strings available in E148 (language 0, read from the string table `[0x61e53d30 + 4·lang]`)

"Black" 2202 / 2091, "White" 2201 / 2089, "Shadow" 744 / 282, "Highlight" 743, "Highlight&Shadow" 842,
"Black & White" 564, "Highlight Intensity" 2555. The getter is `0x60d52ed5` (hooked by films.s at `hook_str`).

## Negative result

An item added to the dispatch and the Color Profile list, but with no record in `0x611b50f8`, was not drawn,
and moving onto it stopped the emulator (jump to `0x8940`). The record is required.

## Everything a new slider row needs (worked out by building Blacks / Whites, emulator)

Row items are accepted only in **7..5377** (`cmp 5377` at `0x60e3ccc8`, `0x60e49f3c`, `0x60e3c64b` …). Each item
needs, besides its row-list entry and record:

| Table / site | Keyed | What Blacks / Whites (5370 / 5372) use |
| --- | --- | --- |
| Setting resolver `0x611a0a98` (32 slots) | `(item−6) & 31` | own handler → setting of the active profile → `jmp 0x60e3cd53` (slider path) |
| Key/value dispatchers `0x611a0618`, `0x611a0718`, `0x611a0818`, `0x611a0918`, `0x611b79a8`, `0x611b7b28` (32 slots each) | `(item−6) & 31` | Shading's handlers (generic key handlers act on the row's own object) |
| Row-widget table `0x611b7aa8` (**16 slots**) | `(item−6) & 15` | `0x60e49fdf` (slider). Free slots in stock: 4, 6, 8 only |
| Editor lists `0x6119ff10` `{u16 mode, u16 count, u32 list}` | mode | Color Profile 1..3 list extended (`0x611a02f8`) |
| Slider style / value-label lookups `0x60e4b02c` / `0x60e4b09d` | item switch (7, 8, 59, 616, 5376, 1011, 5374) | hooked: our items use Shading's (11 values −5..+5) |
| Knob value `0x60e4a9d0..` | item switch (7→7, 8→8, 59→59, 5376→1016) | hooked at `0x60e4a9de`: read the active profile's own setting |
| Left-column value, panel handler `0x60e4a34e` | reads effective 1016 at `0x60e4a37a` | hooked: read the active profile's own setting |
| Commit refresh (wb.s) | setting id | the new setting ids mapped to their profile |

Free slots common to every 32-slot table in stock: 0, 4–8, 10, 11, 14, 15, 17–20, 22 … With the 16-slot table,
items whose keys fall on its free slots 4 / 6 / 8 are 5354 / 5356 / 5358 (and 5370 / 5372, now used): **one more
slider row is possible** without hooking that table's lookup. Knob scale: in this panel the stock Shading knob
uses the 5-step scale (±2 reaches the ends; ±3..5 leave the bar); the 11-step branch needs `panel+256 == 1`,
which is not set here. Blacks / Whites behave the same as stock Shading.

**Setting cells differ by id.** Through the UI, 1822 read −2 back as 254, and grain moved there stepped
Off → High (3) instead of Low. The raw writer/reader `0x602f5121` / `0x602f50f8` store any value for every
id tested. Use ids whose family is signed in the UI (907/911/915, 965–967, 993/997/1020 work).
