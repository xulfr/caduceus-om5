# Looks as a Color Profile's defaults: the "changed" hint and Hold OK reset (2026-11-27)

**Emulator only (OM-Emu `bdb3347`), no camera.** Addresses are runtime addresses of the expanded main program, E148
firmware 1.1 build 1100.

## Owner report (2026-11-27)

On a Color Profile holding a look:

1. After a setting is changed, the Picture Mode screen shows no star next to it.
2. **Hold OK** sets the setting back to 0. It does not return to the look's value. The owner's example was black
   levels.

## Reproduced in OM-Emu on the alpha1 source (`2b3fd53c…a21e6`)

- **Reset to 0.** Look 1 of `tools/dev/films-test.json` is applied to Color Profile 1. One saturation is changed
  and OK is held: all 12 saturations become 0. The tone curve resets to 0 as well.
- **The hint.** OM's only change indicator on these pages is the **Reset OK Hold** hint, bottom right. It already
  shows straight after a look is applied, because the look's values differ from 0. A change therefore adds nothing.
- **No star.** None appeared in the emulator, on a Color Profile or on a stock picture mode.

## Where OM takes a setting's default (static, then confirmed by the emulator runs below)

- The settings object comes from `0x608eedd3` (global `0x61e44380`). Its vtable is at `0x60bb6ad0` (constructor
  `0x608eee3f`).
  - `+0` (`0x608efc53`) is the setter. It reaches `0x6091c624`, the function that holds `read_hook` and `write_hook`.
  - `+8` (`0x608ef257` → `0x6091be54`) is the value getter. It does not pass through `read_hook`, so a colour cell
    reads as its saturation.
  - `+152` (`0x608ef2b4` → `0x6091beb4` → `0x602d0060`) is the **default value**.
- The panel's "changed" check `0x60e4ae7b` is called from the wheel row at `0x60e4acf8` and `0x60e4ad92`. It runs
  through the row's ID list (object at panel + 4444) and compares getter `+8` with default `+152` for each ID. A
  difference sets the row status bytes (panel + 4300 + 9 / + 10), which show the Reset OK Hold hint.
- The Hold OK resets read the default with `+152` and write it with the setter `+0`. Examples are `0x60e91c1d`,
  `0x60e92358` and `0x60e993fa`. In all, 51 sites in `0x60c00000..0x61200000` load `+152`.
- The colour editor's reset (`reset_hook`, `0x60e9e0f4`) runs with `ST_RESET` set. On the Hue / Lightness axes,
  `ui_write` used to write 0 there.

## Change

- **`def_hook`.** The vtable slot `0x60bb6b68` (`+152`) points to `def_hook`. It returns the look's value only when
  the setting belongs to a slot that holds a look, and only while this power-on's `LOOKS.BIN` still holds that
  look, with the same index and stored name. Otherwise it returns OM's default.
  - Settings covered: the 12 saturation cells `928+12p+s`, contrast `908+p`, sharpness `904+p`, shading `912+p` and
    tone `976..978+3p`.
  - On the wheel's Hue / Lightness axis, OM's check still compares saturation. So when the cell's value on that axis
    differs from the look, `def_hook` returns the saturation xor 1, and the check sees the change. OM's reset on
    those axes writes through `hl_reset`, which ignores that value.
- **`ui_write`.** On the Hue / Lightness axis during `ST_RESET`, `hl_reset` writes the look's value for the cell, or
  0 without a look. The write guard is now −7..+7, the range a look may hold.
- **Black / White.** On the tone page's Black / White state, OM's tone IDs write Black / White (`tone_alias`). No
  look holds them, so OM's default, 0, is kept there.
- **Placement.** The code is in `.ext2b` at `0x604ef120`, in section 2. That space is the tail of setting 111's old
  record table (`0x604eeae0..0x604ef520`).
  - `color_profiles.py` repoints the 111 descriptor away from the table. In the stock image that descriptor, at
    `0x6050de48`, is the only pointer into the table.
  - The cp_grain_rows slot (`0x604ef064..0x604ef120`) stays reserved.
  - Before arming, `fl_preset` calls `st_ptr` and nothing else, and OM's default is returned.
- **Bug caught by OM-Emu.** The first build gave `fl_preset` a 16-byte frame for its four saved registers. A `call`
  stores its return address at the caller's `(0,sp)`, so each nested call overwrote a saved register. The firmware
  then trapped in `0x608ef2f6` with an out pointer inside our code. The frame is now 20 bytes, the convention for a
  function that makes calls.

## Emulator results (`tests/run_look_defaults.py`)

On the new build all six cases pass. On the alpha1 build the five look cases fail, and `no-look` passes on both.

| Case | Keys after the look | After Hold OK |
|---|---|---|
| wheel-saturation | wheel, main+1 | 12 saturations are the look's. The hint shows after the change and is hidden after the reset. |
| wheel-hue | wheel, trash (Hue), main+1 | Hue is the look's. The hint shows after the change and is hidden after the reset. |
| wheel-lightness | wheel, trash ×2, main+1 | Lightness is the look's. |
| tone | tone, sub+1, main+1 | Shadows / Highlights are the look's. The hint shows after the change and is hidden after the reset. |
| tone-black-white | tone, INFO, sub+2, main-3 | Black / White are 0. The tone curve stays the look's. |
| no-look | (slot without a look) wheel / tone changes | OM's default, 0, as on alpha1. |

Other observations:

- On the mode strip, the hint is hidden right after a look is applied and shows after a change.
- **No change, and alpha1 behaves the same:**
  - In OM-Emu, Hold OK does nothing on the Shading, Sharpness and Contrast slider rows. The same is true on a stock
    picture mode.
  - Hold OK does nothing on the mode strip.
  - 1.5 s is not a long press in OM-Emu; 3 s is. `tools/dev/sess.mjs` has a new `hold:KEY:MS` token.

## Limits

- When `LOOKS.BIN` is not loaded, the defaults stay OM's. This covers no card, a different card and a bad file.
- Black and White are not part of a look, so their reset is 0.
- On the wheel the hint follows the active axis, like OM's per-axis reset.
- The white-balance shift a look sets is not a Picture Mode row and is not covered.
- A "star" was not seen in the emulator. If the camera draws one somewhere, it needs a photo of the screen to
  identify it.

## Camera checks

Verify the package SHA-256 on the card first. Then, on a slot holding a look:

- The Reset OK Hold hint is hidden right after the look is applied. It shows after a change and goes away after Hold
  OK.
- Hold OK returns the wheel (each axis) and the tone curve to the look.
- On an empty slot and on stock modes, behaviour is unchanged.
