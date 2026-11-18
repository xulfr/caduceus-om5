# OM-5 Mark II 1.1 (E148): native effects map for Glow, Frame, Star Light, Split toning, Halation

Static analysis and OM-Emu, 2026-11-18. Nothing here is built. **Not camera-tested.** E148 addresses are runtime
addresses of the expanded main. The OM-3 and E-P7 results cited are those projects' camera results on other
bodies. They are not evidence for E148.

## Art Effect settings (OM-Emu observation)

Pop Art's Effect row, stepped Off → effect 1 → effect 2 and read through OM's getter and store 2 (context 0):

| ID | Off | 1 | 2 | Reading |
| --- | --- | --- | --- | --- |
| 369, 867 | 0 | 1 | 2 | Art Effect index (369 effective; 867 likely this filter's stored copy) |
| 393 | 0 | 1 | 0 | effect 1 on (Soft Focus) |
| 394 | 0 | 0 | 1 | effect 2 on (Pin Hole) |
| 396 | 0 | 1 | 1 | some effect on |

No other ID of 0..2299 changed.

## Art Effect → job flag converter (static observation)

- Entry `0x6042394c`: `a3 = (28,a0)`, then Art Effect id byte at `a3 + 29473` (`0x7321`), bounds 0..9, jump table
  `0x606058a8`. Cases OR the job flags at `(a2)`: Soft Focus `0x80`, Pin Hole `0x400`, Frame `0x8000`, White Edge
  `0x2000`, Star Light `0x40`, Diorama `0x100`/`0x200` (masking `~0x300`), Shade `0x800`/`0x1000` (masking `~0x1800`).
  The order matches OM-3's converter `0x60555e47` (OM-3 notes, "v0.20 Extras research").
- The tail clears `0x4000` and `0x10000`, then tests `a3 + 28736` (`0x7040`). OM-3's tail tests `capture + 37690`,
  which it calls the mono grain/filter route. The E148 offset role is inferred from that match.

- Lead, not the weight getter: `0x60389774` dispatches on Art Filter job keys `0x01010065..0x01030069`
  (table `0x60564c68`, 16 rows) and its cases also set `0x80`. This is probably how the Soft Focus *filter* gets the pass.

## What the OM-3 project did with the same converter (their camera results, other body)

- **Glow:** Color captures with no Art Effect get Soft Focus (`flags |= 0x80`) from a hook in the converter. The
  Soft Focus weight getter (OM-3 `0x605048c1`, stock weight 600) returns a per-strength weight (942..666).
  Live view needs a separate hook, gated for picture mode ≥ 100 (OM-3 `0x6046b8bb`).
- **Frame, Star Light, White Edge, Pin Hole:** the same hook with the other flags.
- **Split toning:** per-channel R/G/B curves in the development gamma stage. Their job copies 3 × 640-byte curve
  tables; a hook bends them in place. Cross Process uses different R/G/B curves natively.
- **Halation (from the E-P7 project, ported):** a CPU pass over the finished YCbYCr 4:2:2 buffer after the Soft
  Focus blend. On the OM-3, byte 1 = Cb and byte 3 = Cr, offset-binary (camera-proven there). It costs ~1.8 KB of code and
  up to a few seconds per night photo.
- **Code space:** OM-3 ran out and loads a relocatable code block from the card (GUIDES.BIN, tag-checked, with a
  relocator) into heap. That is the "load from the SD card" route in docs/V0.2.0-PLAN.md, proven there.

## E148 plan, cheapest first

1. **Glow (Soft Focus on Color Profiles).** Needs E148's Soft Focus weight getter and the live-view gate (search for
   OM-3's patterns), a per-profile Glow value (storage like grain), a sidebar row and a converter hook. Emulator can
   check flags. Only the camera can show the Soft Focus pass renders on Color Profile stills.
2. **Frame / Star Light** reuse 1's hook (one flag each).
3. **Split toning:** locate E148's gamma-stage copier (OM-3 `0x605169a4` pattern) and the R/G/B curve objects.
4. **Halation:** after 1, a CPU pass. It needs the card-loaded code block because it is ~1.8 KB.

Each step needs an owner camera test before the next builds on it.
