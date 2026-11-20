<h1 align="center">Caduceus for OM-5</h1>

<p align="center"><strong>Looks and a full colour editor for the OM SYSTEM OM-5 Mark II. Experimental.</strong></p>

<p align="center">
  <a href="https://xulfr.github.io/caduceus-om5/"><b>Website</b></a> &nbsp;·&nbsp;
  <a href="docs/INSTALL.md"><b>Install</b></a> &nbsp;·&nbsp;
  <a href="docs/USING.md"><b>Using it</b></a> &nbsp;·&nbsp;
  <a href="https://xulfr.github.io/caduceus-om5/looklab/"><b>LookLab</b></a> &nbsp;·&nbsp;
  <a href="docs/FAQ.md"><b>FAQ</b></a> &nbsp;·&nbsp;
  <a href="docs/SAFETY.md"><b>Safety</b></a> &nbsp;·&nbsp;
  <a href="ROADMAP.md"><b>Roadmap</b></a>
</p>

> [!CAUTION]
> ### v0.2.0-alpha1 is the current experimental build
> Released 20 November 2026. The owner reports that it “works perfectly” on an OM-5 Mark II running stock firmware 1.1.
> New: Black and White on the tone curve page, split toning (Shadow, Midtone and Highlight Tint) on the colour wheel,
> and live view that follows tone and tint changes without a half-press. [Release notes and checksum](releases/v0.2.0-alpha1/README.md).
> Five earlier development builds failed on that camera (4–15 November 2026). Each time, OM's own firmware was put
> back from the card. The installer refuses alpha1–alpha7. Future recovery remains uncertain.
> **Installing it can leave a camera unable to start.** Read [Safety](docs/SAFETY.md) before anything else.

## Status

| Camera | Build | State |
|---|---|---|
| **OM-5 Mark II** (2024), firmware 1.1 | **v0.2.0-alpha1**, 20 Nov 2026 | **Runs on one camera (current build).** The owner reports the candidate from `c3bc45c` “works perfectly”. The number of starts and the on-card checksum were not separately reported. [Release notes](releases/v0.2.0-alpha1/README.md). |
| | v0.1.0-alpha12, 16 Nov 2026 | **Runs on one camera.** The owner reports all defects from alpha11 are fixed, including the filter graphic. [Alpha12 release notes](releases/v0.1.0-alpha12/README.md). |
| | v0.1.0-alpha11 | **Booted on one camera.** Both alpha10 defects resolved. The native filter controls work. [Camera report](research/OM5II-ALPHA11-CAMERA-2026-11-16.md). |
| | v0.1.0-alpha10, 17 Nov 2026 | **Booted on one camera.** Opening Monochrome Color Filter restarted the camera. ND32/64 icons were blank in the CP carousel. [Camera report](research/OM5II-ALPHA10-CAMERA-2026-11-17.md). |
| | v0.1.0-alpha9, 16 Nov 2026 | **Booted on one camera** (owner report). Colour wheel drawn; [defects found](research/OM5II-ALPHA9-CAMERA-2026-11-16.md). |
| | v0.1.0-alpha8, 15 Nov 2026 | **Boot confirmed on one camera.** Color Profiles, SD-card looks and Live ND32/64 work with [known UI defects](research/OM5II-ALPHA8-CAMERA-2026-11-15.md). |
| **Original OM-5** (2022), firmware 1.2 | none working | **No working version.** Pre-alpha 1 (alpha2 donor) failed to start on a tester's camera on 17 Nov 2026. OM's 1.2 was restored from the card ([report](research/OM5I-PREALPHA1-CAMERA-2026-11-17.md)). Pre-alpha 2 (alpha12 donor) has never been built from OM's files or run on a camera. Do not flash either. [Tester page](docs/OM5_PREALPHA.md). |

Every build is also checked in an emulator, which runs the camera's own software on a computer. The emulator
cannot imitate everything (the image sensor, the second processor, the start-up loader), and it did not predict
the earlier camera failures. Only a report from a real camera can change the state above.

