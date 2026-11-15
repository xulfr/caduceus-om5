# Safety

**Short version: nobody has seen this run on a camera. If you flash it, you are the first test.**

## What is known

| | |
|---|---|
| Emulator (OM-Emu, OM-5 Mark II firmware 1.1) | The camera starts, the Picture Mode screens work, looks load from the card and reach the slot's settings, nothing writes into the firmware image. |
| Real OM-5 Mark II | **Alpha5 and alpha6 boot-looped** on 15 November 2026. The owner restored OM's 1.1 from the card. The installer refuses alpha1–alpha7. **Alpha8 has only run in OM-Emu.** |
| Earlier builds on a real OM-5 Mark II | **Three more failures**, 4, 5 and 8 November 2026. Two never started (black screen, the lens hunting). The third started, then froze when the Picture Mode screen was used, and looped on every start after. |
| Going back | After each failure OM's firmware was put back from the card (hold **OK**, switch on). The first attempt after the first failure showed a steady red light and did not work; the second did. |

The third failure was traced to the patch storing its working values inside the firmware's own memory, which OM's
program never does ([the analysis](../research/OM5II-IMAGE-STORE-FAULT-2026-11-11.md)). This build keeps them in a
block of ordinary memory instead and touches nothing until the first half-press of the shutter button. The first
two failures were builds with a different loading scheme that is no longer used; their exact cause was never found.

The emulator did not predict the earlier failures. It has no real loader, no second processor, no image
processor. Passing it means "no fault that the emulator can show".

## What can go wrong

- **The camera does not start, or starts and then freezes.** Then put OM's firmware back (below). So far that has
  worked every time, on one camera. Nothing proves it always will: the part of the firmware that reads the card
  update lives in the same program this project changes.
- **The camera cannot be recovered from the card.** Then it needs OM service, and they may charge, or decline.
- **Warranty.** Unofficial firmware may affect it.
- **Photos.** Whether Hue, Lightness and the looks reach the JPEG exactly as intended has never been checked on a
  camera. Shoot RAW + JPEG for anything that matters.

No responsibility is accepted for any damage or loss.

## Before you flash

1. Fully charged battery. Do not interrupt the update.
2. Keep `card/restore/DCOLYMP/E1489999.BIN`, and a second SD card with that `DCOLYMP` folder already on it.
3. Read [the first-flash plan](FIRST_FLASH.md): it goes in steps, the first of which changes nothing.
4. Note your camera's settings (or save them with OM Workspace): going back resets nothing, but a full reset may be
   part of recovery.

## Going back to OM's firmware

1. Copy the `DCOLYMP` folder from `card/restore` to the top of an SD card (so the card has `DCOLYMP/E1489999.BIN`).
2. Camera off. Card in **slot 1**. Hold **OK** and switch on. Let go when the orange light is steady.
3. Steady light = writing (about two minutes; touch nothing). Blinking = done. Switch off, then on.
4. If the light blinks fast straight away, the file was refused: check the file and its place on the card. If the
   camera just starts normally, OK was not held early enough: try again.
5. A steady **red** light, or nothing: switch off, take the battery out for a minute, try again, and again with the
   second card. That is what recovered the first failure.

Before going back from a working install, set a normal picture mode (Natural) in every custom mode C1–C4, so no
saved mode points at a Color Profile that OM's firmware hides.
