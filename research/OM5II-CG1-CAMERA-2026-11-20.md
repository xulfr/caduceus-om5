# OM-5 Mark II (E148, stock 1.1): colour grain probe cg1 camera report, 2026-11-20

Owner report (physical camera), relayed in a Claude Code session. Package `DCOLYMP/E1489999.BIN`, SHA-256
`f7f1db5d8d2726abe35f82451965736538d0451a5d3d9e9835b8978abb862c51`, rebuilt on 2026-11-20 with
`tools/oly_patch.py firmware/om5ii --write-untested-package` from branch `claude/cp-grain-experiment`
(commit `72d9e8f`) against stock `9de5d77e…d637`. The rebuild reproduced the hash recorded in HANDOVER exactly.

## Observations (owner)

| Step | Result |
| --- | --- |
| Flash the package | **Failed: the camera boot-loops** after the update. |
| Restore stock (`restore-stock/`, OK + power) | **Successful**; camera back on stock 1.1. |

Not reported: how far the boot got (logo, live view), whether any setting or picture was reached.
No grain, carousel or PR #11 feature check was possible.

## What this shows

- Observation: package `f7f1db5d…2c51` does not boot on the owner's OM-5 Mark II. The update path and stock restore
  still work.
- The package carries, relative to the last good flash (`7d611008…1c7f`): probe cg1 (`firmware/om5ii/cg.s` in ext8 and
  the call at `0x6036fc5c`), the carousel reverse-order table edit (`0x61197b8a`, 3 bytes), and the never-flashed
  PR #11 fixes (dev package `4f7aeb6c…4636`: Black / White via split-tone tables, tint axes, 30 s Picture Mode timeout
  with 9 timer arms + re-arm, Blk / Wht labels, heap-built descriptors and first use of the section 3 / 9 FF tails).
- Hypothesis (unresolved): the boot loop comes from the PR #11 changes rather than cg1, since cg1 only runs on a
  still development request and should not be reached during startup. Not yet distinguished.
- The emulator suite (20/20) and build audit passed on this source on 2026-11-19; they did not catch this failure.

## Next step

Flash dev package `4f7aeb6c…4636` (branch `claude/wizardly-feynman-wejd65`, PR #11 fixes without the Color Profile
grain row or cg1). If it also boot-loops, the fault is in the PR #11 set; if it boots, cg1 / the carousel edit is
implicated.
