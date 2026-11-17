# Camera test checklist

## Alpha12 camera checks

The [alpha10 camera report](../research/OM5II-ALPHA10-CAMERA-2026-11-17.md) records a restart on the Color Filter page.
The owner confirmed that alpha11 resolved the restart and CP icon defects and reports that alpha12 fixes the remaining filter graphic issue. [Alpha12 camera findings](../releases/v0.1.0-alpha12/README.md).
For the alpha12 check, verify the installer gives package SHA-256
`cddd7a1f1320e7680bec9e8430e25c69857c2f4bf764e571d6bfffb775acd3fa`. After the startup checks (steps 0–3 below),
do step 19 first. If the camera restarts or freezes, stop the checklist, record what happened and follow
[stock recovery](SAFETY.md#going-back-to-oms-firmware).

| Step | Do | Expect |
|---|---|---|
| 19 | Open Monochrome Profile 1 › Color Filter. Turn both dials. Cycle the filter dial through all values, change the level, then leave and re-enter. Check Profile 2 separately. Take a red-filter and a blue-filter JPEG of the same scene. | The page opens and stays open. The header names each filter through the wrap. The two filters render colours differently in the JPEGs. The other dial changes `+n`. Both values persist after re-entry, and Profile 2 keeps its own values. The ring marks the selected swatch. The centre follows the selected colour and is grey for None. The stock “Vivid” word stays visible. |
| 16 | Tick ND32 and ND64 in CP Button Settings. Hold CP and turn the dial past ND16. Select each, then untick them and repeat. | ND32 and ND64 each show their own icon when offered. Selection gives the matching shooting label and exposure. Unticked items disappear. |
| 20 | After a half-press, untick every CP item except ND32. Hold CP, then repeat with only ND64 ticked. | Each item can be offered, shows its icon and can be selected when it is the only item ticked. |
| 15 | Color Profile 1 › Shading. Turn the dials in both directions and re-enter the screen. | Green knob and a setting that steps and persists. |
| 17 | Check Monochrome Profile 1's Film Grain row and strip, and the Color Filter sidebar row. | Off / Low / Std / High artwork, with visible grain in pictures, and a Filter sidebar icon. |
| 18 | In Color Profile 1 set Daylight with an A/B shift. In Color Profile 2 set Shade. Revisit both profiles and Natural. | Each profile restores its own WB and shift. Natural keeps its own WB. |

## Baseline startup and regression checks

The [alpha8 camera report](../research/OM5II-ALPHA8-CAMERA-2026-11-15.md) records the successful boot and known UI defects. If the camera fails to start or freezes, follow [stock recovery](SAFETY.md#going-back-to-oms-firmware) and report what happened.

**Before step 1, set Picture Mode to Natural in OM's firmware** for the shooting mode the camera
will start in (and in Movie mode if you use it). Earlier test builds may have left a Color Profile stored there.
Alpha8 activates profiles at the first shutter half-press after switching on and repairs stale profile
numbers then.

| Step | Do | Expect | Shows |
|---|---|---|---|
| 0 | Flash **OM's own 1.1** from `card/restore` (hold OK, switch on). | Steady light, then blinking; a normal start. | Your card, your timing and the card update work, before anything is changed. |
| 1 | Flash `card/DCOLYMP/E1489999.BIN`. **No `OM5MOD` folder on the card yet.** Switch on. Do not touch the shutter button. | The normal shooting screen. Menu, playback and the super control panel work. | The changed program loads and starts. Nothing of ours is active before the first half-press. |
| 2 | OK › Picture Mode. Move along the list **without** a half-press first. | Color Profile 1–3 and Monochrome Profile 1–3 are in the list, after Color Creator. Selecting one works; before a half-press their colour and tone pages do not appear and the trash button does nothing. | The tables and screens. This is where the third build froze. |
| 3 | Switch off, on. Half-press once. Take a photo in Natural. Play it back. | A normal photo. | Arming (one small block of memory is taken at the first half-press). |
| 4 | Picture Mode › Color Profile 1 › the colour wheel. Press the trash button. | Saturation → Hue → Lightness. The wheel draws (it was missing on alpha8; alpha9 restored it). Check a strong Hue and Lightness change against Natural. | The editor and that Hue / Lightness reach the photo. |
| 5 | Switch off, on, several times; leave it on Color Profile 1 while you do. | It starts every time, still on Color Profile 1 with your values. | Starting with a profile saved: the suspected cause of the loop after the third failure. |
| 6 | Copy `OM5MOD` (with `LOOKS.BIN`) to the card. Switch on, half-press, Picture Mode › Color Profile 1, press the trash button (highlight on the strip of picture modes). | The title changes to the first look's name at once; its values are in the rows. A second press gives the second look's name. | Films. |
| 7 | Take the card out, put another in, switch off and on. | Color Profile 1 still has the look and its name. | The look lives in the camera. |
| 8 | Live ND: ND32 and ND64, on a tripod. Custom modes C1–C4 with a Color Profile. Monochrome Profile 1. | They work. | The rest. |

### Alpha9 additions

The owner confirmed that alpha9 (package `2e9777ce…fbc50`) boots. After the alpha12 checks and baseline checks, repeat:

| Step | Do | Expect |
|---|---|---|
| 9 | Picture Mode carousel, sidebar and super control panel on Color 1–3 and Monochrome 1–3. | Numbered icons (1/2/3, M1/M2/M3), no overlap when scrolling the sidebar. |
| 10 | Change any setting of Color Profile 1, confirm, return to the shooting screen. Repeat for one Monochrome Profile, and after loading a look. | The profile's icon stays on the shooting screen (alpha8 and earlier candidates lost it). |
| 11 | Tone Curve row: change Shadows, Midtones and Highlights through several values. | An icon in every state, matching the curve's direction. |
| 12 | Colour wheel and tone curve pages. | The wheel and curve draw, and redraw after leaving and re-entering. Note any colour or flicker problem. |
| 13 | Keep using the wheel, Tone Curve and trash look cycling for over 10 s; then leave the screen idle. | The screen stays open while used and closes about 8 s after the last action. |
| 14 | Gear menu › CP Button Settings; hold the CP button; Live ND menu. | ND32 and ND64 listed, switchable and kept after a power cycle; `ND32-LV` / `ND64-LV` labels and their exposure. |

Steps 1 to 3 are the dangerous ones. If step 1 fails, the build is wrong in a way the emulator cannot see, and
nobody else should flash it.
