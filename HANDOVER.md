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

## Continuation checkpoint 3 — regression tests (2026-11-14)

Nine unit/integration tests pass with OM5_STOCK set, including byte-for-byte release reproduction.
Nine emulator cases pass: four/ten films, next/wrap, independent slots, CRC/range rejection, mounted empty
card and no card. Assertions check all H/L pairs, saturation, tone, name cells/string getter and WB record.
Results: tests/alpha1-results.json. The mounted-empty-card gap is now closed in emulation.

Stock initialization writes from PC 0x60d52ed0 to six image addresses also occur with unmodified stock.
Each test compares a matching stock session and rejects additional PC/address pairs or increased counts.
The exercised patch adds no image stores; this is not physical-loader evidence.

The original release LOOKS.BIN had been ignored by Git; it is now included and checked against both writers.
Aligned validation and rejected malformed imported records. Added a source CI template and site-link tests. GitHub rejected active workflow creation because the
existing OAuth credential lacks workflow scope; tests/github-actions.yml is ready to install manually. Visually
checked tour and install guide in a browser. Updated the WB document's stale state/loaded-bit references.

Workspace (local generated/, ignored): stock/ contains hash-verified official E148; alpha1-strict/ contains
the matching source build; om-emu/ is bdb33470705b3be28db52cbe080c31d74db727d8; tests-alpha1-matched/
has logs/screens. Existing WSL GNU MN103 binutils 2.43 reproduced the 2.42 reference exactly, so no new
toolchain was needed. Native Node 26.13.0 runs the emulator. tools/dev/build.sh and run.sh now use supplied
paths and preserve errors/output; builds no longer delete directories or silently re-record hashes.
Next: import only the E144 files named in the session-1 list, rebuild with this donor, then firmware UX gaps.

## Continuation checkpoint 4 — original OM-5 builder (2026-11-14)

Imported exactly patches/ports/om-5-i-from-ii/{README.md,build.py} and tools/{om5i_donor_patch.py,
om5_donor_resources.py,om5_transplant_audit.py} from the named legacy branch. Updated the default donor
to firmware/om5ii and rebuilt with --donor-patch firmware/om5ii. No old repository checkout was explored.

E144 candidate: 92,274,688 bytes, SHA-256
8e47087017812786b1f87036da8c8b79ba69cc34e4abcbcf894f8e28ce78b12b.
Donor: alpha1 a76c064f6f797f2b91719f27fb3f7d0132a12e06cf143627a4b083b540187614.
The build preserves all donor feature ranges (films included), E144 headers/slots/controller, all 557
common-resource leaves and all 116 picture IDs. JPEGs compare pixel-identically after lossless optimization.
Independent tests reconstruct the complete package and verify the recorded hash and exact stock restore.
Three E144 tests pass; compact evidence is tests/e144-results.json. No install file was written.

Local generated/e144-alpha1/ has decoded outputs, restore and build report. WSL dependencies added:
libjpeg-turbo-progs 2.1.5 and python3-pil. E144 official stock is hash-verified in generated/stock/.
This remains developer-only: no successful E144 boot or hardware compatibility is established.
Next: film redraw, row-specific Delete behaviour and SCP naming. Empty-card regression already passes.

## Continuation checkpoint 5 — firmware gaps closed, v0.1.0-alpha2 (2026-11-14)

**Owner statement (2026-11-14): the 12 November candidate (`42fcf6de…`) was NOT flashed to the camera.** So the
record stands at three boot loops (4, 5, 8 Nov) and no build after them tried on a camera. Nothing in this
repository is camera-tested.

Done (all emulator only, package `2eac7af1d82b119acba3952e8dac1dd6b8faec3cbaf1fcbfa9fcced600167ca9`,
releases/v0.1.0-alpha2/patch.json, camera_tested false; alpha1 kept and still reproduced by the tests):
- **Redraw after a film step.** `fl_delete` now ends with the screen's own panel update (`(0x61e588f4)` → `+4` →
  vtable entry 0 = 0x60e49c2b) and sets P+67 (`FL_DIRTY`). `pg_title` (films.s, section 6, first call in hsl.s
  `pages_hook`) consumes the flag and sets the title label's stored string id (child 15, +130) to 0xffff so the
  layout that follows repaints the title. Why each earlier idea failed is in
  research/OM5II-PICTURE-MODE-SCREEN.md (read it before touching this screen again).
- **Rows.** A film steps only when the panel's record of the highlighted row (updater + 136) reads 4, the
  Picture Mode strip. Tone / Shading / Sharpness / Contrast rows: Delete does nothing. Wheel: axis switch as before.
