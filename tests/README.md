# Checks

Run from the repository root with Python 3.10+ and Node.js (the emulator asks for Node 26; the alpha2 run used Node 22.23 without changes).

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

The default suite verifies every library film against the JavaScript writer, round trips, signed
boundaries, malformed inputs, the checked-in starter bank, safety refusal and generated site links.
Full release reproduction is explicitly skipped unless `OM5_STOCK` names the official E148 1.1 file:

```sh
OM5_STOCK=/path/to/OLY_E_148_1100_0000_0000.BIN python -m unittest discover -s tests -v
```

No stock firmware is downloaded by the tests. Supply it yourself or use patch.py's verified download.

## Firmware emulator regressions

Build the recorded source with GNU `mn10300-elf` binutils on PATH:

```sh
python tools/oly_patch.py firmware/om5ii --stock /path/to/OLY_E_148_1100_0000_0000.BIN --out generated/strict --decoded
git clone --branch fix/e148-ipi-stride https://github.com/xulfr/om-emu.git generated/om-emu
python tests/run_emulator.py --emu generated/om-emu --build generated/strict --stock /path/to/OLY_E_148_1100_0000_0000.BIN --out generated/regressions
```

Use a new output directory for each run; `--case NAME` selects an individual case. The suite retains
raw session logs, screenshots, expectations and results.json. It checks four and ten films, stepping,
wraparound, independent slots, all H/L and saturation values, tone and WB records, names, bad CRC,
out-of-range records, mounted empty card and no card. Since alpha2 it also checks that each film step
repaints the screen (two films that differ only in name must give different frames), that the trash button
does nothing on the tone, Shading, Sharpness and Contrast rows, that it steps again after returning to the
Picture Mode row, and that the super control panel's frame differs from stock once a slot holds a film.
Alpha3 adds a valid maximum-size bank with a trailing byte and a pre-arm Delete case with the section-10
extension replaced by stock bytes. Alpha4 adds a title check after returning from lower rows, name-command
and control-byte rejection, and safe display of names persisted by older releases. Alpha5 runs every case with
`layout_guard.mjs` as PRE: it records the Picture Mode row descriptor at the updater's last call and again where
stock reads it, and fails if anything but the title id changed (alpha4 zeroed the style index). Every slot that
holds a look also has its WB record checked: a look without a shift must leave 0 / 0, and the live A/B and G/M
of the current profile must match. Results are in `alpha5-results.json` (19 look/menu cases plus the separate
startup probe). Medium-mounted status and, in
armed cases, section-ready bits are injected because the emulator does not reproduce that hardware lifecycle.

The same session is run on unmodified stock first. Every store into the image is logged. Any PC/address
pair absent from stock, or count above its stock baseline, fails. This distinguishes stock initialization
from patch-origin writes; it does not prove that all hardware paths are safe.

All results are **emulator only**. No loader, second CPU, ISP, physical persistence or exposure validation
is implied. Do not change `camera_tested` after a passing run.

### Color Profile grain (removed)

Color Profile grain was removed on 2026-11-19 (no grain in colour pictures on the camera; stock grain is
monochrome-only). Its tests, `run_cp_grain.py` and `cp_grain_assert.mjs`, are on the experiment branch
`claude/cp-grain-experiment`.

### Blacks / Whites curve (retired)

`tests/bw_assert.mjs` tested the brightness-curve hook (`0x60385f08`), which the camera showed had no visible effect
(research/OM5II-V020DEV-CAMERA-2026-11-19.md). Black / White now go into the split-tone delta tables, checked by
`tests/st_assert.mjs` in the `run_bw_tint.py` cases below.

### Black / White on the tone page and split tone (v0.2.0-dev)

