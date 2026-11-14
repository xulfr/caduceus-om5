# Changelog

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