- **Super control panel.** No code needed: its top line uses the string getter, so it shows the film's name
  while the Picture Mode cell is highlighted. Now a regression case.
- **Empty card** case was already closed at checkpoint 3 and passes again.
- tests/run_emulator.py: 13 cases pass (new: other-rows, row-return, title-redraw, scp-name), each against a
  stock baseline for image stores; tests/alpha2-results.json. Unit tests: 12 pass with OM5_STOCK and the E144
  paths set. Strict build and both releases reproduce byte for byte.
- E144 developer candidate rebuilt on this donor: 92,274,688 bytes, SHA-256
  `70788992f032dad53bfa4e145b2147e376d3f25a62e2b1ce2929973fec26d1b4`; tests/e144-results.json; three E144
  tests pass. Still developer-only, no install file, no hardware compatibility established.
- New developer tools: `T+` / `T-` tokens in tools/dev/sess.mjs, tools/dev/calls.mjs (call log),
  tools/dev/trace.mjs (registers at chosen addresses), tools/dev/calltree.py (tree / chain / events views).
- Docs, tour, ROADMAP, CHANGELOG and generated pages say what changed and keep the untested warnings.
- The name was checked across files, images and commit metadata: only "xulfr" appears.

Workspace used here (gone after the session; about 10 minutes to rebuild):
- `/home/user/work/toolchain/install/bin`: binutils 2.42, `configure --target=mn10300-elf --disable-nls
  --disable-werror --disable-gdb --disable-sim --disable-gprof --disable-gprofng`, `make MAKEINFO=true`.
- Stock files through `patch.fetch_stock` (E148 as the release says; E144 with model_code `E144`, file
  `OLY_E_144_1200_0000_0000.BIN`); both hashes matched the pinned values.
- `xulfr/om-emu` branch fix/e148-ipi-stride at bdb3347; Node 22.23.4 ran it. `apt-get update` first, then
  `libjpeg-turbo-progs` (2.1.5, same as checkpoint 4) for the E144 build; `pip install Markdown==3.7 pillow`.
- Dev loop: copy firmware/om5ii to a scratch directory and run tools/oly_patch_record.py there (it rewrites
  patch.json), run sessions on `WORK/strict/decoded`; only record into the repository when the change is final
  (`tools/dev/build.sh DIR --record`, then a strict `tools/dev/build.sh DIR2`, then tools/mkrelease.py).
- A full tests/run_emulator.py run takes about 45 minutes here (two sessions per case).

Calling convention trap that cost time: `call` and `calls` store the return address at the CALLER's `(0,sp)`.
A function that makes calls needs its frame to start with a free word: `call f,[a2],8` (4 for a2 + 4), never
`[a2],4`, or the nested call overwrites the saved register.

Open (none blocks a first camera test; the test itself is the owner's decision, plan in docs/FIRST_FLASH.md):
- After going down the rows and back up, the stock title reads "Picture Mode" (string 203), also after a film
  step there. The name returns when the mode changes. Updater + 140 holds that id if someone wants to change it.
- In the emulator the super control panel's Picture Mode cell draws no icon for a Color Profile (base patch
  resource question, not looked at).
- tests/github-actions.yml still needs installing by a credential with workflow scope.
- Free loaded-tail space now: section 6 about 490 bytes, section 10 about 900; others as at session 1.
- Everything under "Physical validation remains open" in ROADMAP.md.

## Continuation checkpoint 6 — original OM-5 candidate, emulator and static (2026-11-14)

Owner asked to take the E144 candidate as far as possible without hardware. Result:
research/OM5I-TRANSPLANT-EMULATOR-AND-STATIC-2026-11-14.md, numbers in tests/e144-emulator-static.json.

- OM-Emu `OM_EMU_MODEL=E144` boots stock OM-5 1.2 but refuses the candidate (PlayError at 0x501104e2): its
  handlers are bound to OM-5 code. Not a camera result.
- `OM_EMU_MODEL=E148` with the candidate's decoded 0100/0101 (`tools/dev/sess.mjs` takes any main/resource pair):
  13/13 film regressions pass (`python3 tests/run_emulator.py --build E144_BUILD_DIR ...`, E148 stock as the
  image-store baseline), and a 23-step tour is frame-identical to alpha2. OM-Emu does not read resources through
  the relocated flash addresses (watch: zero reads), so that edit stays unverified.
