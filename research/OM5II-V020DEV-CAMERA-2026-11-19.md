# OM-5 Mark II (E148, stock 1.1): v0.2.0-dev camera report, 2026-11-19

Owner report (physical camera), relayed in a Claude Code session. Package `DCOLYMP/E1489999.BIN`, SHA-256
`7d611008b9622608bcc3d950e5c049a89cfa329fd681c5ebb0a12ee6d8491c7f`, built with `tools/oly_patch.py firmware/om5ii`
from branch `claude/sharp-cray-0up4d3` (commit `524539a`). The handover's short form `7d611008…8c7f` was a typo for
`…1c7f`. Flashed with OK+power from slot 1; the camera boots and works.

## Observations (owner)

| Feature | Result |
| --- | --- |
| Boot, general use | Works. |
| Black / White on the tone page | UI works (INFO cycle, labels, values). **No visible effect** in live view or in the taken photo. The Black / White labels are drawn noticeably larger than the stock Sh / Hi labels. |
| Film Grain on Color Profiles | Row and values can be selected. **No grain visible** at any setting. The carousel's level order is the reverse of Monochrome's. |
| Split tone (colour wheel tints) | UI and effect work: visible in live view and in saved photos. With INFO on "All" the tint axes behave inconsistently (scrolls jump, a seemingly random colour changes). |
| Picture Mode | Owner asks for a longer idle timeout than 8 s (about 30 s). |

Not reported: Reset, custom modes C1–C5, power-off persistence, other picture modes.

## What this shows

- Observation: the R/G/B curve setter route (`0x603e6974`, wb.s `st_tint`) reaches both live view and JPEGs on E148.
- Observation: the brightness-curve modifier route (`0x60385f08` via `bw_hook` / `bw_gate`) produced no visible change.
  Hypothesis: that stage is not used, or its table is replaced, for Color Profile captures and live view. Untested
  which; the fix moves Black / White onto the R/G/B route instead (see the Black / White note).
- Observation: effective grain 998 set for Color Profiles (emulator) does not produce grain in colour pictures.
  Monochrome grain does (alpha9 report). Hypothesis: the grain pass is gated on the monochrome route.
