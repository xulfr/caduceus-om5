# OM-5 Mark II 1.1 (E148): Film Grain for Color Profiles (v0.2.0-dev)

> **2026-11-19: no grain on the camera.** Package `7d611008…1c7f`: the row and its values work, but **no grain is
> visible at any level** in colour pictures, and the carousel reads High, Std, Low, Off where Monochrome reads Off,
> Low, Std, High ([camera report](OM5II-V020DEV-CAMERA-2026-11-19.md); the order is reproduced in OM-Emu).
>
> Why (inference from the OM-3 project's camera work on E147, the closest body; not traced on E148): the stock grain
> pass runs only for monochrome development jobs. On OM-3, a colour development request needed its job key changed
> from 11 (COLOR) to 12 plus the grain level at request +1751 to get any grain, and key 12 then dropped other colour
> settings (Blacks/Whites, white-balance shifts, noise reduction) until the tone gate was patched. Their shipped colour
> grain is a texture pass on a work list (hooks on the work-list builder and combiner 1), reached after many camera
> rounds with freezes and restarts (Frame, Pin Hole on the conversion pass, Shading's getter during capture,
> RAW+JPEG). Source: androidfanman/caduceus-om3 `research/NOTES.md` at `e32363a`, sections gl1–gl10, gt1–gt4,
> ft1–ft9, rc1–rc2c, rj1. Effective 998 alone therefore cannot give colour grain on E148.
>
> (The carousel order is fixed since: see "carousel order fixed" below.)
>
> E148 leads for a real implementation: the Art Effect converter `0x6042394c` tests `a3 + 28736`, the field the OM-3
> converter uses for its monochrome grain/filter route ([effects map](OM5II-EFFECTS-MAP-2026-11-18.md)); 998's only
> direct references are its setting descriptors (`0x608623a2`) and a logger (`0x6072c992`). The E148 development
> request, its job key and the combiner selector are not located yet.
>
> Signature match of OM-3 (E147 1.1, same image base `0x60021020`) addresses against E148 (2026-11-19; masked call
> and 32-bit immediate operands; unique matches only): stage selector `0x6052cf39` → **`0x603ecda1`** (48 bytes),
> grain gains `0x60667dc2` → **`0x6053138e`** (48 bytes), development-request hook site `0x604955f1` →
> `0x6036fc5c` (24 bytes only: candidate). No match for combiner 33 `0x60505142`, the MONO grain gate `0x604b3f28`,
> the work-list builder, the Grainy Film handler or the Art converter (whose E148 address `0x6042394c` is known:
> the bodies differ by struct offsets). Next step for a real implementation: Ghidra cross-references from these
> anchors, then a logging probe on the camera as OM-3's gl1–gl3 (OM-Emu has no image pipeline).
>
> **Removed from the v0.2.0-dev build** (owner, 2026-11-19): `cp_nd.py` `CP_GRAIN = False` drops the row, lookup
> and descriptor edits; the refresh writes 998 = 0 for Color Profiles again (no `0x4000` stride), `CP_NDESC` = 5,
> and wb.s no longer maps 907 / 911 / 915. The trash-button fix on the grain row stays (Monochrome has the row).
> The experiment continues on `claude/cp-grain-experiment`.

Static analysis and OM-Emu only, 2026-11-18. **Not camera-tested.** Addresses are runtime addresses of the
expanded main program. OM-Emu `bdb33470`, GNU binutils 2.42 `mn10300-elf`.

## 2026-11-19 (later): E148's development request located; probe cg1 (static analysis + OM-Emu only)

Static analysis of the expanded E148 1.1 main (objdump, GNU binutils 2.42; Ghidra 11.4.2 import for cross-checks)
against OM-3 E147 1.1 (`caduceus-om3` NOTES gl1–gl10, gt1–gt4, ft1–ft9, rc1–rc2c, rj1 read first). **Not
camera-tested.**

**Observations (E148 code):**

| What | E148 | OM-3 E147 | Evidence |
| --- | --- | --- | --- |
| Combiner selector | `0x603ecda1` | `0x6052cf39` | same body; request at context +4: kind +16, stage +12, flags +14 |
| Context key | context **+52** | +48 | `mov (52,a0),d2` at `0x603ecde7`; hash table `0x60576aa8` `{key − 11, case}`: 0x1 (key 12, MONO) → `0x603ecebb` (stage 0x0901 / 0x0902 → combiner 31 / 32), GF I / II `0x01010068` / `0x01020068` → `0x603ece2e` (stage 0x0100 → combiner 1; E148 also tests request +1807 == 2 there); no entry for key 11 (default `0x603ecf43`) |
| Request configuration | `0x6036fc58`, selector call at **`0x6036fc5c`** `call SEL,[d2,a2],12` (`dd 45 d1 07 00 a0 0c`) | `0x604955ed` / `0x604955f1` | then combiner config `0x60372fdb` (OM-3 `0x60504779`); one direct caller `0x6036f801`. The second selector call (inside combiner set-up) is `0x603d8112` (OM-3 `0x60504b5d`) |
| Development effect | request **+1838** (kind 0 / 16), kind 3 +656 | +1756 / +1084 | getter `0x603ed07a` (OM-3 `0x6052d1a9`); effect 0x0c00 selects combiner 33 (OM-Emu, below) |
| Grain level | request **+1828** | +1751 | combiner-31 handler reads it at `0x603d85b2` and indexes the gains `0x6053138e` (110/300/600); combiner 32 at `0x603d8649` |
| Request builder | `~0x6038acd3..` | — | copies job +5551 → request +1828, +5552 → +1829, clears +1838 |
| MONO-only grain copy | **`0x6041ef09`**: `if key == 12` snapshot +28766/+28767/+28768 → job +5550/+5551/+5552 (second copy at `0x60422067`) | `0x6054fd52`, `0x60553e44` | so a COLOR job never gets a grain level: the reason the restored row showed nothing |
| Key writer | `0x604237fc` (OM-3 `0x60555d10`) | | params +10 = picture-mode byte (snapshot +28735; mapping `0x6037f16a`: default = that byte), before the Art Effect converter `0x6042394c` (callers `0x6041e91a`, `0x60421924`) |

Inference: E148 runs the same grain machinery as OM-3, at different struct offsets. Color Profile stills carry job key 11
(picture-mode byte 11, as `apply_values` already documents); the key-12 recipe OM-3 proved on its camera (gl6/gl7:
request +10 = 12, grain level, context key 12 at configuration time) should therefore apply. Not yet observed on E148:
the still request's +14 = 0x1000 and +10 = 11 (taken from OM-3's logs), and whether key 12 drops Color Profile
settings as it dropped Blacks/Whites, WB fine-tune and NR on OM-3 (gt3) until their tone gate was patched (gw1).