- Static: `node tools/dev/xbuild.mjs OM_EMU_DIR E144_main.bin E148_main.bin OUT.json` and
  `python3 tools/dev/sram_compare.py E144_main.bin E148_main.bin` (expanded stock mains). 100 differing constants:
  7 resource bounds already relocated by the builder, 91 renumbered identifiers kept at Mark II values, 2 SRAM.
  SRAM 0x8ff00000: one 0x40 shift (OM-5 0x450/0x490 = Mark II 0x410/0x450).
- Controller 010e: 55.9 % equal bytes; the candidate keeps OM-5's. Biggest unknown.
- Next steps, all optional and none a substitute for a camera: trace whether any renumbered identifier crosses to
  the controller; find readers of SRAM 0x8ff00410..0x8ff004a0 outside the main program; an OM-Emu E144 model that
  runs Mark II code. The candidate remains developer-only; do not offer an install.

Workspace: as checkpoint 5, plus the E144 stock (patch.fetch_stock with model_code E144, pinned hash matched) and
the candidate built with `patches/ports/om-5-i-from-ii/build.py --donor-patch firmware/om5ii`.

## Continuation checkpoint 7 — original OM-5 pre-alpha for testers (2026-11-14)

Owner decision: offer the E144 candidate as a **pre-alpha for testers** on the site, built by the tester with the
existing developer builder (not added to patch.py or the launchers). CLAUDE.md's rule was reworded accordingly.

- docs/OM5_PREALPHA.md → pages/om5-prealpha/ (own red banner via mksite.py `BANNERS`), linked from the tour, README,
  FAQ, ROADMAP and CHANGELOG ("OM-5 pre-alpha 1", package `70788992…d1b4`).
- Test order on the page: step 0 flashes OM's own 1.2 (the builder's restore-stock file) to prove the card update
  works on that camera before anything risky; then start, basics, Caduceus, films, hardware checks; stop and go
  back at the first fault; report with .github/ISSUE_TEMPLATE/camera-test.md.
- tools/fetch_stock.py E144 E148: downloads and checks both OM files (uses patch.fetch_stock).
- The page's build commands were run as written (binutils 2.42 mn10300-elf, jpegtran 2.1.5, `--write-untested-package`):
  install `70788992f032dad53bfa4e145b2147e376d3f25a62e2b1ce2929973fec26d1b4`, restore equals OM's E144 1.2.
- Unknown and stated on the page: whether a failed OM-5 can be restored from the card; whether another jpegtran
  version reproduces the checksum (the page says to stop and report if not).
- If a tester reports, record it in a new checkpoint and research note with model, firmware, exact checksum,
  steps and outcome. Only a recorded camera result may change any "untested" wording.

## Continuation checkpoint 8 — OM-5 Mark II audit and alpha3 (2026-11-15)

- Rebuilt alpha2 to `2eac7af1…67ca9`. Reproduced a pre-arm Delete trap with the section-10
  extension absent, acceptance of a ten-look file with trailing data and a second Windows
  launcher invocation after a refusal. See [audit and reproduction details](research/OM5II-ALPHA3-AUDIT-2026-11-15.md).
- Alpha3 package (90,832,896 bytes) SHA-256
  `f56a13335e1085e73f79db66e58440839022349a72746e1dcb5b32e2bc08e242`.
  The installer selects `releases/v0.1.0-alpha3` by default. It reproduced the package and
  the exact stock restore using the pinned E148 1.1 file.
- Build commands from the repository root, with `OM5_STOCK` set to the pinned E148 file
  and WSL binutils 2.43 on PATH:

  ```sh
  bash tools/dev/build.sh generated/alpha3-record --record
  python3 tools/mkrelease.py v0.1.0-alpha3 generated/alpha3-record/strict "$OM5_STOCK"
  ```

  The record step ends with a strict build. The release reuses the starter bank from alpha2.
  Format, release and site tests run with `python -m unittest discover -s tests -v`.
- OM-Emu at `bdb3347` and Node 26.13.0 ran all 15 cases, including the new cases.
  Results are in `tests/alpha3-results.json`. The Windows workspace has raw logs and screenshots
  under `generated/alpha3-regressions-1` through `generated/alpha3-regressions-5`, verified
  installer output in `generated/alpha3-installer-verification` and official inputs in `generated/stock`.
- Built the original OM-5 pre-alpha 1 from the source revision now pinned in its guide.
  The package reproduced `70788992…d1b4` with the alpha2 donor.
- The generic title after returning from a lower row and missing super control panel icon in
  OM-Emu remain open. No physical camera result exists for alpha3. The readiness test exercises
  the branch with missing code in OM-Emu. Physical boot, recovery and capture remain unverified.