## At a glance

**What's added** (OM-5 Mark II): six entries in **Picture Mode**, after Color Creator, plus Live ND32 and ND64.

| | Color Profile 1–3 | Monochrome Profile 1–3 |
|---|---|---|
| Looks from `LOOKS.BIN` (trash button steps through them) | Yes | No |
| Hue, Saturation, Lightness for 12 colours | Yes | No |
| Tone curve (Shadows, Midtones, Highlights) | Yes | Yes |
| Black and White on the tone curve page (INFO switches, v0.2.0) | Yes | No |
| Split toning: Shadow, Midtone and Highlight Tint, 12 colours (v0.2.0) | Yes | No |
| Sharpness, Contrast, Shading | Yes | Yes |
| Own white balance, remembered per profile (the camera's usual WB setting, see below) | Yes | No |
| Colour filter, toning, grain | No | Yes (filter graphic restored in alpha12) |
| Name shown on the Picture Mode screen and super control panel | The look's name | OM's name |

Live **ND32 and ND64** are added after ND16 in the camera's Live ND setting. Picture Mode now stays open for
30 seconds after the last input, and tone and tint changes show in live view straight away.

**White balance per profile** is not a row in the Picture Mode screen. Set white balance as usual (WB button or
super control panel) while a Color Profile is selected: the mode, the Kelvin value and the A/B, G/M shift are kept
for that profile and come back when you select it again. Not yet checked on a camera.

**How to use looks**

1. Make up to ten looks in LookLab (or use the ten starter looks) and copy `LOOKS.BIN` into a folder `OM5MOD` at the top of the card.
2. Switch on and **half-press the shutter button once**. The camera reads the file then (once per switch-on).
3. Press **OK**, go to **Picture Mode** and move along the strip to **Color Profile 1**, 2 or 3 (after Color Creator).
4. Press the **trash button**. An empty slot starts with the look matching its slot number, or look 1 if the bank has fewer looks. Press again for the next look. After the last it wraps to look 1. Each slot keeps its own look.
5. Press **down** to fine-tune the look:
   - **Colour wheel**: INFO switches between HSL and Tint. The trash button steps Saturation / Hue / Lightness, or
     Shadow / Midtone / Highlight Tint. The dials choose one of 12 colours and set the strength.
   - **Tone curve**: INFO steps Highlights/Shadows → Black/White → Midtones. Use the dials to adjust.
   - Shading, Sharpness and Contrast.
6. Shoot. The look is stored in the camera: it stays after switching off, with no card, and goes into custom modes C1–C4.

**How to install:** the [install guide](docs/INSTALL.md), summarised [below](#install-om-5-mark-ii).
See [Safety](docs/SAFETY.md) for the camera result and recovery procedure.

## What it does

On the OM-5 Mark II, OM's firmware has three **Color Profile** slots and three **Monochrome Profile** slots that are
hidden from the menus. Caduceus brings them back and adds:

- **Custom looks.** Each Color Profile slot can hold a look, such as "Portra 400" or "Velvia 50". You make up to
  ten looks in [LookLab](https://xulfr.github.io/caduceus-om5/looklab/), a web page that runs in your browser, and
  save them as one file, `LOOKS.BIN`, in a folder `OM5MOD` on the memory card. In Picture Mode, select a Color
  Profile and press the **trash button** to step through the looks. The look's name becomes the screen's title and
  appears on the super control panel. The chosen look is stored in the camera, so the card is only needed to change it.
- **A full colour editor on the camera.** For 12 colours: Saturation, and new **Hue** and **Lightness** controls. Plus a
  tone curve (Shadows, Midtones, Highlights, and from v0.2.0 **Black** and **White**), **split toning** (a Shadow,
  Midtone and Highlight Tint, each one of 12 colours), Sharpness, Contrast, Shading and a white balance for each slot.
- **Monochrome Profile 1–3**, with colour filter, toning, grain and tone.
- **Live ND32 and ND64**, after the camera's ND2–ND16.

It changes JPEG photos and the live view, as any picture mode does. RAW files are not affected.

## Install (OM-5 Mark II)

Read [Safety](docs/SAFETY.md) first. Full steps, with what to expect at each one: **[Install guide](docs/INSTALL.md)**.
In short:

1. Check the camera is an **OM-5 Mark II** on firmware **1.1** (Menu › Setup › Firmware), and charge the battery.
2. Download **Source code (zip)** from the [v0.2.0-alpha1 release](https://github.com/xulfr/caduceus-om5/releases/tag/v0.2.0-alpha1) and unzip it. You need [Python 3](https://www.python.org/downloads/).
3. In the unzipped folder, run `python3 patch.py`. Type `UNTESTED` when prompted.
   The installer downloads OM's official firmware, applies Caduceus, verifies the package and creates `card`.
4. Copy `DCOLYMP` and `OM5MOD` from `card` to the top of the SD card. **Keep `card/restore`**: it is OM's own
   firmware, to go back.
5. Before flashing, check that the SHA-256 of `DCOLYMP/E1489999.BIN` **on the card** is
   `2b3fd53ce24433edb662036a29e1f4ea3988c61f9a15d681f0998ebe7b4a21e6`.
6. Camera off, **hold OK**, switch on, and wait until the light blinks.

## Original OM-5

The original OM-5 runs an older program that has no hidden profiles to bring back. The pre-alpha therefore puts
the whole OM-5 Mark II program, with Caduceus, into the original OM-5's update file. If it works, the camera would
behave like a Mark II running Caduceus. Whether the Mark II program can drive the original OM-5's hardware is
unknown. There is no working version: the one camera report so far, for pre-alpha 1, is a black screen at start-up
([report](research/OM5I-PREALPHA1-CAMERA-2026-11-17.md)). The [tester page](docs/OM5_PREALPHA.md) explains the risks, how to build it, a safe order of first steps
(starting with OM's own firmware), and how to report. It is not in the one-step installer.

## How it compares with Caduceus for OM-3

The OM-5 Mark II's firmware has much less free space than the OM-3's, so this build covers the essentials.

| | OM-3 (v0.29.1) | OM-5 Mark II (this) |
|---|---|---|
| Looks in the Picture Mode list | FILM 1–20, their own entries | 3 slots (Color Profile 1–3); up to 10 looks in the file, trash button steps through them |
| Look names | title, quick menu, shooting screen | Picture Mode title and super control panel (12 characters) |
| Looks kept in the camera | yes | yes: the look's values become the slot's own settings |
| Hue / Saturation / Lightness, 12 colours | yes | yes |
| Tone curve, Contrast, Sharpness, Shading, WB shift | yes | yes |
| Blacks / Whites, split toning | yes | yes (v0.2.0-alpha1) |
| Colour grain, Glow, Halation | yes | no (not yet: [roadmap](ROADMAP.md)) |
| Film recipe in EXIF | yes | no |
| Tested on a camera | yes | One camera, the owner's (v0.2.0-alpha1) |

## How it works, briefly

- **No OM firmware is shared.** This repository holds only the changes this project makes. The installer downloads
  OM's official firmware from OM's server on your computer, applies the changes, and checks every step against
  recorded checksums (SHA-256). If anything differs, it stops and writes nothing.
- **What changes in the camera:** small additions to OM's program, placed in unused space. They run only after the
  first half-press of the shutter button. Settings are kept in the camera's existing settings storage, and the
  patch's working state in ordinary memory, never in the firmware's own memory. Storing state there was the cause
  traced after the third failure ([analysis](research/OM5II-IMAGE-STORE-FAULT-2026-11-11.md)).
- **Going back** uses OM's unmodified firmware, made alongside the patched file.

## Help wanted

- **Camera owners** willing to test carefully: follow [the first test plan](docs/FIRST_FLASH.md) (Mark II) or the
  [tester page](docs/OM5_PREALPHA.md) (original OM-5), and
  [report what happened](https://github.com/xulfr/caduceus-om5/issues/new?template=camera-test.md), including failures.
- **Developers**: see below. Most useful now: the remaining items in the [roadmap](ROADMAP.md), and for the original
  OM-5, the open questions in [this note](research/OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md).

## For developers

| Where | What |
|---|---|
| `firmware/om5ii/` | The patch for OM-5 Mark II 1.1 (E148): `hsl.s` (colour editor, profiles), `films.s` (looks), `wb.s` (white balance), `layout.ld` (hook addresses), `color_profiles.py`, `nd64.py`, and `patch.json` with every changed range and its hashes |
| `patch.py`, `releases/` | The user installer (Python only) and each release's byte edits and expected hashes |
| `patches/ports/om-5-i-from-ii/` | The original OM-5 (E144) builder |
| `card/mklooks.py`, `looklab/` | `LOOKS.BIN` writer in Python, and LookLab (static web app, no build step); format in [FORMATS.md](docs/FORMATS.md) |
| `tools/` | `oly_patch.py` (strict build from source), `oly_patch_record.py` (re-record hashes after a source change), `mkrelease.py`, `mksite.py` (site pages), `fetch_stock.py` (OM's firmware files) |
| `tools/dev/` | Emulator sessions and tracing (`sess.mjs`, `calls.mjs`, `calltree.py`) and cross-build comparison (`xbuild.mjs`, `sram_compare.py`) |
| `tests/` | Unit, release-reproduction and emulator regression tests ([how to run](tests/README.md)) |
| `research/` | Failure analyses and findings. [HANDOVER.md](HANDOVER.md) and [AGENTS.md](AGENTS.md): current state and project rules |

Build from source. Needs Python 3.10+ and GNU binutils for `mn10300-elf`:

```bash
python3 tools/fetch_stock.py E148
```

```bash
python3 tools/oly_patch.py firmware/om5ii --stock OLY_E_148_1100_0000_0000.BIN --out generated/strict --decoded
```

Tests:

```bash
OM5_STOCK=OLY_E_148_1100_0000_0000.BIN python3 -m unittest discover -s tests -v
```

Record physical-camera results with the exact package hash and tested features. The experimental installer
keeps its `UNTESTED` confirmation.
Details in [AGENTS.md](AGENTS.md).

## Words used here

- **Firmware**: the camera's own software. **Flashing**: installing firmware from the memory card.
- **Emulator**: a program that runs the camera's software on a computer. Here, [OM-Emu](https://github.com/xulfr/om-emu).
- **E148 / E144**: OM's internal codes for the OM-5 Mark II and the original OM-5.
- **Boot loop**: the camera keeps restarting and never becomes usable.

## Credits

This project stands on the work of three upstream projects. Thank you to their authors.

- **[fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis)** by **fishcu**: the Olympus firmware research (on the PEN-F) that showed how
  these cameras' firmware can be read, changed and rebuilt. The OM-5 Mark II work here began in a fork of it.
- **[cakelesscoder/caduceus-ep7](https://github.com/cakelesscoder/caduceus-ep7)** by **cakelesscoder**: Caduceus itself, for the PEN E-P7. The idea of look
  looks loaded from a file on the card, the way the patch waits for the first half-press, how the installer asks
  OM's server for the official firmware, and the description of the update file format.
- **[androidfanman/caduceus-om3](https://github.com/androidfanman/caduceus-om3)** by **androidfanman**: Caduceus for the OM-3. The look record layout that
  `LOOKS.BIN` reuses, the looks in LookLab's library, LookLab's preview, and the layout of this site and its guides.

Exactly what was taken from each is listed in [NOTICE](NOTICE).

## Licence

Apache-2.0, as the Caduceus family. No OM firmware is in this repository. Not affiliated with OM Digital
Solutions.
