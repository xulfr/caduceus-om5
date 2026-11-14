# Changelog

## Unreleased — 2026-11-14

- Added the GitHub Pages tour with labelled emulator screenshots, feature comparison and safety banner.
- Added reproducible Markdown guide generation with shared navigation and local guide links.
- Added the roadmap and development rules for the community handover.

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
