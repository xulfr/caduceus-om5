# Original OM-5: pre-alpha for testers

> **Pre-alpha. This has never run on any camera.** The Mark II build it is made from has not run on a Mark II
> either, and three earlier Mark II builds left the camera in a boot loop. Nobody knows whether an original OM-5 can
> be brought back from the card if this fails. Read all of this page, and [Safety](SAFETY.md), before you start.

This page is for **owners of the original OM-5 (2022, firmware 1.2)** who are comfortable with a terminal, accept the
risk to their camera, and want to help: by trying the first steps below and reporting what happens, good or bad, or
by improving the builder. If you only want to use Caduceus, wait for a tested release.

## What it is

The original OM-5 runs an older program that has no Color Profiles to restore. So this build does not patch it.
It takes the **whole OM-5 Mark II program with Caduceus** and fits it into the original OM-5's update file, with
the original OM-5's file layout and its own controller firmware. If it works, the camera should behave like an
OM-5 Mark II running Caduceus: the Mark II's menus, looks, HSL, tone controls and Live ND64.

Whether it can work depends on hardware the two cameras may not share: sensor and image processor, stabiliser,
charging and USB, and above all the separate controller chip. The original OM-5's controller firmware is kept, and
it is a different build from the Mark II's.

## What is known

| | |
|---|---|
| Builder checks | Both OM firmware files are checked against OM's published checksums. Every Caduceus code range, all 557 OM-5 resource records and all 116 pictures are preserved; the pictures are recompressed losslessly to fit, pixel-checked. The OM-5's own firmware is written alongside, byte for byte, to go back. |
| Emulator, OM-5 model | Runs OM's own OM-5 firmware, but cannot run Mark II code at all: no result. |
| Emulator, Mark II model (same chip family) | Starts, all 13 look checks pass, 23 screens identical to the Mark II build. It does not use the original OM-5's resource layout or controller, so this says little about an OM-5. |
| Comparing the two OM programs | About 86 % of functions match. Differences found: renumbered identifiers, one moved variable in on-chip memory, a different controller firmware. [Details](../research/OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md). |
| Real original OM-5 | **Nothing.** You would be the first. |

## What can go wrong

- **It does not start**, or starts and then freezes or loops. This is quite likely.
- **It cannot be put back from the card.** On the Mark II, OM's firmware went back from the card after each
  failure. Whether the original OM-5's card update still works while this build is installed is unknown. If it
  does not, the camera needs OM service, which may charge or decline.
- **Something works wrongly without you noticing**: exposure, stabilisation, battery charging or reading, saving
  settings. Do not rely on the camera for anything that matters while this is installed.
- **Warranty.** Unofficial firmware may affect it.

No responsibility is accepted for any damage or loss.

## 1. Make the file

You need Linux, macOS, or Windows with WSL, plus Python 3.10 or newer, `git` and a C compiler. About 30 minutes,
most of it building the assembler once.

1. The project, and Pillow:

   ```bash
   git clone https://github.com/xulfr/caduceus-om5.git
   ```

   ```bash
   cd caduceus-om5
   git switch --detach 02c3cb2a64687e3aa74b0639550c82a95cfd66d7
   ```

   This revision pins the Mark II alpha2 donor used by the published pre-alpha 1 checksum.

   ```bash
   python3 -m pip install pillow
   ```

2. `jpegtran` from libjpeg-turbo. Debian/Ubuntu/WSL: `sudo apt install libjpeg-turbo-progs`. macOS (Homebrew):
   `brew install jpeg-turbo`. Check that `jpegtran -version` works.

3. The assembler: GNU binutils 2.42 for `mn10300-elf`, built once into `~/mn10300`:

   ```bash
   curl -LO https://ftp.gnu.org/gnu/binutils/binutils-2.42.tar.xz && tar xf binutils-2.42.tar.xz
   ```

   ```bash
   mkdir binutils-build && cd binutils-build && ../binutils-2.42/configure --target=mn10300-elf --prefix="$HOME/mn10300" --disable-nls --disable-werror --disable-gdb --disable-sim --disable-gprof --disable-gprofng && make -j4 MAKEINFO=true && make install MAKEINFO=true && cd ..
   ```

   ```bash
   export PATH="$HOME/mn10300/bin:$PATH"
   ```

4. OM's two firmware files, from OM's own server (about 180 MB; each is checked):

   ```bash
   python3 tools/fetch_stock.py E144 E148
   ```

5. Build. The output folder must not exist yet:

   ```bash
   python3 patches/ports/om-5-i-from-ii/build.py --stock OLY_E_144_1200_0000_0000.BIN --donor-stock OLY_E_148_1100_0000_0000.BIN --out generated/om5-prealpha1 --write-untested-package
   ```

6. **Check the result.** `generated/om5-prealpha1/build.json` must show

   `"package_sha256": "70788992f032dad53bfa4e145b2147e376d3f25a62e2b1ce2929973fec26d1b4"`

   If it shows anything else, stop and report it (a different `jpegtran` version is the likely cause). Do not flash
   a file with another checksum.

You get:

| | |
|---|---|
| `generated/om5-prealpha1/install/DCOLYMP/E1449999.BIN` | the pre-alpha |
| `generated/om5-prealpha1/restore-stock/DCOLYMP/E1449999.BIN` | OM's own firmware 1.2, to go back. **Keep it.** |

These files contain OM's firmware: keep them to yourself, do not share or upload them.

## 2. Test, in this order

Use a fully charged battery and the card in slot 1. The update method is the same as for the Mark II: camera off,
hold **OK**, switch on, let go when the orange light is steady, do not touch anything until it blinks
([Install, step 3](INSTALL.md#3-update-the-camera)). Delete `DCOLYMP` from the card after each update.

| Step | Do | Tells us |
|---|---|---|
| 0 | Put the **restore** `DCOLYMP` folder on a card and update with it. This is OM's own firmware 1.2, so nothing changes. | That the card update works on your camera, before anything risky. If it does not, stop here. |
| 1 | Prepare a second card with the restore `DCOLYMP` folder and keep it at hand. Then update with the **install** file. Switch on, touch nothing for a minute. | Whether it starts at all: the biggest unknown. |
| 2 | If it started: note **Menu › Setup › Firmware**, open the menus and the super control panel, take a photo, play it back. | Whether the basics work. |
| 3 | Half-press once, then **Picture Mode**: look for Color Profile 1–3; try the colour wheel and the trash button there. | Whether Caduceus works. |
| 4 | With [LookLab](../looklab/)'s `LOOKS.BIN` in `OM5MOD`: looks, as in [Using it](USING.md#looks). Switch off and on several times. | Looks, saving, restart. |
| 5 | Check what you can of stabilisation, charging over USB, battery level, autofocus, and video. | The hardware unknowns. |

**At the first thing that is wrong, stop, write it down, and go back** (below). A photo of the screen helps.

## Going back

Update from the card with `restore-stock/DCOLYMP/E1449999.BIN`, the same way. If the camera does not start or does
not take the update, try again from fully off, with a charged battery. If it still will not take it, the camera
needs OM service.

## Report

Please [open an issue](https://github.com/xulfr/caduceus-om5/issues/new?template=camera-test.md) whatever happened,
including "it did not start" and "I stopped at step 0". Give the checksum you built, how far you got, and what you
saw. A failure report is as useful as a success: this page changes only with reports from real cameras.
