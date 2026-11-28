# Phase 4 static traces: Sharpness −5..+2 and Color Mix (2026-11-28)

**Static only (objdump of pinned stock E148 1.1, runtime addresses, base `0x60021020`). Nothing built or hooked.**
Leads from OMKit's E148 docs (necrostaz/omkit `cc55893`, docs CC BY 4.0: `docs/platform/om5m2/fw1100/imaging.md`,
`still-pipeline.md`, `color-pipeline.md`); OMKit's camera results are OMKit's, not evidence for this build. The OM-3
project's Sharp (v0.22) is the model for Sharpness; its results are the OM-3's (E147).

## Sharpness: where a still's sharpness comes from (observation)

1. **The capture read, key `0x8119`.** At `0x6034138d` the firmware calls the generic key reader `0x6005faa9` with
   `d0 = 33049` (`0x8119`), `d1 = d3`, `a0 = 0`, and stores the byte at **request `+5522`** (`0x60341397`). It is the
   same key the OM-3's Sharp hooks on E147. A second branch (`0x6034130d`, `(40,sp)+362 == 6`) reads key `0x9cc9`
   (40137) into the same field (`0x6034131f`): a different shooting kind, to identify before hooking.
2. **Into the pass block.** `0x6038accb`: `B+1795 = request+5522` (with `+5523..+5527` → `B+1796..1800`, contrast,
   gradation, saturation, noise filter ... per OMKit's `B+1795..1804` list). `0x60387549` clears `B+1795` on another
   path (job kinds that carry no picture settings).
3. **Change detection.** `0x6037a1bc` copies `B+1795` to job `+5701`; `0x60379f5b` compares them and clears change bit
   `0x100` when equal (OMKit: the colour builder's change mask).
4. **The detail block's parameters.** `0x603dd84c` copies `B+1795` into a parameter block on its stack (`(184,sp)`,
   with `B+1799` noise filter at `(185,sp)`, `B+1797` at `(186,sp)`, `B+1804` at `(187,sp)`), then builds the job
   (`0x603dd97c` → `0x603ed217`). OMKit: the detail block `0x1800` is set up for class 1 / 2 outputs (`0x6036fbbb`).
5. **Stock range.** Sharpness is −2..+2 here (IDs 904+p, 7). The live view uses its own path (OMKit:
   `0x6034f966` reader; the OM-3 kept the camera's value in live view).

**To do before building (the OM-3 v0.22 way):** wrap the `0x8119` read at `0x6034138d` (5-byte call): when armed and a
Color Profile is active, return the profile's extended value −5..+2 instead (the OM-3 sends −5 as −7 = off on E147).
Still open: what `B+1795` value E148's detail block takes as "off" and how far it accepts (the table behind
`(184,sp)` in `0x603ed217`'s callees), and the `0x9cc9` branch. UI: the Sharpness slider row from 5 to 8 steps (the
rows note's slider style / value-label lookups `0x60e4b02c` / `0x60e4b09d`).

## Color Mix: the colour matrix site (observation)

- **The colour builder `0x603e8fba`** (OMKit's hook site, camera for OMKit) builds S for a job (a0 = ctx, kept in
  d3; S = `(ctx+12)`): at **`0x603e8ff3`** it calls the matrix build `0x603e509a` (`call …,[d2,d3,a2,a3],84`, 5 bytes)
  with a0 = **S+80** (9 × s16 Q7, rows sum to 128), then the gamma stage `0x603e69ae` at `0x603e8ffa` (where our
  `gs_hook` sits), then the "six axes" `0x603e5ed6`.
- `0x603e509a` multiplies with `0x603e4cad` (3 × 3, Q8) and normalises rows with `0x603e4f0c` (calls at
  `0x603e5146` / `0x603e5242`).
- The matrix is written for every job (OMKit: "the matrix and the gamma pointers are written in every build"), so a
  mix applied after `0x603e509a` returns reaches both live view and stills without a cache.

**Plan (not built):** a 5-byte `jmp` at `0x603e8ff3` to a stub that makes OM's call, then (armed, Color Profile, mix
set) S+80 = Mix × S+80 in Q7 with each row brought back to 128 (as `0x603e4f0c` and OMKit's ispdrv do; grey stays
grey), then back to `0x603e8ff8`. The OM-3's Color Mix moves R, G, B toward their neighbours in linear light after the
WB gains: that is this matrix's place (WB gains act on the RAW before it). Storage: 6 values per profile (R, G, B ×
Sat / Hue), the same question as the curves had (slot-4 cells: 1015, 1050, 1054 are left in the save / copy / reset
lists, see the [storage note](OM5II-RGB-CURVES-STORAGE-2026-11-28.md); 6 × 4 bits fit one cell per profile).
