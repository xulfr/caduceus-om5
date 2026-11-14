<h1 align="center">Caduceus for OM-5</h1>

<p align="center"><strong>Film looks and a full colour editor for the OM SYSTEM OM-5 Mark II. Experimental.</strong></p>

<p align="center">
  <a href="https://xulfr.github.io/caduceus-om5/"><b>Tour</b></a> &nbsp;·&nbsp;
  <a href="docs/INSTALL.md"><b>Install</b></a> &nbsp;·&nbsp;
  <a href="docs/USING.md"><b>Using it</b></a> &nbsp;·&nbsp;
  <a href="https://xulfr.github.io/caduceus-om5/looklab/"><b>LookLab</b></a> &nbsp;·&nbsp;
  <a href="docs/FAQ.md"><b>FAQ</b></a> &nbsp;·&nbsp;
  <a href="docs/SAFETY.md"><b>Safety</b></a> &nbsp;·&nbsp;
  <a href="ROADMAP.md"><b>Roadmap</b></a>
</p>

> [!CAUTION]
> ### Not tested on a camera
> **No build of this project has run correctly on a real OM-5 Mark II yet.** Three earlier builds of the work it is
> based on left the owner's camera in a boot loop (November 2026); OM's own firmware could be put back each time.
> The current build fixes the fault found after the third failure and passes every check in an emulator, which is
> not the camera. Flashing it can leave a camera unable to start. Read [Safety](docs/SAFETY.md) before anything else.
> This project is looking for someone willing to make the first camera test: see [the test plan](docs/FIRST_FLASH.md).

Latest: **v0.1.0-alpha1** (2026-11-14, emulator only) · OM-5 Mark II, firmware **1.1** · OM-5: [see below](#om-5-the-first-model)

## What it does

- **Films in Picture Mode.** The three Color Profile slots that OM left out of the OM-5 Mark II are back, and each
  can hold a film. The film's name shows as the title on the Picture Mode screen.
- **Films from one file.** Make up to ten films in [LookLab](https://xulfr.github.io/caduceus-om5/looklab/), save
  `LOOKS.BIN`, copy it to the card's `OM5MOD` folder. On a Color Profile, press the **trash button** to step the
  slot through the films. A film you have chosen stays in the camera: the card is needed only to choose another.
- **A full colour editor on the camera.** Saturation, **Hue and Lightness** for 12 colours, the tone curve
  (Shadows / Midtones / Highlights), Sharpness, Contrast and Shading for each slot, and a white balance of its own.
- **Monochrome Profile 1–3**, back as well, with filter, toning, grain and tone.
- **Live ND32 and ND64**, beside the camera's ND2–ND16.

Open-source firmware patches, part of the [Caduceus](https://github.com/cakelesscoder/caduceus-ep7) family
([E-P7](https://github.com/cakelesscoder/caduceus-ep7), [OM-3](https://github.com/androidfanman/caduceus-om3)).

## How it compares with Caduceus for OM-3

The OM-5 Mark II's firmware has far less free room than the OM-3's, so this build is the essentials.

| | OM-3 (v0.29.1) | OM-5 Mark II (this) |
|---|---|---|
| Films in the Picture Mode list | FILM 1–20, own entries | 3 slots (Color Profile 1–3), up to 10 films in the file, trash button steps through them |
| Film names | title, quick menu, shooting screen | Picture Mode title (12 characters) |
| Films kept in the camera | yes | yes: the chosen film's values are the slot's own settings |
| Hue / Saturation / Lightness, 12 colours | yes | yes |
| Tone curve, Contrast, Sharpness, Shading, WB shift | yes | yes |
| Blacks / Whites, split toning, grain, Glow, Halation | yes | no (no room yet: [roadmap](ROADMAP.md)) |
| Film recipe in EXIF | yes | no |
| Camera-tested | yes | **no** |

## Install

**[Install guide](docs/INSTALL.md).** In short, and only after [Safety](docs/SAFETY.md):

1. The camera is an OM-5 Mark II on firmware **1.1**, with a full battery.
2. Download this project (**Code › Download ZIP**), unzip, and double-click `Make SD card files (Mac).command` or
   `Make SD card files (Windows).bat`. It gets OM's official firmware from OM's server, adds Caduceus, and checks
   the result. It asks you to confirm that you know the build is untested.
3. Copy the `DCOLYMP` and `OM5MOD` folders from `card` to the top of the SD card. Keep the `restore` folder.
4. Camera off, **hold OK**, switch on.

## OM-5 (the first model)

The OM-5 runs a different, older program without these profiles. The
[second-stage builder](patches/ports/om-5-i-from-ii/README.md) rebuilds this project's E148 donor and fits
its application and resources into the E144 layout. It preserves the E144 controller component and
checks every feature range and resource transformation. It writes no install file by default.

**Developer-only and more experimental still:** hardware compatibility and a successful camera boot
are unestablished. The user patcher and launchers support E148 only. See [ROADMAP.md](ROADMAP.md).

## For developers

- `firmware/om5ii/`: the patch (`hsl.s` editor and profiles, `wb.s` white balance, `films.s` films, tables in
  `color_profiles.py`, `patch.json` with every changed range and its hashes).
- `tools/`: `oly_patch.py` (strict build from source), `oly_patch_record.py`, `mkrelease.py`, `tools/dev` (emulator).
- `card/mklooks.py`, `docs/FORMATS.md`: the `LOOKS.BIN` format. `looklab/`: the web app (no build step).
- `research/`: how the camera failures were traced. `HANDOVER.md`, `CLAUDE.md`: where the work stands.

```sh
python3 tools/oly_patch.py firmware/om5ii --stock OLY_E_148_1100_0000_0000.BIN --out generated/ii --decoded
```

Needs GNU binutils for `mn10300-elf`. `patch.py` needs only Python.

## Licence

Apache-2.0. See [NOTICE](NOTICE) for what this builds on. No OM firmware is in this repository.