`tests/run_bw_tint.py` drives the tone page (INFO into Black/White, the dials, the INFO cycle, Color Profile 2, a stock
mode afterwards), the Split toning row (phase 3a) and the split-tone tints (12 cases total). Since the OM-3 v0.41 wheel keys (2026-11-28) the
tints have no key on the wheel: their cases set the tint cells first (`tests/seed_cells.mjs`); the Tint-group key cases
and the wheel tint gamma-cache pair are retired until the Split toning row. `tests/bw_tint_assert.mjs` checks the settings, OM's own
tone values, P's curve values and states; for tint cases it runs `tests/st_assert.mjs`, which recomputes every delta
from the tint cells and calls the camera's R/G/B curve setter with test ramps (every output entry must match; with the
tint flag cleared or only sections 1 and 2 ready, the stock tables must pass through). The gamma cases enter at
`0x603e6a3b`, trace the allowed section for all 1023 incomplete ready masks and check both stock exits.

```sh
python tests/run_bw_tint.py --emu generated/om-emu --build generated/strict --out generated/bw-tint
```

`tests/run_boot_arm.py` starts boot.s's background task as its FastEndCb hook would (OM-Emu does not run that
callback) and checks, with no half-press, that the patch arms, reads `LOOKS.BIN` and `CADUCEUS.BIN`, refuses a card
block made for another build or damaged, and that the first half-press runs the pending refresh. The page-graphics
and Monochrome filter tests put `CADUCEUS.BIN` for the build under test on their card (`tests/card_block.py`).

```bash
python tests/run_boot_arm.py --emu generated/om-emu --build generated/strict --out generated/boot-arm
```

`tests/run_look_defaults.py` applies a look to Color Profile 1, changes the wheel (each axis) or the tone curve,
holds OK (`hold:ok:3000`) and checks with `tests/look_defaults_assert.mjs` that the values return to the look and
that the Reset OK Hold hint shows only while they differ. Black / White and a slot without a look reset to 0.

```bash
python tests/run_look_defaults.py --emu generated/om-emu --build generated/strict --out generated/look-defaults
```

`tests/run_wheel_keys.py` (14 cases) drives the colour wheel and the Split toning row with the OM-3 v0.41 key map: INFO steps Hue → Saturation →
Lightness, the colour dial past colour 1 gives Sat. All (skipped on Hue / Lightness), INFO from Sat. All returns to
colour 1, Delete changes nothing, and the "H/S/L [INFO]" hint is the same on every axis. `tests/wheel_keys_assert.mjs`
reads the settings and P. `tests/seed_cells.mjs` (also used by `run_bw_tint.py` for the tints, which have no key on
the wheel now) writes setting cells before the keys. The Split toning cases check the focused row (the panel's
per-row state bytes), its Shadows / Highlights pages and that Picture Mode reopens on the wheel row.

```bash
python tests/run_wheel_keys.py --emu generated/om-emu --build generated/strict --out generated/wheel-keys
```

### Live ND shooting labels

Run the shooting UI with the display-side reads for settings 1709–1711 supplied by the fixture.
It checks the prefix bitmap and whether the shooting screen draws the native `-LV` suffix.

```sh
for lv in 0 1; do
  for step in 4 5 6; do
    ND_LV=$lv ND_STEP=$step PRE=tests/nd_shooting_labels.mjs POST=tests/nd_shooting_labels.mjs \
      OM_EMU_DIR=generated/om-emu bash tools/dev/run.sh BUILD "generated/nd-$step-$lv" 'ok ok ok'
  done
done
```

## Startup fault injection and build audit

`startup_assert.mjs` is a POST module for `sess.mjs`. It checks all incomplete section masks, task identity,
allocation failure/retry, state-clear and handle bounds. It tests the native half-press hook with all incomplete masks, then calls the section-8 allocation path
directly for fault injection. Update the probe's ELF symbol addresses if they move. Run a session without keys:

```sh
OM_EMU_MODEL=E148 PRE="$PWD/tools/dev/mount.mjs" POST="$PWD/tests/startup_assert.mjs" node tools/dev/sess.mjs generated/om-emu generated/strict/decoded/0100.bin generated/strict/decoded/0101.bin generated/startup '' --watch --json
```

