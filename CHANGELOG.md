# Changelog

## Unreleased — original OM-5 builder on the alpha12 donor (2026-11-16)

- The original OM-5 builder now documents and defaults to the current Mark II source, v0.1.0-alpha12
  (donor package `cddd7a1f…cd3fa`). Pre-alpha 1 (alpha2 donor) is withdrawn.
- The builder packs the transplanted main program with the donor patch's own repack settings. These include the
  `stock-page` stream-length rule. Each main stream is checked for length faults, and `build.json` records `main_packing`.
- Pre-alpha 2 has not been built from OM's files, and it has no published checksum. Never run on any camera.
- Refreshed the original OM-5 tester page for pre-alpha 2. The README, Safety, Roadmap, first-flash checklist and
  handover now lead with alpha12's camera result instead of the older build reports.

## Camera result — 2026-11-15

**v0.1.0-alpha5 and alpha6 boot-looped on the owner's OM-5 Mark II on 15 November 2026.**
[Camera report](research/OM5II-FIFTH-BOOT-FAILURE-2026-11-15.md).

## v0.1.0-alpha12 (owner camera checks complete)

- Restores the Monochrome Color Filter swatches, selection outline and centre colour.
  The hook draws the ring over the stock page. The panel requests a repaint when the filter page is active.
  Alpha12 keeps the stock labels and widget positions.
- Package SHA-256 `cddd7a1f1320e7680bec9e8430e25c69857c2f4bf764e571d6bfffb775acd3fa`. [Validation results](tests/alpha12-results.json).
- The owner reports that the remaining filter graphic issue is fixed. Alpha12 is the current
  experimental build. [Release notes and camera findings](releases/v0.1.0-alpha12/README.md).

## v0.1.0-alpha11 (boot and both alpha10 fixes confirmed)

The owner confirmed boot, both CP icons and an operable Monochrome Color Filter page.
The centre graphic was absent. [Camera report](research/OM5II-ALPHA11-CAMERA-2026-11-16.md).

- The Monochrome Color Filter page returns to alpha9's rendering. Restored the stock `0x107e` image,
  both widget rectangles and the stock painter. Removed the paint hook, ring, “Level” text and
  child 3 invalidation. The native filter header and both dials remain available. The picker graphic
  is postponed pending camera validation.
