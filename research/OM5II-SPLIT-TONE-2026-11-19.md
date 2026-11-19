# OM-5 Mark II 1.1 (E148): Split tone on Color Profiles (v0.2.0-dev)

Static analysis (objdump, Codex's Ghidra findings) and OM-Emu, 2026-11-19. **Not camera-tested.** OM-Emu
develops no photos, so the checks call the camera's own curve setter on test tables.

## Image side

- E148's R/G/B curve setter `0x603e6974` (Codex Q1): a0 = job output O, a1 / d0 / d1 = R / G / B tables
  (256 × u16, 0..4095); stores them at O+0xa24 / 0xa28 / 0xa2c. Callers `0x603e6b3e` (gamma stage `0x603e69ae`)
  and `0x603e6f0b` (special filters), both `call …,[d2,a2],8`. It is a **leaf that returns with
  `retf [d2,a2],8`** (through MDR), and its 8-byte frame holds only the saved d2 / a2.
- Two traps, both hit in the emulator:
  1. Any `call` from code at its entry writes the return address at `(sp)`, over the saved a2. The emulator
     reported "bad return state" with a2 = the call's return address.
  2. `call` and `mul` both write MDR, so the setter's final `retf` returned into Caduceus code and looped.
  The hook therefore makes no call: `st_entry` (ext2) checks the state handle inline, keeps MDR in d2 and
  jumps to `st_tint` (wb.s, fixed at `0x60829764`, section 4). That code saves d3 / a3 with `movm`, keeps O,
  MDR and G in the buffer's tail and restores MDR before rejoining the setter at `0x603e6979`.
- When the active Color Profile's amount A ≠ 0: for i = 0..255, u = i − 128, d = A·u·|u| / 2^14,
  R' = R + d, B' = B − d (clamped 0..4095), G unchanged. +A gives teal shadows and orange highlights; −A the
  reverse; i = 128 unchanged. R' and B' are written to a 1,552-byte heap buffer (class 1, allocated by the refresh
  in the settings task, uncached alias). Concurrent jobs write identical values.

Emulator (tests/st_assert.mjs), ramp 0..4095, A = 180 (Split tone +3):

| i | off R,G,B | +3 R,G,B | −2 (A = −120) R,G,B |
| --- | --- | --- | --- |
| 32 | 514,514,514 | 413,514,615 | 582,514,446 |
| 128 | 2056 ×3 | 2056 ×3 | 2056 ×3 |
| 224 | 3597 ×3 | 3698,3597,3496 | 3529,3597,3665 |

## Picture Mode row

- Item **5358** (key slot 8 in the 32-slot tables), title string 3838 (an internal name) overridden with
  "Split Tone" in films.s `fl_str`, slider −5..+5 like Shading. Storage 971 / 972 / 973 (Color Profile 4's
  colour-sector cells, part 0; default 0). The refresh writes A = 60 × value into P+1128 for context 0.
- **The 16-slot row-widget table `0x611b7aa8` must keep an empty slot.** It uses open addressing, and filling
  its last free slot made every lookup for a missing item loop for ever (emulator fault 7 at `0x60e49f65`). None of the
  new rows is entered there. `row_widget` hooks its lookup at `0x60e49f45` and sends items 5354..5358 to the
  slider handler `0x60e49fdf`.
- Tests: `tests/run_bw_rows.py` cases `cp1-split+3`, `cp3-split-2` and `split-after-cp1`.

## Not shown

Whether the tint renders in JPEGs and live view, and its strength (camera test). Whether the special-filter
caller `0x603e6f0b` is reached in a Color Profile (P's amount is 0 in every other mode).
