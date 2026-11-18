# OM-5 Mark II 1.1 (E148): Film Grain for Color Profiles (v0.2.0-dev)

Static analysis and OM-Emu only, 2026-11-18. **Not camera-tested.** Addresses are runtime addresses of the
expanded main program. OM-Emu `bdb33470`, GNU binutils 2.42 `mn10300-elf`.

## How the Picture Mode sidebar chooses its rows (observation)

- `0x60e376c3` picks the row list by picture-mode family. Color Profiles take `0x6119a0f0`, 6 row items
  `111, 0x14fe, 0x14ff, 0x1500, 7, 8`. These are the mode strip, colour wheel, tone, Shading, Sharpness and
  Contrast. Monochrome Profiles take `0x6119a0d0` (`mov 8,d0` at `0x60e376bf`): the same six with the filter row
  in place of the wheel, then **`0x1501` (Film Grain)** and `0x83` (toning).
- A row item resolves to its setting through `0x60e3ccba`: key `item − 6` in the 32-entry dispatch `0x611a0a98`.
  `0x1501` goes to `0x60e3cd68` → `0x60e3d0f5`, which reads setting 111 and searches `{u32 mode, u32 id}` table
  `0x611a02f8`, 4 entries: 57/58/59/65 → 999/1000/1001/1002. It returns 0 when there is no match. A second copy,
  `0x60e4b32e` with table `0x611b5ad0`, serves the same IDs.
- `0x6119ff10` is a different table: `{u16 mode, u16 count, u32 list}` read at `0x60e3dbac`. Pointing Color
  Profiles at a 6-item list there did **not** add a row (negative result, emulator).
- Adding Color Profiles to the lookup table alone showed no row. Adding `0x1501` to the Color Profile row list
  showed the "Film Grain Effect" row. Without a descriptor for the stored ID, its carousel read "Off" seven times.

## Storage (decision, with its evidence and risk)

- The grain value is kept in **907 / 911 / 915**: the value (part 0) cells of Color Profile **4**'s Sharpness,
  Contrast and Shading. E148 has no Color Profile 4 (inference: 111 = 64 is not in the Picture Mode strip), and none of the three has a
  stock descriptor among the 1589 at `0x6050dad4`. Part 1 of the same IDs holds this project's WB records
  (wb.s). That part is separate; the emulator showed the WB words unchanged by a grain edit.
- Hypothesis still open: no stock path writes these cells. A byte scan is too noisy to settle this. It needs
  cross-references (Ghidra), or a camera check that a Reset or custom-mode recall leaves grain as expected.
- Each ID gets a copy of 999's descriptor: 4 values, list `0x6050ced8` = 0..3, flags `0x200`.
  `cp_nd_link` links 8 descriptors (was 5) into OM's RAM hash once armed. P grows from 1040 to 1064 bytes for
  the 3 extra nodes.

## Edits (firmware/om5ii/cp_nd.py, hsl.s, wb.s)

| Edit | Address | Change |
| --- | --- | --- |
| `cp_nd_descriptors` | `0x604f24f0` | + 907, 911, 915 (copies of 999's) |
| `cp_item_values` | `0x604f2590` | moved from `0x604f2554` to make room (`cp_item_desc` follows) |
| `cp_grain_table` | `0x604f25a8` | 57..59, 65 → 999..1002, then 54/55/56 → 907/911/915 (fills to `0x604f25e0`) |
| `cp_grain_lookup_a/_b`, `cp_grain_count_a/_b` | `0x60e3d10d`/`0x60e3d121`, `0x60e4b346`/`0x60e4b35a` | both lookups → new table, 7 entries |
| `cp_grain_rows` | `0x604ef064` | Color Profile row list with `0x1501` (tail of 111's old record table, unused by color_profiles.py) |
| `cp_grain_list`, `cp_grain_list_count` | `0x60e376c5`, `0x60e376ca` | Color Profile case → new list, 7 items |
| hsl.s refresh | ext5 | effective 998 = `907 + 4p` for Color Profile p (was 0); new `src \| 0x4000` stride flag |
| wb.s `wb_profile` | `0x613f2f20` | the commit hook maps 907/911/915 to profile 0/1/2, so an edit refreshes at once (it fits with no spare bytes) |

## Emulator results (tests/run_cp_grain.py)

The 6/6 cases pass on the v0.2.0-dev build (package `39160075…d3c3`). Values read through OM's getters:

- CP1 → Low: 907 = 1, effective 998 = 1. CP2 → High: 911 = 3, 998 = 3.
- After CP1 Low, switching to CP2, to a stock mode (111 = 5) or to Monochrome 1 gives 998 = 0. MONO1's own grain
  is 0, and 999..1001 stay at alpha12's values. Returning to CP1 gives 998 = 1, and the value survives leaving
  and reopening Picture Mode.
- Control: the same `cp1-low` case fails on the alpha12 build (no grain row).
- Static audit against alpha12: all edits declared, no byte back to stock, native loader bounds and resources
  unchanged.

## Fix: Delete and the title on the Film Grain row

The grain row is a carousel, so the panel updater's `+136` reads 4 there as on the mode strip. The first build stepped
a look when Delete was pressed on the grain row (case `grain-row-delete` fails on it: "slot 0 untouched"). The
title restore had the same gate. Both now also require the row's title id (updater `+140`, descriptor `+4`) to be
the strip's: 203, or 2749..2751. Grain titles are 2772..2775. Emulator dump: `+140` = 2749 / 203 / 2757 on the
strip (Color, after returning, Monochrome) and 2772 / 2774 on grain. `+260` also separates them (1 vs 0), but its
meaning is unknown, so it is not used. `row-return` now presses down 7 times; with 6 it had passed by
stepping a look from the grain row.

## Not shown

- That E148's image pipeline applies 998 in a colour picture mode. OM-Emu has no image pipeline. Monochrome
  grain reaches photos on the camera (alpha9 report). The OM-3 project reports colour grain made by the image
  processor; that is a different camera.
- Camera behaviour of grain with Reset, custom modes (C1..C5), power-off persistence, the Super Control Panel and
  live view. The grain carousel has no icons, as with Monochrome (known placeholders `0x38e7..0x38ee`).
