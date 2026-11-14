# Project rules

Read HANDOVER.md first, including the latest continuation checkpoints. Work in `xulfr/caduceus-om5`
on `main`. The maintainer is **xulfr**. Commit and push each finished piece and update HANDOVER.md
with its commands, results, remaining gaps and workspace requirements.

## Evidence and safety

- **Emulator only** means observed in OM-Emu. It never means **camera-tested**.
- Use **camera-tested** only for an explicitly recorded physical-camera result, with model, stock
  version, exact package SHA-256, procedure and outcome. Do not infer it from a successful build.
- No successful camera run is recorded for the current release. Keep `camera_tested: false`,
  patch.py's `UNTESTED` acknowledgement and visible site warnings.
- The owner flashes. Sessions prepare files, inspect code and run tools/emulation only; never
  initiate a camera update or suggest that emulator success establishes a safe install.
- Record negative results. Never suppress a failing audit or rewrite expected hashes to conceal
  an unexplained change. Re-record hashes only for an intentional, reviewed source change.
- Do not distribute OM stock firmware, decoded images, or full patched camera images. Releases
  contain project-authored edits and verified hashes.

## Scope and sequence

OM-5 Mark II (E148, 1.1) first; original OM-5 (E144, 1.2) second. Priorities are films from one
LOOKS.BIN, full HSL, ND64 and tone controls. Additional effects are optional.
Do not re-explore the old repositories. Fetch a specific legacy file only when the handover calls
for it. Rebuild the toolchain, stock workspace and emulator only when a step needs them.

The original OM-5 build is a **pre-alpha for testers** (owner decision, 2026-11-14): built by the tester with
the developer builder, offered only on its tester page with its warnings and the step-0 restore check. Keep it out
of patch.py and the launchers, keep `camera_tested` false, and do not call it compatible or recommend installing
it until camera reports exist.

Keep settings in the existing declared part-1 cells and transient state in allocated RAM. Never
write patch state into firmware-image addresses. Check section bounds, hook preimages, compression,
container checksums and the strict builder's recorded hashes.

## Repository workflow

- Site sources: root index.html, docs/*.md, ROADMAP.md, CHANGELOG.md. After documentation changes:
  `python -m pip install -r requirements-dev.txt` then `python tools/mksite.py`.
- Keep generated guide pages checked in. GitHub Pages uses `main`, `/(root)`, with `.nojekyll`.
- Preserve Apache-2.0 attribution and NOTICE. No unlicensed container-code imports.
- Use targeted automated checks for binary formats, patch integrity and emulator flows. Record
  precisely which checks ran, which require external firmware and which remain unverified.
- HANDOVER.md is the continuity record; historical sections describe their own checkpoint, and
  the latest checkpoint takes precedence for the current state.
