# Fourth OM-5 Mark II boot failure: alpha5 (2026-11-15)

> The later loader audit corrected the submission order to 1–10.
> Section 8 follows section 7. [Disassembly findings](../HANDOVER.md).

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

## Owner's answers (15 Nov, after the report)

- No Color Profile or Monochrome Profile was selected, and no C1–C4 held one, before the update.
- The **red light also appears when flashing OM's own 1.1** with the same card. It is normal for this camera/card
  and is not a symptom. (INSTALL/SAFETY describe an orange light; they should say the light may be red.)

## Static investigation (15 Nov, no camera, no flash)

The owner asked for code inspection only. Evidence below is static analysis of the pinned E148 1.1 main
(`objdump -m am33-2`) plus OM-Emu probes; OM-Emu builds its booted state before any probe can attach and does not
run the loader, so it cannot observe start-up.

### New fact from the camera run

The recovery flash ran the card updater **from alpha5's own image** (FIRMUP_CLI is in section 7, started by task 92
after section 6). So on the camera, with alpha5 installed: the base boot, the loader, sections 1–7 including the
hardware LZ4 decode of the patched sections 6 and 7, and task 92 all worked. The fault is in something that runs on
a normal start but not in update mode: sections 9/10 loading, application start-up (settings restore, picture-mode
refresh, GUI and live view) or later.

### Ruled out (with evidence)

| Candidate | Why it is ruled out |
|---|---|
| Truncated compressed streams (sections 6/7 grew by 875 / 1,036 bytes) | The loader reads the length from each stream's own header and fetches whole 2 KiB blocks (`0x6005b249`); the camera decoded section 7 well enough to run the updater. Offset/literal statistics match stock. |
| String-getter hook `0x60d52ed5` (new since 8 Nov, runs on every start) | Built bytes are `jmp 0x612a4f04; nop`; `fl_str` replays `mov d0,d2; call 0x60d52eec,[],0` (which returns by `retf`/mdr) and `jmp 0x60d52edb`; all 67 stock callers use the matching `[d2],8` frame. Only IDs 2749–2754/2859–2861 reach `st_ptr` (section 8, loaded before 7); section 10 is entered only when armed. |
| "Armed" handle not zero at power-on | The HLS manager is a static object at `0x6218c250` (lazy init `0x6085c6bc`). Its initialiser writes +0xAC with a 16-bit store and never touches +0xAE, but the start-up clear `0x600286da` zeroes `0x6205bd80..0x6259ed80`, which contains it. |
| Section constructor tables running into patch code | Runners at `0x601ae87a..` use fixed byte counts; tables end at `0x605af4b0` (sec 2), `0x612a4b94` (sec 7), `0x613f2b78` (sec 8), before each patch tail. |
| Stock code using the "free" tails we fill | A dword scan of the stock image at every alignment finds no pointer into ext2/ext5/ext6/ext7/ext8/st8/extvec/ext10 except coincidental instruction bytes, and one compare bound (`0x616595d4` uses `0x6169c820` as the end of a stock table; it never reads past it). |
| Section 10 checksum | Only the loader descriptor and end selector reference section 10's bounds. |
| `LOOKS.BIN` / `OM5MOD` on the card | Read only after arming on a half-press; the loop is immediate. |
| Arming at power-on without a half-press | In OM-Emu, arming event `0x02000100` is S1 down (`0x02010100` is the release); no such event occurred during the emulated start. Weak evidence: the real HLS start-up is not modelled. |
| `pm_num` writing 903/989 = 0 at mode recall | 0 is E148's own blank-store default for both (OM-Emu runs the firmware's blank-store init). |

### Hazards found (not shown to be the cause)

1. **The picture-mode lookup now depends on hidden settings.** `color_profiles.py` extends the group records of
   setting 111 to `(111, 361, 903, 989)` and of 504/505 to `(…, 1060, 1061)` / `(…, 1064, 1065)`. With 903 = 1 and
   Natural selected, alpha5 reads 111 = **63** where stock reads 1 (OM-Emu, `ui_write(903, 1)`). A record that
   matches nothing resolves to the last entry. 63 (ART16) is a real entry of stock's table, so this is probably not
   a crash by itself, but any non-zero value in these hidden settings would make every start use the wrong picture
   mode, and stock never shows or resets them (they survive a stock restore). Their values on the owner's camera are
   unknown. Stock references 903/989 directly in only a few places (two plain reads each).
2. **A hardware access monitor covers unloaded sections until section 10 loads.** After each section is finalised,
   `0x60046506..0x60046569` programs registers at `0x99700040..` with the range from the next section by index to
   the end of section 10, and `0x60059278` turns it off after section 10. Alpha1–5 are the first builds to put code
   in section 10 (`ext10`, and the pointer to it in section 8's last word). No path was found that touches section
   9/10 before arming, but what the monitor traps (CPU writes, reads or bus-master access) is not known and it is
   not modelled by OM-Emu.

### What alpha5 changed relative to the 8 Nov build, which booted

From the 11/12 Nov notes and this repository: state moved to a heap block armed on the first half-press (WB commit,
Delete and editor paths are now inert at start-up); the refresh case passes the profile in `d2` instead of storing a
byte; `st8` (281 bytes) and the extension vector (section 8's last word); H/L −7..7; `wb_extension` moved to
`0x605af590`; then the looks layer (string hook, `pg_title`, `ext10`). Tables, carousel, resource aliases, ND and
the start-up guards are unchanged. The exact 8 Nov source (`fix/om5ii-startup-readiness` at `25a336e` in the old
repository) was not fetched: CLAUDE.md forbids re-exploring the old repositories without the handover calling for
it. A byte diff of that build against alpha5's start-up paths is the most direct next static step if the owner
allows it.

## Suggested next steps (not done)

1. Bisect on hardware with the smallest possible builds, owner-approved, starting with a package that changes
   one inert byte inside a declared range, then the data edits only, then the resource alias only, then the
   hooks only. Each step is a separate, recorded camera result.
2. Ask the owner whether the camera was left on a Color Profile or with C1–C4 holding one before the update,
   and whether the red light also appears when flashing OM's own 1.1.
3. Compare with `OM5II-BOOT-LOOP-TRACE-2026-11-05.md` and `OM5II-SECOND-BOOT-FAILURE-2026-11-05.md`.

`patch.py` now refuses alpha1–alpha5 (`blocked` in each release's patch.json) and `tools/oly_patch.py` lists the
alpha5 package as a known boot failure.
