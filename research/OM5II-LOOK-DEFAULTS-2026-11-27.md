# Looks as a Color Profile's defaults: the "changed" mark and Hold OK reset (2026-11-27)

**Static analysis and a strict build only.** OM-Emu was not available in this session, and no camera has run this
code. Addresses are runtime addresses of the expanded main program, E148 firmware 1.1 build 1100.

## Owner report (2026-11-27)

On a Color Profile holding a look:

1. After a setting is changed, the Picture Mode screen shows no star next to it.
2. **Hold OK** sets the setting back to 0. It does not return to the look's value. The owner's example was black
   levels.

## Where OM takes a setting's default (observation, static)

- The settings object comes from `0x608eedd3` (global `0x61e44380`). Its vtable is at `0x60bb6ad0` (constructor
  `0x608eee3f`).
  - `+0` (`0x608efc53`) is the setter. It reaches `0x6091c624`, the function that holds `read_hook` and `write_hook`.
  - `+8` (`0x608ef257`) is the value getter. It goes to `0x6091be54` and does not pass through `read_hook`, so the
    colour cells read as their saturation.
  - `+152` (`0x608ef2b4`) is the **default value**. It goes `0x6091beb4` → `0x602d0060`.
- The Picture Mode panel's "changed" check `0x60e4ae7b` is called from the wheel row at `0x60e4acf8` and
  `0x60e4ad92`. It runs through the row's ID list (object at panel + 4444, vtable +8 count, +16 ID) and compares
  getter `+8` with default `+152` for each ID. A difference sets the row status bytes (panel + 4300 + 9 / + 10).
  The second compare in that block, at `0x60e4b10e`, uses the same two methods.
- The Hold OK resets in the editor code read the default with `+152`, then write it with the setter `+0` (`d1 = 0`).
  Examples are `0x60e91c1d`, `0x60e92358` and `0x60e993fa`. In all, 51 sites in `0x60c00000..0x61200000` load
  `+152`.
- The colour editor's reset (`reset_hook`, `0x60e9e0f4`) sends each of the 12 cells the command and then `0x900c`.
  hsl.s sets `ST_RESET` around it. On the Hue / Lightness axes, `ui_write` used to write 0 in place of OM's
  saturation default.
- Looks were written as plain values (`fl_delete`). The default stayed OM's, which is 0. So after a look, the
  "changed" check compared against 0 and Hold OK wrote 0.

## Change (build `e583093b…1839`, emulator not run)

- The vtable slot `0x60bb6b68` (`+152`) points to `def_hook`. OM's default is still used except in one case: the ID
  is one of a slot's own settings, and that slot holds a look from this power-on's `LOOKS.BIN`. Both the look's
  index and its stored name must match. In that case the look's value is the default. The settings covered are the
  12 saturation cells `928+12p+s` and contrast `908+p`, sharpness `904+p` and shading `912+p`. The tone IDs
  `976..978+3p` are covered too (the `fl_ids` table). The "changed" check and every `+152` reset then use the look.
- `ui_write` (Hue / Lightness axis, during `ST_RESET`) writes the look's Hue / Lightness of that cell through
  `hl_reset`. Without a look it writes 0, as before. The write guard is now −7..+7, the range a look may hold.
- On the tone page's Black / White state, OM's tone IDs write Black / White through `tone_alias`. No look holds
  those, so OM's default (0) is kept there.
- The code (279 bytes) is in `.ext2b`, at `0x604ef120..0x604ef237`, in section 2. That space is the tail of setting
  111's old record table, which `color_profiles.py` repoints away from. The stock image has one pointer into
  `0x604eeae0..0x604ef520`: the 111 descriptor at `0x6050de48`, which the patch rewrites. Nothing else uses
  `0x604ef120..0x604ef520`. The cp_grain_rows slot (`0x604ef064..0x604ef120`) is left free.
- Before arming, `fl_preset` calls `st_ptr` and nothing else, so the stock default is returned.

## Limits (inference / by design)

- When `LOOKS.BIN` is not loaded, the defaults stay OM's. This covers no card, a different card and a bad file. It
  also covers a file in which the slot's look index or name changed.
- Black and White are not part of a look, so their reset is 0.
- OM's "changed" check compares saturation only on the wheel (getter `+8`). A Hue- or Lightness-only change is
  therefore not expected to show the mark.
- The white-balance shift a look sets is not a Picture Mode row and is not covered.
- **Not established:** which on-screen mark the row status bytes draw. Whether the screen draws it for Color
  Profile rows at all is also open. The owner's "star" is assumed to be this mark. Check in OM-Emu and on the
  camera.

## Checks still needed

OM-Emu:

- Wheel, tone, Shading, Sharpness and Contrast rows on a slot with a look. Compare the mark before and after a
  change.
- Hold OK on each row returns the look's value. Check saturation and Hue / Lightness on the wheel.
- On the tone page's Black / White state, Hold OK gives 0 and leaves Highlights / Shadows unchanged.
- An empty slot and a stock picture mode behave as before.

Then the camera, with the package SHA-256 verified on the card.
