# OM-5 Mark II 1.1 (E148): Black / White and tints in live view — the gamma-stage cache (2026-11-20)

Static analysis (GNU objdump) and OM-Emu, 2026-11-20. **Not camera-tested.** OM-Emu runs no live-view development, so
the emulator checks the hook's logic, not the picture.

## Problem (owner, package `4f7aeb6c…4636`)

Black / White and the split-tone tints reach photos, but live view shows a change only after a shutter half-press.
OM's own Sh / Mid / Hi update live view at once. [Camera report](OM5II-DEV4F7A-CAMERA-2026-11-20.md).

## What differs (observation)

- A Black / White or tint edit and an OM tone edit take the same commit and refresh path (`wb_load` → `wb_profile`
  → `pm_refresh` → `rt_tail` → `bw_refresh`). OM-Emu call traces of the refresh's writes of effective 383 / 691 / 382
  are identical between the two except for the value store's save-dirty marker (`0x6005fc17` → `0x6005f98a`, byte
  `0xa26c857a`, read by the flush path `0x600604d7`): nothing there signals the image side. Dead end, recorded.
- The gamma stage `0x603e69ae` keeps a **cache record per pipeline**: `d3 = (R+1484) + 5736` (R = context +4). It
  holds the selected R/G/B table pointers (+0/+4/+8, from `0x603e644a`), a descriptor (+12..: four halfwords built by
  `0x603e2e97`), and the cached results (+20..+35). At `0x603e6a3b..0x603e6a85` it is a hit when d3 ≠ 0, R+1838 ≠
  0x101, O+60 has none of the bits `0x4460001e`, `0x603ed185` returns 0, the three pointers match and
  `0x603ed982` returns 4. **On a hit it skips the curve setter `0x603e6974`** (`jmp 0x603e6b8b`, which clears O+108
  bit 0) and the hardware keeps its curves; on a miss it calls the setter (`0x603e6b3e`) and refills the record
  (`0x603e6b43..`).
- Inference: OM's tone edits select different tables (a miss); Black / White and tints change only Caduceus's delta
  tables in P (applied in the setter hook `st_tint`), so live view kept hitting until the half-press rebuilt it.
  The per-pipeline cache suggests live view runs the stage repeatedly; that is what makes a forced miss enough
  (camera test).

## Initial fix (package 0565540a)

- `gs_hook` at `0x603e6a3b` (6 bytes: `cmp 0,d3; beq 0x603e6aa3; mov (56,sp),a0` → `jmp gs_entry; nop`), code in
  ext8 (section 2 had 19 bytes free). The choice relied on an incorrect section-load order. No call; uses d0, d1, a0, a1 (reloaded by
  the stage), keeps d2 / d3 / sp.
- `bw_refresh` adds 1 to `P+1504` (`GS_GEN`) after each table rebuild (every Color Profile refresh of context 0, and
  the refresh that clears the tables in other modes).
- Once armed, a cache record not seen at the current `GS_GEN` takes the stock miss path once (`P+1508`: 4 × {record,
  generation}; a full table reuses its last entry). d3 = 0 and unarmed are stock. P grows 1528 → 1544 bytes.
- `tests/gs_assert.mjs` (via `run_bw_tint.py`, cases `cp1-gs-baseline`, `cp1-bw-gamma-cache`, `cp1-wheel-gs-baseline`,
  `cp1-tint-gamma-cache`): runs the hook from `gs_entry` with fake records — miss / hit / generation / second record /
  full table / unarmed — and checks that Black / White and tint edits raise `GS_GEN` above a session with the same keys
  and no value change (11 vs 8).

## Not shown

Live view on the camera; whether more than four gamma caches exist (then the fifth and later share one entry and
miss more often: extra recomputes, no wrong output); cost of one recompute per cache after each profile refresh.


## Startup follow-up (emulator only)

With section-ready mask 3 and no state handle, the original hook enters section 8 even for a null cache.
Candidate `c3bc45c` keeps the initial checks and stock exits in section 2 and enters section 8 only when armed
and all ten ready bits are set. [Exact-build comparison and trace](OM5II-DEV0565-CAMERA-2026-11-20.md#startup-comparison-and-wheel-fix-2026-11-20-emulator-only).
