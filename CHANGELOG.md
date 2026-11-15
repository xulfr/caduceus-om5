# Changelog

## v0.1.0-alpha4 — 2026-11-15

**OM-5 Mark II, E148 firmware 1.1. Emulator only.** Package SHA-256
`590c2959206e8e06f5ab12efe4635f6674ac69e20879012e55ec6a798713d648`.

- Fixed the look title after returning from the lower Picture Mode rows and stepping looks again.
- Reject `@` display commands and invalid name bytes in look banks. Older saved names display `?` for those
  bytes without changing stored settings. LookLab and the Python writer reject `@` too.
- Installer reruns preserve custom `LOOKS.BIN` files. Complete firmware files replace their destinations
  only after writing succeeds, and the restore file is prepared before the patched update is published.
- The Mac launcher returns the patcher's failure status after its closing prompt, as the Windows launcher does.
- Added regressions for the reported failures, persisted names, startup gates and installer I/O failures.
  See the [audit](research/OM5II-ALPHA4-AUDIT-2026-11-15.md) for evidence and remaining hardware gaps.

## v0.1.0-alpha3 — 2026-11-15

**OM-5 Mark II, E148 firmware 1.1. Emulator only.** Package SHA-256
`f56a13335e1085e73f79db66e58440839022349a72746e1dcb5b32e2bc08e242`.

- The Picture Mode trash handler checks startup readiness before entering the look code in the last-loaded section.
- The camera rejects look banks longer than 832 bytes, including a valid ten-look bank with trailing data.
- The Windows launcher prompts once and returns the patcher's exit status after a refusal or failure.
- Corrected the README's description of which look an empty slot takes on its first press.
- Pinned the original OM-5 pre-alpha 1 build instructions to the source revision for its published hash.
- Updated the site, guides and LookLab to use the term "looks" for named custom colour profiles.

## OM-5 pre-alpha 1 — 2026-11-14

**Original OM-5, E144 firmware 1.2. Never run on any camera; for testers.** Package SHA-256
`70788992f032dad53bfa4e145b2147e376d3f25a62e2b1ce2929973fec26d1b4`, built by the tester from OM's two firmware files.

- The OM-5 Mark II program with Caduceus v0.1.0-alpha2, in the original OM-5's update layout with its own
  controller firmware.
- Tester page with the risks, a build guide, a step-by-step first test that starts with OM's own firmware, and a
  camera-test issue template. `tools/fetch_stock.py` downloads and checks OM's files.

## Earlier unreleased — 2026-11-14

- Original OM-5 developer candidate: ran the film regressions and a menu tour in OM-Emu's Mark II model (all pass,
  frames identical to alpha2), recorded that OM-Emu's OM-5 model cannot run it, and compared the two stock programs
  statically (SRAM layout, renumbered identifiers, controller firmware). Still developer-only and untested.

## v0.1.0-alpha2 — 2026-11-14

**OM-5 Mark II, E148 firmware 1.1. Emulator only; untested on a camera.**

- A film step now repaints the Picture Mode screen at once: the title takes the new film's name and
  the rows its values, through the screen's own panel update.
- The trash button steps films only while the highlight is on the Picture Mode row. On the tone,
  Shading, Sharpness and Contrast rows it does nothing; in the colour wheel it still switches
  Saturation / Hue / Lightness.
- Checked that the super control panel shows the film's name while its Picture Mode cell is highlighted.
- Emulator regressions added for the repaint, the rows, the return to the Picture Mode row and the
  control panel name. The E144 developer candidate was rebuilt on this donor.

Known limitations: after returning from the lower rows the title reads "Picture Mode" until the mode
changes; the emulator limits listed under alpha1 are unchanged.

## Development before alpha2 — 2026-11-14

- Added the GitHub Pages tour with labelled emulator screenshots, feature comparison and safety banner.
- Added reproducible Markdown guide generation with shared navigation and local guide links.
- Added the roadmap and development rules for the community handover.

- Added format parity, corruption, release-integrity, guide-link and firmware emulator regression tests.
- Included the previously missing starter LOOKS.BIN in the release and aligned writer validation.
- Made developer build/run wrappers portable and removed automatic deletion and implicit hash re-recording.

- Imported the E144 donor builder, rebuilt with the Caduceus films donor, and added independent output checks.
  E144 remains developer-only, with no default install output and no established hardware compatibility.

## v0.1.0-alpha1 — 2026-11-14

**OM-5 Mark II, E148 firmware 1.1. Emulator only; untested on a camera.**

- Established the standalone Apache-2.0 project, with attribution in NOTICE.
- Restored three Color Profiles and three Monochrome Profiles; added Hue and Lightness editing,
  tone controls, per-profile white balance and ND32/ND64 menu entries.
- Added up to ten films from `OM5MOD/LOOKS.BIN`, assigned independently to the three Color Profile
  slots with the trash button. Film names appear in the Picture Mode title.
- Added LookLab's 67-film library, local preview and binary writer, plus the Python writer.
- Added a pure-Python release patcher that checks stock and result hashes and requires acknowledgement
  of the untested build. No OM firmware is distributed in the repository.
- Added safety, installation, first-test and format documentation, and the prior failure analyses.

Known limitations: film changes need a highlight move to redraw; trash also changes films on other
profile rows; no super control panel film name. The emulator cannot validate boot loading, the second
processor, the image processor, physical persistence or actual exposures. Earlier builds in the
source project's history caused three camera boot loops. See [Safety](docs/SAFETY.md).
