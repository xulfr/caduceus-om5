# OM-5 Mark II (E148, stock 1.1): dev package 4f7aeb6c camera report, 2026-11-20

Owner report (physical camera), relayed in a Claude Code session. Package `DCOLYMP/E1489999.BIN`, SHA-256
`4f7aeb6c5d53d7d13bde1a77e9252e7358c9c3a5f74f9714d89eb6b078ce4636`, built 2026-11-20 with
`tools/oly_patch.py firmware/om5ii --write-untested-package` from branch `claude/wizardly-feynman-wejd65`
(commit `4ce7194`, no Color Profile grain, no cg1) against stock `9de5d77e…d637`. Flashed after the cg1 package
`f7f1db5d…2c51` boot-looped and stock was restored ([cg1 report](OM5II-CG1-CAMERA-2026-11-20.md)).

## Observations (owner)

| Feature | Result |
| --- | --- |
| Boot, general use | **Works.** |
| Split tone, INFO "all" on a tint axis | Still selectable. Behaves better than `7d611008`: only one colour (green / yellow, owner's impression) moves. |
| Black / White effect | **Works** in pictures. |
| Black / White in live view | **Not live:** the change appears only after a shutter half-press. OM's Sh / Mid / Hi update live view at once. |
| INFO hint "Black/White" (Hi/Sh state) | Text does not fit the hint box. Owner asks for "Bl/Wh". |
| Value labels "Blk n" / "Wht n" | Still larger than the stock Sh / Hi images. Owner asks for "Bl" / "Wh" (to match Sh / Hi). |

Not reported: Reset, C1–C5, power-off persistence, the 30 s Picture Mode timeout.

## What this shows

- Observation: `4f7aeb6c` boots; `f7f1db5d` (the same source plus probe cg1 and the 3-byte carousel table edit)
  boot-loops. So cg1 or the carousel edit causes the boot loop on this camera (inference from one flash each).
- Observation: Black / White through the split-tone delta tables (R/G/B curve setter route) reach JPEGs.
- Owner decision: colour grain is shelved; this build is the base for the next alpha.
