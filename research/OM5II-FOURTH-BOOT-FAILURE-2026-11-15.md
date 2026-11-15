# Fourth OM-5 Mark II boot failure: alpha5 (2026-11-15)

**Camera result, negative.** Reported by the owner (xulfr) in the session that produced alpha5.

| | |
|---|---|
| Camera | OM-5 Mark II (E148), stock firmware 1.1 |
| Package | v0.1.0-alpha5, `DCOLYMP/E1489999.BIN`, made by the repository launcher / `patch.py`, which writes the file only when it equals SHA-256 `98bd2433bef76706f4c71706439feb23d05524477b4d078135c1675ab97880c2`. The owner did not report the printed checksum separately. |
| Card | `DCOLYMP` and `OM5MOD/LOOKS.BIN` (starter bank `5e72b197…522c`) at the top level. |
| Procedure | Hold OK, switch on. The first-flash plan's step 0 (flash OM's own 1.1 first) and step 1 (no `OM5MOD`) were not followed. |
| During the update | A **red** light, then after about a minute a blinking light. (Install guide expects a steady orange light, then blinking.) |
| Outcome | After a power cycle: **immediate boot loop**. |
| Recovery | OM's 1.1 (`card/restore/DCOLYMP/E1489999.BIN`) flashed from the card and the camera restored fine. |

## What it tells us

- The loop starts at power-on, before any shutter half-press. Nothing in films.s runs before arming, and
  `LOOKS.BIN` is only read after a half-press, so the `OM5MOD` folder is not a candidate cause.
  The candidates are the parts that act during boot without the half-press gate:
  - data edits: the Color/Monochrome Profile table edits (`color_profile_01..55`), the ND selector and the
    setting-1710 allowed list;
  - the resource-component alias edit (`profile_icon_aliases`, component 0x101);
  - hooks reached during settings initialisation: `refresh_hook`/`refresh_cases` (picture-mode refresh, gated
    only by section-5 bit), `creset_hook`, `wb_hook` (gated by section-6 bit), the four `pm_s*` mode-list copies
    (no gate), `arm_hook` (runs the stock call first);
  - the loaded-tail extensions themselves (ext2, ext5, ext6, ext7, ext8, st8, ext10) if the real loader does
    not copy those tail bytes the way the end-selector audit assumes.
- This is the first camera run of the heap-state design (no image stores), which OM-Emu passed. It differs from
  the 8 November failure (started, froze on the Picture Mode screen, then looped). It resembles the 4/5 November
  failures in starting before any user action. OM-Emu again did not predict it: it does not run E148's loader.
- The red light during the update is unexplained. It may be normal for this camera or this card; the owner's
  step-0 flash of OM's own file with the same card would show which.
- Alpha1–alpha4 were never flashed but share this startup code; treat them as failed too.

## Suggested next steps (not done)

1. Bisect on hardware with the smallest possible builds, owner-approved, starting with a package that changes
   one inert byte inside a declared range, then the data edits only, then the resource alias only, then the
   hooks only. Each step is a separate, recorded camera result.
2. Ask the owner whether the camera was left on a Color Profile or with C1–C4 holding one before the update,
   and whether the red light also appears when flashing OM's own 1.1.
3. Compare with `OM5II-BOOT-LOOP-TRACE-2026-11-05.md` and `OM5II-SECOND-BOOT-FAILURE-2026-11-05.md`.

`patch.py` now refuses alpha1–alpha5 (`blocked` in each release's patch.json) and `tools/oly_patch.py` lists the
alpha5 package as a known boot failure.
