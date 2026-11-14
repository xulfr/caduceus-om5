# Handover: Caduceus for OM-5 (state at 2026-11-14, end of session 1)

Read this first in a new session. It replaces re-deriving the context.

## Goal (owner: xulfr)
A dedicated, stripped-down `caduceus-om5` repository (Apache-2.0, as the Caduceus family) with OM-5 Mark II (E148 fw 1.1)
first, OM-5 (E144 fw 1.2) second, a GitHub Pages site like androidfanman.github.io/caduceus-om3 (tour, install, using,
FAQ, LookLab), and films loaded from one `LOOKS.BIN`. Owner will hand the project to the community.
Must-haves: film slots from LOOKS.BIN made by the web app, full HSL, ND64, tone curve. Effects (grain, halation) optional.

## Hard facts (do not lose)
- **No OM-5 II build has ever run correctly on a camera.** Three builds boot-looped (4, 5, 8 Nov 2026; owner restored
  stock each time). The 12 Nov candidate (`42fcf6de…`, heap state, no image stores) was NOT flashed as far as the
  repo records. Ask the owner whether it has been flashed since. Everything here is emulator-only.
  The site and patcher must say so and must not present this as a tested install.
- Sources this repo was built from: `xulfr/oly_fw_analysis` branch `fix/om5ii-no-image-stores` (patches/hsl/om-5-ii,
  tools/, research/OM5II-*.md, patches/ports/om-5-i-from-ii). All of that OM-5 code is xulfr-authored, EXCEPT
  `tools/oly_container.py` (fishku, unlicensed): replace it with a container module written from Caduceus's
  `firmware/oe_container.py` (Apache-2.0) before publishing.
- The earlier `caduceus-om5-fork.bundle` (branch port/om5) was not found in any cloud repo. Not needed now.
- References (read-only): `androidfanman/caduceus-om3` v0.29.1 (site layout, LookLab = `webapp/`, patch.py that
  downloads stock firmware from OM's server, FORMATS.md), `cakelesscoder/caduceus-ep7`.
- Session cannot create GitHub repos. This tree is stored as branch `caduceus-om5` of `xulfr/oly_fw_analysis`
  (orphan branch, superseded): the real repo is now `xulfr/caduceus-om5`.

## Workspace recipe (about 5 minutes, all scripted in session 1)
- Toolchain: binutils 2.42 `--target=mn10300-elf` from archive.ubuntu.com `binutils_2.42.orig.tar.xz`
  (configure flags as in caduceus-om3 `research/setup.sh`), installed to `/home/user/work/toolchain/install/bin`.
- Stock firmware: OM's update server serves all three (request as in caduceus-om3 `firmware/patch.py fetch_stock`,
  hard_code `OLYE148…`, `OLYE144…`, `OLYE147…`). SHA-256: E148 1100 `9de5d77e…d637`, E144 1200 `a0c91f3a…3d11`,
  E147 1100 `8c133084…696d`.
- Emulator: `xulfr/om-emu` branch `fix/e148-ipi-stride` (node 22 works). `OM_EMU_MODEL=E148`.
- Build + record hashes: `tools/dev/build.sh NAME` (paths assume /home/user/work). Emulator session:
  `tools/dev/run.sh BUILD OUT 'keys' [--watch --json --cells=ID:N]` (wraps `tools/dev/sess.mjs`, a copy of
  om5ii_ui_session.mjs with a `PRE=script.mjs` hook; `mount.mjs` sets the card-mounted word, which the emulator
  does not model). Keys to reach Color Profile 1: `s1 ok ok` then 8 x `right`.
- `tools/dev/xm.py ADDR`: finds the E148 counterpart of an E147 (OM-3) code address by instruction shape.
  Needs expanded mains in /home/user/work/dec (`oly_compress.expand_image` of component 0x100).

## State at the end of session 1 (2026-11-14) — READ THIS PART FIRST
Repo: github.com/xulfr/caduceus-om5, branch main (everything is pushed). Owner wants: regular commits + pushes,
no status chatter, just finish the work.

Done and pushed:
- firmware/om5ii: base patch + films.s. Strict build + hash record: `tools/dev/build.sh NAME`.
  Current package `a76c064f…7614` = releases/v0.1.0-alpha1/patch.json (camera_tested false).
- patch.py (user patcher: downloads stock, applies release, pure Python, asks the user to type UNTESTED),
  launchers, tools/mkrelease.py, tools/oly_container.py rewritten (Apache), resource repack pure Python.