Compare image stores to a stock session with the same empty key script and PRE, omitting POST.
`audit_build.py` checks native loaded bounds, every declared preimage/postimage, containment of all byte
changes against stock and a previous build, unchanged resources/loader bounds and the 768 ND selector inputs:

```sh
python tests/audit_build.py --build generated/strict --previous generated/previous --stock "$OM5_STOCK" --out generated/build-audit.json
```

Host tests in `test_installer.py` use temporary directories and fake firmware bytes to exercise custom-bank
preservation, fresh starter creation, write failure and failed recovery preparation. They never download firmware.

`github-actions.yml` can be installed as `.github/workflows/tests.yml` by a credential with workflow
permission. It runs the source suite without firmware; no active workflow is claimed here.

## Start-up gating and static rules (alpha8)

```sh
K='ok ok right right right right right right right right menu menu'
EXPECT=inert   POST=tests/unarmed_assert.mjs OM_EMU_DIR=... bash tools/dev/run.sh BUILD OUT1 "$K"
EXPECT=applied POST=tests/unarmed_assert.mjs OM_EMU_DIR=... bash tools/dev/run.sh BUILD OUT2 "$K s1"
python3 tools/dev/static_rules.py BUILD STOCK.BIN
```

`tests/unarmed_pcs.mjs` (PRE, with `PCS=file`) records every executed address in the patch extensions during
a session without `s1`. `python3 tests/unarmed_pcs.py BUILD file` accepts only gates and replays of OM's
instructions and rejects any recorded PC in sections 3, 4 or 8 and later.
`N989=1 PRE=tests/stale_number.mjs POST=tests/stale_number_assert.mjs` with keys `wait:300 s1`
injects stale 903 and 989. The probe checks that arming restores Natural and clears both numbers. `tests/startup_assert.mjs` also checks handle alignment and the block magic.

The first pair checks that a Color Profile selected before any half-press does not run the project's refresh and
that the arming half-press applies it. The static rules are camera lessons an emulator does not show: no `0xfb`
opcode, aligned data tables, safe compressed stream lengths. Emulator and host only.

## UI activity and HSL axis repaint (WIP UI candidate 2)

```sh
python tests/run_ui_activity.py --emu generated/om-emu --build generated/strict --out generated/ui-activity
```

Opens the Picture Mode direct screen on Color Profile 1 with a test LOOKS.BIN, then repeats one control seven
times 2.5 s apart (beyond the screen's 8000 ms timer 500): trash, INFO and dials on the wheel, INFO and both
dials on Tone Curve, trash and a dial on the mode strip. Each must keep state `0x0418`; an idle screen must
close. The axis case presses trash three times on the wheel and requires axis 1, 2, 0 with one timer restart
and one colour-page invalidation (`0x60d49294` on a page widget) per press. OM-Emu repaints the whole plane, so
frames cannot show the camera's missing repaint; the invalidation count is the check. `tools/dev/sess.mjs`
accepts `main+N` / `sub-N` to turn the dials.

`tests/audit_build.py` accepts a changed resource block only when everything outside record 0 is identical and
the decoded record differs only at pointer words of aliases declared in patch.json; it reports the image IDs.
`tools/oly_resource_recipe.py PATCH --stock STOCK TARGET=SOURCE` adds such an alias and records its LZ4 recipe;
re-record hashes with `tools/oly_patch_record.py` afterwards. `firmware/om5ii/cp_nd.py --spec STOCK` rewrites the
CP Button Settings data edits. The unarmed PC scan ignores assembler-local `.L*` labels (relaxed branches inside
a function).

## Tone Curve row icons

```sh
python tests/run_tone_icons.py --emu generated/om-emu --build generated/strict --out generated/tone-icons
```

Steps Shadows, Highlights and Midtones through all 27 sign combinations on Color Profile 1 and reads the
selected Tone Curve row: never blank, 27 different icons, and with Midtones at 0 the glyph bends the way the
values say. `tools/dev/imgwatch.mjs` (PRE, `IMG_LO` / `IMG_HI`) prints each image-table read. Emulator only.
