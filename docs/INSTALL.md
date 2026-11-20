# Install

> **Experimental firmware.** Read [Safety](SAFETY.md) before you start, and keep the restore file the installer makes.

About 15 minutes.

## You need

- An **OM-5 Mark II** on firmware **1.1** (Menu › Setup › Firmware). Not the OM-5, not another version.
- A fully charged battery, an SD card, a card reader, a computer with [Python 3](https://www.python.org/downloads/).

## 1. Make the card files

1. Download and unzip the **Source code (zip)** from the [v0.2.0-alpha1 release](https://github.com/xulfr/caduceus-om5/releases/tag/v0.2.0-alpha1).
2. Open a terminal in the unzipped folder and run `python3 patch.py`.
   The double-click scripts use the newest release.
3. It displays an experimental firmware warning and asks you to type `UNTESTED`. Then it downloads OM's official firmware 1.1
   from OM's server (90 MB), checks it, adds Caduceus and checks the result against this release's checksum.
   If OM's server has moved on to a newer firmware, get `OLY_E_148_1100_0000_0000.BIN` another way, put it next to
   `patch.py` and run again.

You get a folder `card`:

| | |
|---|---|
| `card/DCOLYMP/E1489999.BIN` | the update with Caduceus |
| `card/OM5MOD/LOOKS.BIN` | the ten starter looks |
| `card/restore/DCOLYMP/E1489999.BIN` | OM's own firmware, to go back. **Keep it.** |

Running the installer again keeps any existing `card/OM5MOD/LOOKS.BIN`, so your custom looks are not replaced.
It prepares the restore file before publishing the update file. If file preparation fails, fix the reported
problem and run it again before copying anything to the card.

## 2. Copy to the SD card

Copy the folders `DCOLYMP` and `OM5MOD` from `card` to the top of the SD card (not inside `DCIM`).
Use the card in **slot 1**.

## 3. Update the camera

1. Camera **off**.
2. Hold **OK** and switch the camera **on**. Let go of OK when the orange light is steady. The screen stays dark.
3. Steady light: writing, about two minutes. **Do not touch anything.**
4. Blinking light: done. Switch off, then on.
5. Delete the `DCOLYMP` folder from the card afterwards (so it cannot be flashed again by accident). Keep `OM5MOD`.

The camera's firmware version still reads 1.1.

## 4. First use

Half-press the shutter button once after switching on. Then **OK › Picture Mode**: after Color Creator you find
Color Profile 1–3 and Monochrome Profile 1–3. [Using it](USING.md).

## Going back to OM's firmware

[Safety › Going back](SAFETY.md#going-back-to-oms-firmware).

## If something goes wrong

- **Fast blinking at once, no steady light:** the file was refused. It must be `DCOLYMP/E1489999.BIN` at the top of
  the card, made by the launcher (it checks its own result).
- **The camera starts normally and nothing changed:** OK was not held from before switching on.
- **It does not start, or freezes:** go back to OM's firmware, then please [report it](https://github.com/xulfr/caduceus-om5/issues).
