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