- card/mklooks.py, releases/v0.1.0-alpha1/LOOKS.BIN (10 starter films), looklab/films.json (67-film library).
- LookLab: looklab/index.html + app.js (no build step; writes the same bytes as mklooks.py; browser-checked).
- Docs: README, NOTICE, docs/{SAFETY,FIRST_FLASH,INSTALL,USING,FAQ,FORMATS,WHITE_BALANCE}.md, research/OM5II-*.md.
- pages/site/site.css (shared style, has tour classes .hero .steps .step .facts .screen), pages/showcase/img/*.png
  (true-colour emulator screens: film-title, wheel-sat, wheel-hue, tone, film-slot2, mono, color-profile).
  Emulator PNGs are YCbCr in RGB channels: convert with PIL `Image.merge('YCbCr', im.split()).convert('RGB')`.

NOT done yet (next, in order):
1. Site: root `index.html` tour (hero + steps using the screenshots + comparison table + untested banner), and
   `tools/mksite.py` to turn docs/*.md, ROADMAP.md, CHANGELOG.md into pages/{install,using,faq,safety,first-flash,
   formats,roadmap,changelog}/index.html with the shared header/nav (LookLab's header shows the nav links used).
   Add `.nojekyll`. Tell the owner to enable GitHub Pages (main, root).
2. ROADMAP.md, CHANGELOG.md, CLAUDE.md (project rules: status words camera-tested / emulator only; never present
   emulator results as camera results; owner flashes, sessions only prepare files).
3. tests/: LOOKS.BIN writer parity (python vs looklab/app.js via node), patch.py reproduces the release hash,
   emulator film checks from session 1 (see "Emulator results" below).
4. OM-5 (E144): move `patches/ports/om-5-i-from-ii` + `tools/om5i_donor_patch.py`, `om5_donor_resources.py`,
   `om5_transplant_audit.py` from xulfr/oly_fw_analysis (branch fix/om5ii-no-image-stores), rebuild on this build
   with `--donor-patch`, document as second-stage.
5. Firmware gaps: redraw after a film step (title/values only refresh when the highlight moves); Delete on the
   Sharpness/Contrast/Shading/Tone rows also steps the film; film name on the super control panel; re-run the
   "card mounted but no LOOKS.BIN" emulator case. Ask the owner whether candidate `42fcf6de…` was ever flashed.

Workspace is gone after the session: rebuild it with the recipe below (toolchain build ~3 min, firmware download
from OM's server, clone xulfr/om-emu branch fix/e148-ipi-stride, expand mains into /home/user/work/dec).

## Films layer (films.s) — design and emulator status
- FILM 1-3 = the three Color Profile slots. `C:\OM5MOD\LOOKS.BIN`, magic `OM5F`: 32-byte header (u32 total,
  u32 CRC-32 of bytes 12.., u16 version 1, u16 count 1..10) + count x 80 bytes (64-byte record in the OM-3 LOOKS
  record layout: hue[12] +0, light[12] +12 (-7..7), sat[12] +24 (-5..5), +36 WB on, +37 A/B, +38 G/M (-7..7),
  +41 contrast, +42 sharpness (-2..2), +43 shading (-5..5), +44/45/46 shadows/mid/highlights (-7..7);
  then a 16-byte ASCII name, 12 characters used).
- Half-press (HLS_EVENT task, via hsl.s extension vector 0x613f2ffc -> `fl_entry`, section 10 tail 0x6169c820):
  reads and checks the file into heap block P+152. One attempt per power-on; needs MS_A/B/C == 0xf000.
- **Delete (trash) on the Picture Mode screen while a Color Profile is selected = that slot takes the next film.**
  Values are written with the camera's UI writer `0x60855cdc` (saturation, contrast, sharpness, shading, tone,
  WB shift) and `active_write` part 1 (H/L words, name). Name + index live in part-1 cells 916-919 / 924-927 /
  972-975 (slot 1/2/3), so the film stays in the camera with no card. Inside the colour wheel Delete still only
  switches Saturation/Hue/Lightness (detected by the axis changing).
- String getter hook `0x60d52ed5` (ids 2749-2754, 2859-2861) shows the film name instead of "Color Profile n".
- E148 addresses found in session 1: fopen 0x606aa3bd, fclose 0x606aa3c6, fread 0x606aa54e, medium words
  0x61e43b88/90/98, string getter 0x60d52ed5 (lang fn 0x60d52eec).
- Emulator results (build `6590440c…`): 4-film and 10-film files load; slot 1 -> "Portra 400", second press ->
  "Velvia 50"; slot 2 independent; all 12 H/L pairs, tone, contrast and the WB record correct; no store into the
  firmware image from patch code; bad CRC / out-of-range value / no file / no card -> stock behaviour.
- Known gaps: the title and values redraw only after the highlight moves (two refresh attempts failed: forwarding
  0x900c, re-writing setting 111); Delete on the Sharpness/Contrast/Shading/Tone rows also steps the film;
  empty-card run not yet re-checked (grep choked on binary output, re-run); free loaded-tail space left:
  sec3 384, sec4 656, sec5 ~850, sec6 ~550, sec7 ~250, sec9 568, sec10 ~1000 bytes.

## Continuation checkpoint 1 — website (2026-11-14)

Completed the root tour, screenshot captions, comparison table, untested banner, shared guide generator,
keyboard focus styling and `.nojekyll`. `python tools/mksite.py` renders the Markdown guides with local
navigation and heading anchors. Install `requirements-dev.txt` first. ROADMAP and CHANGELOG pages will
be generated at checkpoint 2 when their sources are added. GitHub Pages: enable **Deploy from a branch**,
**main**, **/(root)** in repository Settings → Pages. No firmware workspace was needed for this step.

## Continuation checkpoint 2 — project documentation (2026-11-14)

Added ROADMAP.md, CHANGELOG.md and CLAUDE.md, and generated their guide pages. The rules explicitly
separate emulator-only evidence from camera testing and retain the untested gate. No firmware workspace
has been rebuilt. Next is the format/release/emulator regression suite, then the E144 builder.