Logging probe: not feasible now. OM-3 logged to a card file from a 16 KB code block; E148 has about 120 bytes of free
tail space left (ext8 88, ext9 64, ext3 48 unreferenced bytes per the space map), and no card-loaded code yet.

**Probe cg1 (`firmware/om5ii/cg.s`):** the 7-byte selector call at `0x6036fc5c` becomes `call cg_sel,[d2,a2],12`
(same frame); `cg_sel` (81 bytes, ext8 `0x613f2ec8..0x613f2f19`) passes every request to the stock selector, and
first, only for a kind-0 request with +14 = 0x1000, +10 = 11 and +1838 = 0 (no own effect), reads effective setting 998
(store 0, context 0, `0x602f514d`, the element read `active_read` also uses) and, for 1..3, writes request +1828 =
level, +10 = 12 and context +52 = 12. Grain Off (default) = stock request. The Shading gate avoids combiner 33's mono
set-up (OM-3 gl3: grey). The settings getter OM-3 found unsafe during capture (v0.24's AGET reboot) is not used.
Emulator bug caught on the way: `0x602f514a` is a `calls` entry (own `add -4,sp`); `call` must target `0x602f514d`.

OM-Emu (`tests/run_cp_grain.py`, 7/7; `tests/cg_probe_assert.mjs` calls `cg_level` and `cg_sel` on a fake request in
heap memory after the GUI steps): CP1 Low → level 1, the COLOR still request gets +1828 = 1, key 12, context 12;
CP2 High → 3; CP2 / stock mode / Monochrome 1 after CP1 Low, and CP1 Off → 0 and the request untouched. In every case
live view (+14 0x0130), kind 3, a MONO request and a request with effect 0x0c00 are untouched (0x0c00 → combiner 33,
as on OM-3). OM-Emu has no image pipeline: whether grain appears is a camera question.

## 2026-11-19: carousel order fixed (OM-Emu; not camera-tested)

Observation (OM-Emu call trace of opening the grain row, Monochrome 1 vs Color Profile 1, then static): the carousel
builder `0x60e2c539` (and 14 other carousel sites, each the same loop over 0x144 IDs) draws a setting high to low when
its ID is in the table `0x61197b8a`. 907 / 911 / 915 are entries 235 / 239 / 323 (Color Profile 4's Sharpness,
Contrast and Shading, which run high to low); 999..1002 are not listed. `cp_nd.py` `cp_grain_order_907/911/915`
replace them with their neighbours 906 / 910 / 914, which the table already lists, so no other setting changes (E148
has no Color Profile 4). The Color Profile carousel now reads Off, Low, Std, High, and right steps up, as Monochrome.
`run_cp_grain.py` steps now go right; the build without the fix fails `cp1-low` and `cp2-high` (control).

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
