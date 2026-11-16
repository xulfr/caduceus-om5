# Camera test checklist

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
| 4 | Picture Mode › Color Profile 1 › the colour wheel. Press the trash button. | Saturation → Hue → Lightness. On alpha8 the header and dials work with the wheel graphic missing. Check a strong Hue and Lightness change against Natural. | The editor and that Hue / Lightness reach the photo. |
| 5 | Switch off, on, several times; leave it on Color Profile 1 while you do. | It starts every time, still on Color Profile 1 with your values. | Starting with a profile saved: the suspected cause of the loop after the third failure. |
| 6 | Copy `OM5MOD` (with `LOOKS.BIN`) to the card. Switch on, half-press, Picture Mode › Color Profile 1, press the trash button (highlight on the strip of picture modes). | The title changes to the first look's name at once; its values are in the rows. A second press gives the second look's name. | Films. |
| 7 | Take the card out, put another in, switch off and on. | Color Profile 1 still has the look and its name. | The look lives in the camera. |
| 8 | Live ND: ND32 and ND64, on a tripod. Custom modes C1–C4 with a Color Profile. Monochrome Profile 1. | They work. | The rest. |

### Alpha9 additions

Alpha9 (package `2e9777ce…fbc50`) has not been run on a camera. After steps 0 to 3, also check:

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
