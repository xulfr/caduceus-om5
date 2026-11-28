# Using it

**After switching on, Caduceus wakes up by itself** (v0.2.0-dev, not yet checked on a camera). About a second
after the live view appears, the Color Profiles' extra controls, the looks and the page graphics are ready; there is
no need to half-press first. Start-up itself is OM's, unchanged. The profile's one-time catch-up still runs at the
first half-press, so it is in place before the first photo.

- **Hold OK while switching on** to skip this: Caduceus then wakes at the first half-press, as in earlier versions.
- **The card:** the looks (`OM5MOD/LOOKS.BIN`) and the Picture Mode graphics (`OM5MOD/CADUCEUS.BIN`) are read from it
  once per switch-on. Without `CADUCEUS.BIN` everything works, but the colour wheel, tone curve and filter pages show
  no graphic. `CADUCEUS.BIN` is made for one update: use the one that came with your `E1489999.BIN`.

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
  On the Color Filter page, one dial picks the filter from a ring of eight colour swatches and the other sets its level.

Each Color Profile has its own rows (press down from the list):

| Row | What |
|---|---|
| Colour wheel | 12 colours. **INFO**: one colour / all. **Trash button: Saturation → Hue → Lightness → Shadow Tint → Midtone Tint → Highlight Tint.** Saturation −5..+5, Hue and Lightness −5..+5 on the camera (looks can hold −7..+7). Tints: see below. |
| Tone curve | **INFO: Hi/Sh → Black/White → Mid.** Shadows and Highlights (Hi/Sh), Black and White, Midtones, each −7..+7. |
| Shading | −5..+5 |
| Sharpness, Contrast | −2..+2 |

**Black and White** (v0.2.0-dev, not yet checked on a camera) bend the two ends of the tone curve: +Black lifts the
blacks (no pure black), −Black crushes them; +White brightens the whites (they clip sooner), −White dims them.
On the tone curve page press INFO until the labels read Black and White; the two dials then set them, as they set
Shadows and Highlights in Hi/Sh. The curve graphic shows all five. Hold OK resets the state you are in.

**Split toning** (v0.2.0-dev, not yet checked on a camera): on the colour wheel, press the trash button until the
title reads Shadow Tint, Midtone Tint or Highlight Tint. Each tint is one of the twelve colours with a strength 1..5:
turn the value up on the colour you want (the other colours then read 0); turning it back to 0 removes the tint. The
three tints blend smoothly: Shadow Tint is strongest in the blacks, Midtone Tint in the middle greys, Highlight Tint
in the whites. With INFO on "all" the dial sets the last colour only, so use the one-colour mode.

Each Color Profile also remembers its own **white balance**: the mode, the Kelvin value and the A/B, G/M shift you
set while it is selected come back when you select it again. All other picture modes share one white balance. This
is not a row in the Picture Mode screen: set white balance as usual (WB button or super control panel). Not yet
checked on a camera.

**Hold OK** on a row resets it, as on OM's own picture modes. On a slot holding a look (v0.2.0-dev, emulator
only) the colour wheel and tone curve go back to **the look's values**. OM's **Reset OK Hold** hint is shown only
while a value differs from the look. This needs the look file read at this switch-on (the card with the same
`LOOKS.BIN`); without it the reset gives 0 as before. Black and White are not part of a look and reset to 0.

## Looks

1. Make `LOOKS.BIN` in [LookLab](https://xulfr.github.io/caduceus-om5/looklab/) (or use the starter file) and put
   it in a folder `OM5MOD` at the top of the card.
2. Switch on. The camera reads the file about a second after the live view appears (up to ten looks). On
   v0.2.0-alpha1 and earlier, or with OK held at switch-on, it reads it at the first half-press instead.
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
