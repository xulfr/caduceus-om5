# The first camera test

For whoever tests this first. Stop at the first thing that is not as written, put OM's firmware back
([Safety](SAFETY.md)), and report it (what you pressed, what the screen and the lights did).

**Before step 1 (alpha7), still on OM's firmware:** set Picture Mode to Natural in the shooting mode the camera
will start in (and in Movie mode if you use it). Earlier test builds may have left a Color Profile stored there.
From alpha7 on, nothing of this project acts until the first shutter half-press after switching on; if the picture
mode looks wrong before that half-press, it is put right at the half-press.

| Step | Do | Expect | Shows |
|---|---|---|---|
| 0 | Flash **OM's own 1.1** from `card/restore` (hold OK, switch on). | Steady light, then blinking; a normal start. | Your card, your timing and the card update work, before anything is changed. |
| 1 | Flash `card/DCOLYMP/E1489999.BIN`. **No `OM5MOD` folder on the card yet.** Switch on. Do not touch the shutter button. | The normal shooting screen. Menu, playback and the super control panel work. | The changed program loads and starts. Nothing of ours is active before the first half-press. |
| 2 | OK › Picture Mode. Move along the list **without** a half-press first. | Color Profile 1–3 and Monochrome Profile 1–3 are in the list, after Color Creator. Selecting one works; before a half-press their colour and tone pages do not appear and the trash button does nothing. | The tables and screens. This is where the third build froze. |
| 3 | Switch off, on. Half-press once. Take a photo in Natural. Play it back. | A normal photo. | Arming (one small block of memory is taken at the first half-press). |
| 4 | Picture Mode › Color Profile 1 › the colour wheel. Press the trash button. | Saturation → Hue → Lightness. Set a strong Hue and Lightness on one colour, take a photo of something that colour, compare with Natural. | The editor and that Hue / Lightness reach the photo. |
| 5 | Switch off, on, several times; leave it on Color Profile 1 while you do. | It starts every time, still on Color Profile 1 with your values. | Starting with a profile saved: the suspected cause of the loop after the third failure. |
| 6 | Copy `OM5MOD` (with `LOOKS.BIN`) to the card. Switch on, half-press, Picture Mode › Color Profile 1, press the trash button (highlight on the strip of picture modes). | The title changes to the first look's name at once; its values are in the rows. A second press gives the second look's name. | Films. |
| 7 | Take the card out, put another in, switch off and on. | Color Profile 1 still has the look and its name. | The look lives in the camera. |
| 8 | Live ND: ND32 and ND64, on a tripod. Custom modes C1–C4 with a Color Profile. Monochrome Profile 1. | They work. | The rest. |

Steps 1 to 3 are the dangerous ones. If step 1 fails, the build is wrong in a way the emulator cannot see, and
nobody else should flash it.
