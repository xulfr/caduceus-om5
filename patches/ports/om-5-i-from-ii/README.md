# Original OM-5: second-stage donor builder

**Pre-alpha for testers ([docs/OM5_PREALPHA.md](../../../docs/OM5_PREALPHA.md)). Emulator/host checks only. No camera test and no established hardware compatibility.**
This uses the E148 1.1 Caduceus application on the E144 1.2 update layout. It is not a native patch of
the original OM-5 application, and a successful package build is not evidence of a successful boot.

## Build

Use Python 3.10+, Pillow, GNU `mn10300-elf` binutils and libjpeg-turbo `jpegtran`. The compression and
container modules are included; no external liblz4 is required. On Ubuntu, Pillow and jpegtran are
available in `python3-pil` and `libjpeg-turbo-progs`. Supply both official firmware files.

```sh
python3 patches/ports/om-5-i-from-ii/build.py \
  --stock OLY_E_144_1200_0000_0000.BIN \
  --donor-stock OLY_E_148_1100_0000_0000.BIN \
  --donor-patch firmware/om5ii \
  --out generated/e144
```

The current `firmware/om5ii` patch is also the default donor. Use `--as`, `--ld`, `--objcopy` and
`--jpegtran` for explicit executable paths. Each output directory must be new.

By default this writes `decoded/`, `build.json` and the exact E144 stock restore under
`restore-stock/DCOLYMP/E1449999.BIN`. It writes **no install file**. The explicit developer flag
`--write-untested-package` also writes `install/DCOLYMP/E1449999.BIN`. The builder never accesses a
camera. Keep these generated vendor images local; do not commit or redistribute them.
The consumer `patch.py` and launchers continue to support only E148.

## What is checked

- Full stock hashes: E144 `a0c91f3ac7caaf0925b2af609e711183cf3b5982b3333224bcef26c0c5943d11`;
  E148 `9de5d77e1d290fa2ed4ebc7d75cee0ed490befbc89566722467d1d421d66d637`.
- The donor strict build, all declared feature ranges (including films), loaded-section bounds,
  and known failed package exclusions.
- Twenty-one inspected native address operands for the E144 resource map. Numeric coincidences
  elsewhere are not changed. Update filename patterns and three model defaults become E144.
- Eleven common-resource banks, retaining all 557 leaf records exactly and repairing checksums.
- All 116 picture IDs fit E144's 7 MiB slot after lossless JPEG entropy optimization. Each JPEG's
  decoded pixels are compared before and after. No pictures are removed or downsampled.
- All five E144 outer headers, component addresses and sizes, and the complete E144 controller
  component (010e) are preserved. The E148 startup library stays with its matching application.
- Container checksum and compression round trips, exact stock restore, and no overlapping slots.

The shared GPIO table and 180 matching parameter descriptors are static evidence only. Sensor/ISP,
IBIS, charging/USB, retained settings, calibration, controller protocol, bootloader acceptance and
recovery are unresolved. Do not use the Mark II install instructions for this transplant.

## Emulator and static findings (2026-11-14)

OM-Emu's original OM-5 model refuses this program (its handlers are tied to OM-5 1.2 code). In OM-Emu's Mark II
model, which uses the same board family, the candidate passes all 13 film regressions and draws a 23-step tour
identically to the Mark II build. The relocated resource addresses are not exercised there. A static comparison
finds one on-chip SRAM layout shift and about 90 renumbered identifiers between the two programs. Details, limits
and next steps: [research/OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md](../../../research/OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md).
None of this shows that the camera would boot it.

## Reproducible verification

`build.json` records the donor hash, source/tool versions, preserved ranges and resource statistics.
The checkpoint's compact result is in `tests/e144-results.json`; it is not a downloadable camera image.
Run the independent output checks with:

```sh
OM5I_STOCK=/path/to/OLY_E_144_1200_0000_0000.BIN \
OM5_STOCK=/path/to/OLY_E_148_1100_0000_0000.BIN \
OM5I_BUILD=generated/e144 OM5II_BUILD=generated/strict \
  python3 -m unittest discover -s tests -p test_e144.py -v
```

Imported from the five specific files listed in HANDOVER.md, at
`xulfr/oly_fw_analysis` branch `fix/om5ii-no-image-stores`; authored by xulfr. This repository uses its
own Apache-2.0 container implementation. The donor patch defaults and local documentation were adapted.
