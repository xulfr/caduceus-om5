# OM-5 Mark II 1.1 (E148): Blacks / Whites in the tone curve (v0.2.0-dev)

Static analysis (GNU objdump, with Codex's Ghidra findings) and OM-Emu direct calls, 2026-11-18.
**Not camera-tested.** OM-Emu does not develop photos. The checks call the camera's own curve function on a
test table, so they test the table maths, not a picture.

## How E148 builds a photo's brightness curve (observation)

- Stage `0x603e863e` (a0 = context C; R = (4,C), O = (12,C)) points `O+0xa30` at a 256-entry u16 brightness
  table. It takes it from the art cache `R+1524` when set, or from `0x603e85de` (base table `0x603e7f72`,
  optional secondary `0x603e85aa`, composed into `O+0xa34`).
- Then, if gate `0x60385b9c` (a0 = `(1512,R)`; true when any of five u16 there is non-zero) passes, it copies the
  table into the job's own buffer `O+0xa34` (unless it is already there). It calls **`0x60385f08`** (a0 = that
  copy, a1 = `C+64`, d0 = `R+1802` bit 7) to bend it in place, then points `O+0xa30` at the copy and clears
  `O+4` bit `0x100`. Only caller of `0x60385f08`: `0x603e86f0`. The gate has five other callers
  (`0x6037a0b4`, `0x6037a0db`, `0x6037a936`, `0x60385c1c`, `0x603e736e`).
- `0x60385f08` evaluates splines on a 27-point grid (x = 0, 10 … 250, 255 at `0x6052e9c8`) via `0x60385d22`
  (fit) and `0x60385e5c` (evaluate), clamped to 0..1023:
  1. Spline A, 5 points `0x6052e9fe` = 0, 204, 473, 832, 1023: point 1 −= `p[+4]`, point 3 += `p[+4]`
     (a contrast-like S).
  2. Spline B, 8 points `0x6052ea08` = 0, 130, 473, 474, 476, 477, 832, 1023, applied to A's output. Copied to
     `(124,sp)`. **Point 1 += `p[+6]`, point 6 += `p[+8]`** at `0x60385f9c..0x60385fb0` (Shadows / Highlights
     by position; inference). The 473..477 cluster pins the middle.
  3. If `p[+10]` ≠ 0 or d0 = 1, spline C, 5 points `0x6052ea18` = 0, 130, 473, 832, 1023: point 2 += `p[+10]`
     (midtones; inference), points 1 / 3 += `p[+12]` / `p[+14]`.
  The 27 values are then expanded to the 256-entry table.

## Caduceus hook (built, inert until values are set)

- `bw_hook` `0x60385f9c` (5 bytes, no branch targets them) → `bw_apply` (ext2): if P is armed and
  `P+1052` (Blacks) / `P+1054` (Whites) are non-zero, raise point 0 by B and point 1 by 7B/8, and lower point 7
  by W and point 6 by 13W/16. Then replay the 5 bytes and `jmp bw_resume` (`0x60385fa1`). It uses d0, d1 and a0;
  the stock code reloads all three.
- `bw_gate_call` `0x603e86a8`: `call 0x60385b9c,[],0` → `call bw_gate,[d2],8`. That runs the stock gate, and also
  returns 1 when B or W is non-zero, so the curve is built even with every native tone value at 0.
- `st_ptr` reads the state handle through the uncached alias, so this is safe from the image pipeline's task
  and CPU. Unarmed means no effect.
- Negative result: an output-levels map of all 8 points (`y = B + y(1023−B−W)/1024`) moved middle grey
  514 → 482. The point-0/1/6/7 shape keeps it at 512.
- Assembler pitfall: `jmp 0x60385fa1` with a literal links as a raw displacement and jumped to `0xc0935607` (emulator
  fault). Use a linker symbol (`bw_resume`). New sections need both a `layout.ld` line and an `assembly.sections`
  entry plus a placeholder `ranges` row in `patch.json` before `--record`.

## Emulator results (tests/bw_assert.mjs; values at table index 0, 32, 64, 128, 192, 240, 255)

| Case | Gate | Output |
| --- | --- | --- |
| Off (B = W = 0, no tone) | closed | 0 128 257 514 770 963 1023 (identity) |
| Off + Shadows 40 | closed* | 0 167 292 514 770 963 1023 |
| B = W = +64 | open | 64 184 289 512 727 901 959 |
| B = W = +64 + Shadows 40 | open | 64 224 325 512 727 901 959 |
| B = W = −64 | open | 0 72 225 515 813 1023 1023 |

\*The gate reads the `R+1512` struct; the test passes an all-zero struct to the gate and the Shadows value only
to the modifier.

## Negative result: a new sidebar row item needs more than dispatch + list (emulator, scratch image)

A scratch image (not committed) added item `0x150a` in an empty slot of the row-item dispatch `0x611a0a98` (slot 4,
key `0x1504`). Its handler `mov 1017,d0; jmp 0x60e3cd53` follows the sharpness/contrast case path (type 0, setting in
`(4,sp)`). The item was appended as the eighth entry of the Color Profile row list (count 8). Result: the sidebar
drew only the seven known rows, and moving down to the eighth stopped the emulator (jump to `0x8940`, fault 3).
So a row item also needs entries in at least one more per-item table (left-column cell, icon or page). This is
the next Ghidra question, not more trial edits.

## Still to do (for a usable feature)

1. Per-profile storage (2 × 3 values; the IDs must default to 0 in the stock reset/init lists, see the CP grain note)
   and refresh writes of the active profile's values into `P+1052/1054` (0 for other modes).
2. Two Picture Mode sidebar rows (Blacks, Whites). Unlike grain, E148 has no ready-made row items for these.
3. Check that live view also goes through `0x603e863e` (the preview would then show the change).
4. Camera test: Blacks and Whites visible in JPEGs, no slowdown, no change with both at 0.
