# Shared Caduceus Control Panel for the OM-5 (issue #4), 18 Nov 2026

Proposal: [xulfr/caduceus-om5#4](https://github.com/xulfr/caduceus-om5/issues/4) by cakelesscoder. The owner agreed
in principle on 18 Nov 2026 ("one control panel"). This note checks how much work it is and what could go wrong. It
is a desk study: no code was written for caduceus-ep7, and nothing here touches the firmware.

Sources: this repository at `a72851a` (`docs/FORMATS.md`, `card/mklooks.py`, `looklab/app.js`,
`tools/mkrelease.py`, tests), and caduceus-ep7 `main` as read on 18 Nov 2026 (`docs/CONTROL_PANEL.md`,
`webapp/src/cameras.ts`, `webapp/src/pack.ts`, `webapp/src/targets/types.ts`, `webapp/src/targets/om3.ts`). The
caduceus-ep7 files were read through the web and paraphrased. Re-check them before writing code.
`sharecode.ts`, `targets/index.ts`, `targets/ep7.ts`, `split.ts`, `preview.ts` and the vendored `om3.ts` were not read.

## What the shared panel expects

- **Profile**: one `Cam` id and one `CameraProfile` entry in `webapp/src/cameras.ts`. It sets the ranges (`hl`, `sat`,
  `wb`) and flags (`mono`, `tints`, `lensCorrection`, `arts`, `settings`, `lookNr`, `lookHw`, `halo`).
- **Target**: `webapp/src/targets/<cam>.ts` implementing
  `Target { id; label; status: 'ready' | 'soon'; doc?; note; supports(look): true | string; export(pack): ExportFile[] }`.
  Import is optional. List it in `targets/index.ts` as `status: 'soon'` until it has run the files.
- **Tests**: the built-in library exports without throwing; the output matches the firmware's own writer byte for byte
  on a few looks; round-trip if there is an import. Then add credit to NOTICE and BODIES.md.
- **Shared model**: `Pack` (`caduceus-pack/1`, up to 32 looks) of `Look`. Share codes: look codes v1–8 and `pk1_`
  pack links.

## Field mapping: shared `Look` → OM5F record

| Shared `Look` | OM5F (docs/FORMATS.md) | Status |
|---|---|---|
| `hue[12]` −7..7 | 0..11, −7..7 | Same range. **Check the sector order and sign** (below). |
| `light[12]` −7..7 | 12..23, −7..7 | Same range |
| `sat[12]` −5..5 | 24..35, −5..5 | Same range |
| `wb: {a_b, g_m} \| null` | 36 flag, 37, 38 (−7..7) | Direct match (`null` → flag 0) |
| `tone.shadows / midtones / highlights` −7..7 | 44, 45, 46 | Direct match |
| `tone.blacks / whites` | — | Dropped (reported) |
| Contrast, Sharpness, Shading | 41 (−2..2), 42 (−2..2), 43 (−5..5) | **Unclear where the shared model keeps them**: see open questions |
| `name` ≤ 12 | 64..75, ≤ 12 printable ASCII | OM-5 also forbids `@` and leading or trailing spaces: `supports()` must refuse those |
| `kind: 'mono'` | — | Not supported: the OM-5 looks are colour only (`supports()` reason) |
| `grain`, `effect`, `split`, `curve`, `matrix`, `art_effect`, `film_grain`, `lens_correction`, `vignette`¹, `tone_balance`, `halation`, `film_wb`, `advice` | — | Dropped and reported, as the OM-3 target does |
| Pack of up to 32 looks | 1..10 looks | Export the first 10 colour looks and list the rest, as the OM-3 target does past 20 |

¹ Unless the shared model's `vignette` (−5..5, "stored only") is meant to carry Shading: see open questions.

Header, CRC-32 and length rules stay exactly as in `card/mklooks.py`. The OM5F file shares only the 64-byte record
layout with the OM-3 file. The header (`OM5F`, version 1, 32 bytes) and the 80-byte record-plus-name are this
project's own. An OM-3 `LOOKS.BIN` is not an OM-5 file, and LookLab already refuses it.

Inference: the OM-5 profile would be roughly `hl: 7, sat: 5, wb: 7, mono: false, tints: false,
lensCorrection: false, arts: ['off'], settings: true, lookNr: false, lookHw: false, halo: false`. Check each flag's
exact meaning against `cameras.ts` before using it.

## Open questions for cakelesscoder (ask on #4 or caduceus-ep7)

1. **Contrast, Sharpness, Shading.** `CameraProfile.settings` says these are "saved in the look" (true for the
   OM-3), but the `Look` type as read lists them only under `advice` (Contrast, Sharpness) and has `vignette` (−5..5).
   Where does the OM-3 target take record bytes 41–43 from? The OM-5 must use the same source, or the starter looks
   will lose Contrast, Sharpness and Shading on export.
2. **Hue sector order and sign.** The shared hue arrays are in "UI sector order". OM5F runs clockwise from Yellow
   (FORMATS.md). The OM-3 target "copies hue numbers unchanged" and calls the direction an open question. OM5F reuses
   the OM-3 order, so copying unchanged should be right if `om3.ts` does not reorder. Confirm this from `om3.ts`.
3. **Name rules.** Does the shared panel allow `@` or leading and trailing spaces? If so, the OM-5 target must refuse
   them in `supports()`, never rewrite them silently. `@` is a display command on the camera.
4. **Library.** LookLab's `films.json` is adapted from the OM-3 films. Does the shared `data/library.json` include the
   OM-3 films, so OM-5 users keep "Portra 400" and the others?
5. **Preview.** LookLab's preview uses the OM-3 fitted numbers, which the shared panel's `preview.ts` probably also
   has. Neither has been compared with an OM-5 photo; the target's `note` should say so.

## Effect on this repository

- `looklab/films.json` is also the source of each release's starter `LOOKS.BIN` (`tools/mkrelease.py`) and
  of `tests/test_formats.py`. Keep it, or replace it with a pinned export from the shared library. Do not retire it with
  LookLab.
- `looklab/app.js` is the JavaScript writer in the Python/JavaScript parity tests (`tests/looks_bridge.cjs`). If
  LookLab is retired, keep a small local writer for those tests, or test the shared target's output against
  `card/mklooks.py` with checked-in fixtures.
- The byte-for-byte test the shared panel asks for is easy to meet: generate fixtures with `card/mklooks.py` from the
  starter looks and some edge cases (no WB, all-extremes, a 12-character name, 10 looks), and compare them in
  caduceus-ep7's test suite.
- The links to LookLab are in README.md, docs/USING.md, docs/FAQ.md, index.html, the pages/ guides (through
  `tools/mksite.py` navigation) and `tests/test_site.py`. Switch them once the shared target is `ready`, not before.
- New OM-5-only fields (none are pending) would follow cakelesscoder's "Look field: <name>" process before they
  reach the panel.

## Safety

The card file is not firmware. The camera validates length, magic, version, count, CRC and every range, and ignores a
bad file as a whole (FORMATS.md). An export bug should show up as "no looks", not as a failure to start. That has
not been tested on a camera with a panel-written file. Until the target has an owner-run camera check with the
exported file's SHA-256, keep it at `status: 'soon'` and keep LookLab as the documented writer.

## Suggested order

1. Ask questions 1–3 on #4.
2. Write `targets/om5.ts` and the `cameras.ts` entry in a caduceus-ep7 PR (`status: 'soon'`), with
   `card/mklooks.py` fixtures as byte-for-byte tests and an optional `LOOKS.BIN` import that mirrors `readLooks`.
3. The owner loads one panel-exported `LOOKS.BIN` (hash recorded) on the OM-5 Mark II. Then switch to `ready`.
4. Here: point the README and guides at the shared panel. Keep LookLab as a local preview and debug page, and keep
   `films.json` and the parity tests.
