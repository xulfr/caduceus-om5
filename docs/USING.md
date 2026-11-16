# Using it

> The [alpha8 camera report](../research/OM5II-ALPHA8-CAMERA-2026-11-15.md) records confirmed functions and known UI defects.

**After switching on, half-press the shutter button once.** Until then the camera behaves exactly as OM's
firmware (the Color Profiles are in the list, but their extra controls are asleep and no look file is read).
A profile that was selected when the camera was switched off is applied at that half-press; a photo taken
before any half-press (by remote control, for example) uses the camera's stock values.

## The slots

| | Color Profile 1–3 | Monochrome Profile 1–3 |
|---|---|---|
| Looks from `LOOKS.BIN` (trash button steps through them) | Yes | No |
| Hue, Saturation, Lightness for 12 colours | Yes | No |
| Tone curve (Shadows, Midtones, Highlights) | Yes | Yes |
| Sharpness, Contrast, Shading | Yes | Yes |
| Own white balance, remembered per profile | Yes | No |
| Colour filter, toning, grain | No | Yes |
| Name shown on the Picture Mode screen and super control panel | The look's name | OM's name |


**OK › Picture Mode.** After Color Creator:

- **Color Profile 1, 2, 3**: your three look slots.
- **Monochrome Profile 1, 2, 3**: OM's monochrome profiles (filter, toning, grain, tone), as on the OM-3 and PEN-F.
  The Color Filter page cannot change the filter yet (no filter picker, [roadmap](../ROADMAP.md)).

Each Color Profile has its own rows (press down from the list):

| Row | What |
|---|---|
| Colour wheel | 12 colours. **INFO**: one colour / all. **Trash button: Saturation → Hue → Lightness.** Saturation −5..+5, Hue and Lightness −5..+5 on the camera (looks can hold −7..+7). |
| Tone curve | Shadows, Midtones, Highlights, −7..+7 (INFO moves between them). |
| Shading | −5..+5 |
| Sharpness, Contrast | −2..+2 |

Each Color Profile also remembers its own **white balance**: the mode, the Kelvin value and the A/B, G/M shift you
set while it is selected come back when you select it again. All other picture modes share one white balance. This
is not a row in the Picture Mode screen: set white balance as usual (WB button or super control panel). Not yet
checked on a camera.

**Hold OK** on a row resets it, as on OM's own picture modes.

## Looks

1. Make `LOOKS.BIN` in [LookLab](https://xulfr.github.io/caduceus-om5/looklab/) (or use the starter file) and put
   it in a folder `OM5MOD` at the top of the card.
2. Switch on, half-press once. The camera reads the file (up to ten looks).
3. **Picture Mode › Color Profile 1** (or 2, 3). Press the **trash button**: the slot takes a look. Press again:
   the next look. After the last look it starts again at the first.
4. The title changes to the look's name at once and the rows show its values.

The first press on an empty slot gives look 1 on Color Profile 1, look 2 on Color Profile 2, look 3 on Color
Profile 3.

What a look sets: the 12 colours' Saturation, Hue and Lightness, the tone curve, Contrast, Sharpness, Shading and
the white-balance shift (A/B, G/M, on the white-balance mode you are using). A look made without a shift sets the
shift to 0, so it never keeps the shift of the look before it.

**The look is now the slot's own settings.** It is saved with the camera's settings, it is there after switching
off, with another card or with no card, and it goes with a custom mode (C1–C4) you save. You can change any of its
values on the camera. The card is needed again only to choose another look.

Things to know:

- **The trash button steps the look only on the Picture Mode row** (the strip of picture modes). A step
  **overwrites the slot's values**, including changes you made. In the colour wheel the trash button switches
  Saturation / Hue / Lightness; on the tone, Shading, Sharpness and Contrast rows it does nothing.
- If you go down to the other rows and come back up, a slot holding a look keeps the look's name as the title. An
  empty Color Profile slot reads "Picture Mode" instead of its own name until you move along the strip.
- On the super control panel the look's name is the top line while the Picture Mode cell is highlighted.
- A `LOOKS.BIN` that is damaged, or has a value out of range, is ignored as a whole.
- The look file is read once per switch-on. After changing the file, switch off and on.
- A full reset, or resetting the custom mode, clears the slots and the names.

## Live ND

In the camera's Live ND setting, ND32 and ND64 are added after ND16. Whether the camera completes 32- and
64-frame exposures has not been seen on a camera.
