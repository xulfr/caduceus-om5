# Original OM-5: pre-alpha for testers

> **There is no working version for the original OM-5.** On 17 November 2026 a tester flashed **pre-alpha 1** onto
> an original OM-5. It did not start: black screen, no backlight, silent. They put OM's firmware 1.2 back from the
> card, and the camera works again ([report](../research/OM5I-PREALPHA1-CAMERA-2026-11-17.md)). That is one camera and one kind of failure. It does not
> promise that recovery will always work. Read all of this page, and [Safety](SAFETY.md), before you start.
>
> **Status (17 November 2026): pre-alpha 2, not ready to flash.** Pre-alpha 1 is withdrawn. Its Mark II base
> (alpha2) shares start-up code with Mark II builds that failed, so the report cannot say whether the transplant
> itself is at fault. Pre-alpha 2 is built from Mark II **v0.1.0-alpha12**, which starts on the owner's OM-5 Mark II
> ([camera findings](../releases/v0.1.0-alpha12/README.md)). That is a Mark II result only. Pre-alpha 2 uses alpha12 and packs the program
> with that build's stream-length rule ([note](../research/OM5II-STREAM-LENGTH-2026-11-15.md)). Nobody has built
> it from OM's files yet, so this page publishes no reference checksum. You can build it and report your
> `build.json` (section 1, step 6), but **do not flash it** until a checksum is published here and yours matches it.

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
| Emulator, Mark II model (same chip family) | Pre-alpha 1 (alpha2 base) started there, passed all 13 look checks, and drew 23 screens identically to its Mark II build. Pre-alpha 2 has not been run there yet. That model does not use the original OM-5's resource layout or controller, so a result there says little about an OM-5. |
| The Mark II base | Alpha12 starts on an OM-5 Mark II. The owner confirmed its looks, the Live ND32/ND64 icons and the Monochrome Color Filter page there. That is a Mark II result only. |
| Comparing the two OM programs | About 86 % of functions match. Differences found: renumbered identifiers, one moved variable in on-chip memory, a different controller firmware. [Details](../research/OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md). |
| Real original OM-5 | **Pre-alpha 1 failed to start** (one tester, 17 Nov 2026), and OM's 1.2 went back from the card ([report](../research/OM5I-PREALPHA1-CAMERA-2026-11-17.md)). **Pre-alpha 2: nothing.** You would be the first. |

## What can go wrong

- **It does not start**, or starts and then freezes or loops. This is quite likely: pre-alpha 1 did not start.
- **It cannot be put back from the card.** On the Mark II, OM's firmware went back from the card after each
  failure. On the original OM-5 it worked once, after pre-alpha 1's black screen. A different failure could still
  stop the card update from working. Then the camera needs OM service, which may charge or decline.
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
   ```

   Stay on the default branch, `main`, which builds pre-alpha 2 from the Mark II alpha12 source. (Pre-alpha 1 is
   withdrawn. It can still be rebuilt at revision `02c3cb2a64687e3aa74b0639550c82a95cfd66d7`, for comparison only.
   Do not flash it.)

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
   python3 patches/ports/om-5-i-from-ii/build.py --stock OLY_E_144_1200_0000_0000.BIN --donor-stock OLY_E_148_1100_0000_0000.BIN --out generated/om5-prealpha2 --write-untested-package
   ```

   If it stops with an error instead, that is a useful result too. Report the full message. An error that mentions
   a "stream" or a "span" comes from the new packing checks.

6. **Check the result.** Look in `generated/om5-prealpha2/build.json`:

   - `donor_build.package_sha256` must be alpha12's,
     `cddd7a1f1320e7680bec9e8430e25c69857c2f4bf764e571d6bfffb775acd3fa`. If it is not, stop and report it.
   - `main_packing` should show `"stream_length": "stock-page"`.
   - Report `package_sha256` and `jpegtran_version` in an [issue](#report). The first matching reports from
     different people will set the published checksum here.

   **Do not flash** until this page publishes a pre-alpha 2 checksum and yours matches it exactly. If yours differs,
   a different `jpegtran` version is the likely cause.

You get:

| | |
|---|---|
| `generated/om5-prealpha2/install/DCOLYMP/E1449999.BIN` | the pre-alpha |
| `generated/om5-prealpha2/restore-stock/DCOLYMP/E1449999.BIN` | OM's own firmware 1.2, to go back. **Keep it.** |

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
| 3 | Half-press once, then **Picture Mode**: look for Color Profile 1–3 and Monochrome Profile 1–3. Try the colour wheel, the trash button and the Monochrome Color Filter page there. In the super control panel, look for ND32 and ND64 after ND16 in Live ND. | Whether Caduceus works, compared with the same checks on the Mark II. |
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
