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
Results of the last run are in `alpha2-results.json`. Medium-mounted status and section-ready bits are
injected because the emulator does not reproduce that hardware lifecycle.

The same session is run on unmodified stock first. Every store into the image is logged. Any PC/address
pair absent from stock, or count above its stock baseline, fails. This distinguishes stock initialization
from patch-origin writes; it does not prove that all hardware paths are safe.

All results are **emulator only**. No loader, second CPU, ISP, physical persistence or exposure validation
is implied. Do not change `camera_tested` after a passing run.

`github-actions.yml` can be installed as `.github/workflows/tests.yml` by a credential with workflow
permission. It runs the source suite without firmware; no active workflow is claimed here.
