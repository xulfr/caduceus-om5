# OM-5 Mark II 1.1 (E148): Split tone on Color Profiles (v0.2.0-dev)

> **2026-11-20:** deltas are now looked up by the output level `c[i] >> 4`, not the table index (the tables are
> indexed by linear input; Highlight Tint showed nothing on the camera), and `st_tint` is at `0x6082976c`.
> [Report and fix](OM5II-DEV0565-CAMERA-2026-11-20.md).

Static analysis (objdump, Codex's Ghidra findings) and OM-Emu, 2026-11-19. **Not camera-tested.** OM-Emu
develops no photos, so the checks call the camera's own curve setter on test tables.

History: the first version (same day) was a Split Tone sidebar row, −5..+5, teal shadows / orange highlights only.
It is replaced by three tints set on the colour wheel (owner request: midtones too, any colour).

## What the user sets

Colour wheel of Color Profile 1–3, trash button: Saturation → Hue → Lightness → **Shadow Tint → Midtone Tint →
Highlight Tint** (P+0 axis 3..5). On a tint axis each of the 12 colours shows the tint's strength if the tint is that
colour, else 0. Writing 1..5 on a colour moves the tint there (the other children are refreshed to 0); writing 0
on the tint's own colour removes it; 0 elsewhere changes nothing; negative values count as 0. With INFO on "all"
the editor writes all 12 colours and the last one (Yellow-green) wins: use one-colour mode. Hold-OK reset clears it.

Storage, one cell per zone and profile (value store, through OM's writer so it is committed, saved, reset and copied
like the other profile settings): value = strength × 16 + colour (0..11, Yellow at the top, clockwise), 0 = none.
Cells `tint_ids` = 3·zone + profile: 968 969 970 / 971 972 973 / 974 975 964 (Color Profile 4's colour-sector
cells, value store; no stock descriptor). Descriptor: byte list of 96 entries at `0x60207318` (an identity table
0, 1, 2 … in section 1; inference: read-only data). In OM-Emu the untouched cells read 964 = −4, 968..970 = −1,
975 = −4 (factory defaults, presumably): both decode as "none" (colour ≥ 12 or strength ≥ 6 is ignored).

The descriptors (and Black / White's) are built in P at arming by `cad_build` (P+1204, 15 × 20 bytes) and linked
into OM's descriptor hash by `cp_nd_link` (nodes P+988..1171). Commit: `wb.s` maps 964..975 to profile
(id − 962) mod 3 and refreshes that profile's contexts.

## Image side

- E148's R/G/B curve setter `0x603e6974` (Codex Q1): a0 = job output O, a1 / d0 / d1 = R / G / B tables
  (256 × u16, 0..4095); stores them at O+0xa24 / 0xa28 / 0xa2c. Callers `0x603e6b3e` (gamma stage `0x603e69ae`)
  and `0x603e6f0b` (special filters), both `call …,[d2,a2],8`. It is a **leaf that returns with
  `retf [d2,a2],8`** (through MDR), and its 8-byte frame holds only the saved d2 / a2.
- Two traps, both hit in the emulator:
  1. Any `call` from code at its entry writes the return address at `(sp)`, over the saved a2.
  2. `call` and `mul` both write MDR, so the setter's final `retf` returned into Caduceus code and looped.
  The hook therefore makes no call: `st_entry` (ext2) checks the state handle inline, keeps MDR in d2 and jumps
  to `st_tint` (wb.s, section 4, now at `0x60829774`, 130 bytes, no `mul`).
- **Refresh (settings task, `tint_refresh`, ext8):** T[z] = strength × `tint_rgb`[colour] per zone, where
  `tint_rgb`[k] = round(64 cos(h − 120°·c)), h = 60° − 30°·k (c = R, G, B; sum 0, so roughly brightness-neutral).
  Then for table index i (u = i − 128, w = u²): delta_c[i] = (w · T[edge][c] + (16384 − w) · T[mid][c]) >> 14, edge =
  shadows for u < 0, highlights from the middle up. Shadows weigh 1 at black and fade by the middle; midtones peak at
  the middle; highlights weigh 1 at white. Written to the 3,088-byte buffer (class-1 heap, uncached) at +1552 / +2064
  / +2576; P+1176 (`ST_A`) = 1 when any tint is set (cleared while rebuilding). Strength 1 at full weight is 64 units
  of 4095 on the strongest channel (the old row: 60 per step).
- **Per job (`st_tint`):** when ST_A ≠ 0, c'[i] = clamp(c[i] + delta_c[i], 0, 4095) for R, G and B into the buffer
  (+0, +512, +1024) and those pointers go to the setter. Concurrent jobs write identical values.

Emulator (`tests/run_bw_tint.py` cases `cp1-tints`, `cp3-midtone`; `tests/st_assert.mjs` recomputes every delta from
the cells and checks every output entry), ramp 0..4095, Color Profile 1 with Shadow Tint Yellow 3 and Highlight Tint
Green-cyan 1:

| i | off R,G,B | tinted R,G,B |
| --- | --- | --- |
| 0 | 0,0,0 | 96,96,0 |
| 32 | 514 ×3 | 568,568,406 |
| 128 | 2056 ×3 | 2056 ×3 |
| 224 | 3597 ×3 | 3566,3627,3597 |
| 255 | 4095 ×3 | 4040,4095,4095 |

## Not shown

Whether the tint renders in JPEGs and live view, and whether strength 5 is too strong or too weak (camera test).
Whether the special-filter caller `0x603e6f0b` is reached in a Color Profile (ST_A is 0 in every other mode). The
`0x60207318` table being constant is an inference (identity bytes 0..255 after a pointer table). The camera's own
colour wheel display (the C3D reader hooked by `display_hook`) shows saturation on the tint axes.