- The out-of-range `0xffff` image lookup is the leading hypothesis for the alpha10 restart.
  The physical cause remains unproved. See the [filter and CP investigation](research/OM5II-MONO-FILTER-CP-2026-11-17.md#alpha11-follow-up).
- The CP carousel's ND32 and ND64 slots now reference existing ND32 and ND64 artwork.
  Static verification covers the image IDs and resource pointers. The owner confirmed both icons on the camera.
- Package SHA-256 `5384eafef3cb06de4761dba50a09112135fa2cdfacb6716d9e4d0423f5b7072a`. [Validation results](tests/alpha11-results.json).

## v0.1.0-alpha10 — 2026-11-17 (booted, filter page restarted the camera)

The owner reported that alpha10 booted. Opening Monochrome Color Filter restarted the camera once, and
ND32 / ND64 worked from the CP carousel with empty icons. [Camera report](research/OM5II-ALPHA10-CAMERA-2026-11-17.md).

Fixes from the [alpha9 camera report](research/OM5II-ALPHA9-CAMERA-2026-11-16.md):

- **Color Profile Shading works.** Its slider was grey and ignored the dials: OM's firmware has no setting
  description for the Color Profiles' Shading, so it dropped every change. Caduceus now supplies one.
- **ND32 and ND64 appear when holding the CP button** (when ticked in CP Button Settings). The CP carousel only
  offered the items in its list of allowed values, which stopped at ND16.
- **Monochrome Film Grain shows Off / Low / Std / High** in the sidebar and the strip, and the **Color Filter row
  shows "Filter"** instead of an empty cell.
- **Monochrome colour filter picker.** The Color Filter page (Monochrome Profile 1–3, second sidebar row) now
  draws the filter: eight colour blocks in the order the front dial steps them (None, Yellow, Orange, Red,
  Magenta, Blue, Cyan, Green, Yellow-Green, as on the OM-3), the selected one outlined and repeated in the centre
  (grey for None). The rear dial's value is labelled "Level" instead of a stray "Vivid". The dials already
  changed and kept the filter and level in the emulator; alpha9's notes said otherwise because only the rear
  dial was tried.
- **CP button with only ND32 / ND64 ticked.** The CP button's "is any item ticked" test skipped ND32 and ND64,
  so with only those ticked it found nothing to offer. It now counts them (after the first half-press).
  Static analysis only: the emulator has no CP button for this camera.
- Known: colour grain for Color Profiles is deferred with the other effects; per-profile white balance is behind
  the scenes, not a Picture Mode row (README).
- Emulator checks: see [results](tests/alpha10-results.json). The build audit can now also compare against alpha8.

## v0.1.0-alpha9 — 2026-11-16 (booted on the owner's camera)

The owner reported that alpha9 boots and the colour wheel draws correctly on the camera. Package `2e9777ce…fbc50`. [Camera report](research/OM5II-ALPHA9-CAMERA-2026-11-16.md).

- Color Profiles 1–3 and Monochrome Profiles 1–3 show their own numbered icon in the carousel, sidebar, super
  control panel and shooting screen (alpha8 showed C2 or M for all three).
- The edited-profile icon on the shooting screen no longer disappears after a profile is changed
  (images `0x3d66..0x3d68` and `0x3d5e..0x3d60`).
- The Tone Curve row shows an icon for every Shadows / Midtones / Highlights state (27 states).
- The colour wheel and tone curve are drawn on the Picture Mode screen (block graphics, not OM-3's artwork).
- The shooting screen draws ND32 and ND64; CP Button Settings lists Live ND32 and ND64 and they can be switched.
- Activity on the Picture Mode screen keeps it open, and the trash button repaints the HSL axis.
- Known: ND64's digits look squashed and ND32 has a gap; Monochrome Color Filter and Film Grain rows still show
  placeholders; the palette and drawing budget are unverified on a camera.
- All 19 look/menu regressions, the startup, arming, unarmed-PC and stale-number probes, the UI, graphics, icon
  and Live ND checks, the static rules and the build audit passed in OM-Emu. [Results](tests/alpha9-results.json).

## v0.1.0-alpha8 — 2026-11-15 (boot confirmed on camera)

- The owner confirmed boot, SD-card look cycling and names, Color Profile controls, and Live ND32/64
  on a physical OM-5 Mark II. Four UI defects remain. [Camera report](research/OM5II-ALPHA8-CAMERA-2026-11-15.md).
- Stock disassembly confirms that the loader submits sections 1 through 10 in order. Section-2 hooks
  now check the armed state in their own section. White-balance processing runs from section 4 after arming.
- The first shutter half-press can arm the patch after all ten sections finish initializing. It applies
  the selected profile and repairs stale profile numbers 903 and 989. RAM handle validation and the
  stock-page compressed-stream rule carry forward from alpha7.
- All 19 look/menu regressions, the startup and arming probes, the unarmed PC check, and the build
  and static audits passed. [Verification](tests/alpha8-results.json).

## v0.1.0-alpha7 — 2026-11-15 (blocked)

- Added startup gating, RAM handle validation and stale profile-number repair.
- Some startup gates call section 8 from section 2 before section 8 is loaded. The installer refuses
  this package (`c6f3a8fa…243a`). [Load-order finding](HANDOVER.md).

## v0.1.0-alpha6 — 2026-11-15 (boot loop on a camera)

- Same camera code as alpha5, byte for byte. Only the way the program is compressed in the update file changes.
- Alpha5's compressed block for section 7 was exactly 611 × 4096 bytes long, and the camera's loader ignores the
  32-byte block header when it works out how much to read. Alpha6 keeps each compressed block at the same offset
  inside a 4 KiB page as OM's own firmware, and the builder refuses unsafe lengths.
- The resource block is byte-identical to the 8 November build's, which started on the camera.
- This is the best-supported explanation of the alpha5 boot loop, not a proven one:
  [stream length note](research/OM5II-STREAM-LENGTH-2026-11-15.md). Package `2bb95563…3e84`.
- If the picture mode looks wrong on the first start, choose a picture mode once.

**v0.1.0-alpha5 boot-looped on the owner's OM-5 Mark II** immediately after the update; OM's 1.1 restored from
the card. The installer now refuses alpha1–alpha5. Details: [fourth boot failure](research/OM5II-FOURTH-BOOT-FAILURE-2026-11-15.md).

## v0.1.0-alpha5 — 2026-11-15

**OM-5 Mark II, E148 firmware 1.1. Emulator only.** Package SHA-256
`98bd2433bef76706f4c71706439feb23d05524477b4d078135c1675ab97880c2`.

- The title restore added in alpha4 wrote a 32-bit word into the camera's 16-bit row descriptor and zeroed the
  title's style index on every layout of a named slot. It now changes only the title id. No visible effect was
  seen in the emulator, but it was a write into the camera's own state outside the intended field.
- A look without a white-balance shift now sets the shift to 0, as LookLab previews it. Before, it kept the
  shift of the look before it, so a look's colour depended on the order you stepped through them.
- Corrected the tone-curve ID comments in the firmware source, and the guides' description of the title after
  returning from the lower rows.
- Every emulator case now checks the row descriptor and each slot's WB record. See the
  [audit](research/OM5II-ALPHA5-AUDIT-2026-11-15.md) for evidence and remaining hardware gaps.

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
