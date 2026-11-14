<h1 align="center">Caduceus for OM-5</h1>

<p align="center"><strong>Film looks and a full colour editor for the OM SYSTEM OM-5 Mark II. Experimental.</strong></p>

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
> ### Nobody has run this on a camera yet
> Everything here has only been tried in an **emulator**, a program that imitates the camera on a computer. Three
> earlier versions of this work left the owner's OM-5 Mark II stuck restarting (November 2026). Each time, OM's own
> firmware could be put back from the memory card, but there is no guarantee that will always work.
> **Installing it can leave a camera unable to start.** Read [Safety](docs/SAFETY.md) before anything else.
> We are looking for someone willing to make the first careful camera test: see [the test plan](docs/FIRST_FLASH.md).

## Status

| Camera | Build | State |
|---|---|---|
| **OM-5 Mark II** (2024), firmware 1.1 | v0.1.0-alpha2, 14 Nov 2026 | Works in the emulator. **Never run on a camera.** One-step installer included. |
| **Original OM-5** (2022), firmware 1.2 | pre-alpha 1, 14 Nov 2026 | **Never run on any camera**; recovery after a failure is unknown. For testers who can build it: [tester page](docs/OM5_PREALPHA.md). |

"Emulator only" means: the camera's own software was run on a computer and behaved correctly there. The emulator
cannot imitate everything (the image sensor, the second processor, the start-up loader), and it did not predict
any of the three earlier failures. Only a report from a real camera can change the state above.

## What it does

On the OM-5 Mark II, OM's firmware has three **Color Profile** slots and three **Monochrome Profile** slots that are
hidden from the menus. Caduceus brings them back and adds:

- **Film looks.** Each Color Profile slot can hold a film look, such as "Portra 400" or "Velvia 50". You make up to
  ten looks in [LookLab](https://xulfr.github.io/caduceus-om5/looklab/), a web page that runs in your browser, and
  save them as one file, `LOOKS.BIN`, in a folder `OM5MOD` on the memory card. In Picture Mode, select a Color
  Profile and press the **trash button** to step through the looks. The look's name becomes the screen's title and
  appears on the super control panel. The chosen look is stored in the camera, so the card is only needed to change it.
- **A full colour editor on the camera.** For 12 colours: Saturation, and new **Hue** and **Lightness** controls. Plus a
  tone curve (Shadows, Midtones, Highlights), Sharpness, Contrast, Shading and a white balance for each slot.
- **Monochrome Profile 1–3**, with filter, toning, grain and tone.
- **Live ND32 and ND64**, after the camera's ND2–ND16.

It changes JPEG photos and the live view, as any picture mode does. RAW files are not affected.

## Install (OM-5 Mark II)

Read [Safety](docs/SAFETY.md) first. Full steps, with what to expect at each one: **[Install guide](docs/INSTALL.md)**.
In short:

1. Check the camera is an **OM-5 Mark II** on firmware **1.1** (Menu › Setup › Firmware), and charge the battery.
2. On this page, **Code › Download ZIP**, then unzip it. You need [Python 3](https://www.python.org/downloads/).
3. Double-click `Make SD card files (Mac).command` or `Make SD card files (Windows).bat`. It asks you to type
   `UNTESTED` to confirm you understand, downloads OM's official firmware from OM's own server, adds Caduceus, and
   checks the result. You get a folder `card`.
4. Copy `DCOLYMP` and `OM5MOD` from `card` to the top of the SD card. **Keep `card/restore`**: it is OM's own
   firmware, to go back.
5. Camera off, **hold OK**, switch on, and wait until the light blinks.

## Original OM-5

The original OM-5 runs an older program that has no hidden profiles to bring back. The pre-alpha therefore puts
the whole OM-5 Mark II program, with Caduceus, into the original OM-5's update file. If it works, the camera would
behave like a Mark II running Caduceus. Whether the Mark II program can drive the original OM-5's hardware is
unknown. The [tester page](docs/OM5_PREALPHA.md) explains the risks, how to build it, a safe order of first steps
(starting with OM's own firmware), and how to report. It is not in the one-step installer.

## How it compares with Caduceus for OM-3

The OM-5 Mark II's firmware has much less free space than the OM-3's, so this build covers the essentials.

| | OM-3 (v0.29.1) | OM-5 Mark II (this) |
|---|---|---|
| Films in the Picture Mode list | FILM 1–20, their own entries | 3 slots (Color Profile 1–3); up to 10 looks in the file, trash button steps through them |
| Film names | title, quick menu, shooting screen | Picture Mode title and super control panel (12 characters) |
| Looks kept in the camera | yes | yes: the look's values become the slot's own settings |
| Hue / Saturation / Lightness, 12 colours | yes | yes |
| Tone curve, Contrast, Sharpness, Shading, WB shift | yes | yes |
| Blacks / Whites, split toning, grain, Glow, Halation | yes | no (no room yet: [roadmap](ROADMAP.md)) |
| Film recipe in EXIF | yes | no |
| Tested on a camera | yes | **no** |

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
| `research/` | Failure analyses and findings. [HANDOVER.md](HANDOVER.md) and [CLAUDE.md](CLAUDE.md): current state and project rules |

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

Rules that keep the project honest: only a recorded camera result may be called "camera-tested"; releases keep
`camera_tested: false` and the installer's `UNTESTED` confirmation until then; failures are recorded, never hidden.
Details in [CLAUDE.md](CLAUDE.md).

## Words used here

- **Firmware**: the camera's own software. **Flashing**: installing firmware from the memory card.
- **Emulator**: a program that runs the camera's software on a computer. Here, [OM-Emu](https://github.com/xulfr/om-emu).
- **E148 / E144**: OM's internal codes for the OM-5 Mark II and the original OM-5.
- **Boot loop**: the camera keeps restarting and never becomes usable.

## Licence and credits

Apache-2.0. Part of the [Caduceus](https://github.com/cakelesscoder/caduceus-ep7) family
([E-P7](https://github.com/cakelesscoder/caduceus-ep7), [OM-3](https://github.com/androidfanman/caduceus-om3)).
See [NOTICE](NOTICE) for what this builds on. No OM firmware is in this repository. Not affiliated with OM Digital
Solutions.
