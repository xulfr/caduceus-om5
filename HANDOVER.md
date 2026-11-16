# OM-5 Mark II handover

## Baseline

The owner confirmed that the full **v0.1.0-alpha8** update boots on an **OM-5 Mark II (E148, firmware 1.1)**.
The trash button cycles through SD-card looks in the Color Profile carousel, look names appear there and on
the super control panel, HSL and tone controls are available, and Live ND32/64 work. The camera report links
these observations to the exact release and records the limits of the test.

[Camera report](research/OM5II-ALPHA8-CAMERA-2026-11-15.md) · [Alpha8 manifest](releases/v0.1.0-alpha8/patch.json) · [Emulator results](tests/alpha8-results.json)

## WIP UI candidate 2 (16 November 2026)

Branch `claude/pensive-hamilton-pg8dpr`, built from the UI candidate `ae96e94` (package `7ba9aba0…b92508`,
reproduced byte for byte in this session). **Emulator only; not camera-tested.** Not a release: no tag, no
manifest under `releases/`, `camera_tested` stays false.

Strict source build package SHA-256: `32a0c5f124a4f80cdab8489d075828d7e15309f59d5d0e451174aa6908a0a5bd`
(90,832,896 bytes, `DCOLYMP/E1489999.BIN`). [Findings](research/OM5II-WIP-UI2-2026-11-16.md).

| Defect | Status | Change |
| --- | --- | --- |
| HSL title stuck after trash | Fixed in OM-Emu by invalidation count; camera check needed | Axis switch marks `P+56`; `pages_hook` invalidates the colour page with OM's `0x60d49294`. Baseline made no dirty mark; OM-Emu repaints the whole plane, so frames could not show it. |
| Screen times out during custom controls | Fixed in OM-Emu | Axis switch, film step and INFO on the custom pages restart timer 500 (8000 ms) exactly as the stock container does. Idle still closes. |
| Tone Curve sidebar icon | Fixed in OM-Emu | Image `0x38cc` aliased to stock tone-curve glyph `0x2aef` (28 × 28). |
| ND32/ND64 in CP Button Settings | Menu and toggles fixed in OM-Emu; carousel unverified | Page `0x16f` lists 2217/2218; their descriptors are linked into OM's RAM hash after arming. |
| Colour wheel / tone curve graphics | Unresolved | No new trace; next step unchanged (OM-3 draw requests). |
| ND64 digit artefact | Cause identified, not changed | Digits narrowed to 13 px by column sampling in sprite `0x205d`. |

Commits: `3209740` repaint and timeout, `7424c74` Tone Curve icon, `04903de` CP Button Settings, then the
records commit with this handover. New sources: `firmware/om5ii/cp_nd.py`, `tools/oly_resource_recipe.py`,
`tests/run_ui_activity.py`, `tests/ui_activity.mjs`. `tools/dev/sess.mjs` accepts `main+N` / `sub-N` dial input.

State and image rules: new state is `P+56` (axis repaint) and `P+988..1003` (two hash nodes); the descriptor
hash is OM's own RAM (`.bss`). No startup gate, section order, allocator or loader byte changed. Section tails
left: ext6 345, ext7 92, ext10 602 bytes. All three section-2 data edits sit in the region color_profiles.py
already frees.

### Checks run on this candidate (`generated/w3`)

- Strict build and package hash above; `tests/audit_build.py` against `ae96e94`: all edits declared, loader
  bounds and 768 ND selector cases unchanged, resource delta exactly image `0x38cc`.
- `tools/dev/static_rules.py`: no `0xfb`, 14 tables aligned, stream lengths safe.
- Startup probe: 1023 masks, task gates, allocation retry, bounds, alignment and magic passed; startup image
  stores equal stock (6/6, none beyond).
- Gating: inert and applied passed; stale profile number passed; unarmed PC scan passed (now ignores
  assembler `.L*` labels and allows the INFO gate `container_info`).
- `tests/run_emulator.py`: 19 look/menu cases, see `tests/wip-ui2-results.json`.
- `tests/run_ui_activity.py`: 10/10 (8 controls stay open, idle closes, axis 1→2→0 with 3 restarts and 3
  invalidations; the axis case fails on `ae96e94` with 0/0).
- Six Live ND label cases passed. Host suite with `OM5_STOCK`: 18 tests OK, 1 skipped (E144 inputs).
- Not run: anything needing a camera, the CP-button carousel (button not wired in OM-Emu), C3D graphics.

### Camera retest checklist (owner)

Record model, stock 1.1, the package SHA-256 above, procedure and outcome for each.

1. Boot and the step-0 restore check; half-press once before the tests below.
2. Picture Mode carousel: Color Profile 1–3 and Monochrome 1–3 icons (1/2/3, M1/M2/M3) unchanged.
3. SCP Picture Mode cell icon and look name; after cycling looks and after moving the SCP highlight.
4. Sidebar: scroll down to Contrast and back; no overlap. Tone Curve row now shows a curve icon, selected and
   unselected, aligned with the other icons.
5. Colour wheel row: press trash repeatedly, slowly and quickly. The title must go Saturation → Hue →
   Lightness → Saturation, changing on every press with no navigation. Turn the dials after each switch.
6. Keep using controls for over 10 s each: trash look cycling on the mode strip, trash and INFO on the wheel,
   dials and INFO on Tone Curve. The screen must stay open. Then leave it idle: it must close (about 8 s).
7. Colour wheel and tone curve graphics: note whether either now draws (not expected from this candidate),
   including after leaving and re-entering the editor.
8. Gear menu → CP Button Settings: ND32 and ND64 listed after ND16; untick and re-tick each; ND2–ND16 and the
   rest unaffected; settings kept after a power cycle.
9. Hold the CP button: ND32/ND64 appear when ticked and are absent when unticked; selecting each gives ND32 /
   ND64 exposure and the `ND32-LV` / `ND64-LV` label.
10. Live ND menu: ND2–ND64 still selectable; labels and exposure as before. Note the ND64 digit artefact.
11. HSL edits, tone edits and JPEG output for a look as in alpha8.

## UI candidate (`ae96e94`)

The strict source build at `ae96e94` produces package SHA-256
`7ba9aba03cefb22969b9abde3cd387cd1d3390dc263b4117cbe52c509fb92508`.
It has been exercised in OM-Emu. Owner camera report (relayed 16 November 2026, OM-5 Mark II, stock 1.1, this
package): M1–M3 and Color 1–3 icons, the SCP Picture Mode icon, the sidebar overlap (including scrolling) and
the `ND32-LV` label are fixed; `ND64-LV` shows with a small artefact on the digits. New on camera: the HSL title
lags behind trash presses, custom controls let the screen time out, the Tone Curve row has no icon and
CP Button Settings lacks ND32/ND64. Alpha8 remains the released, camera-tested build.

| Defect | Alpha8 in OM-Emu | Candidate and camera retest |
| --- | --- | --- |
| Sidebar icons overlap | Reproduced on the carousel and while scrolling through Tone Curve. | `758f237` aligns stock widgets with the 60 px sidebar rows. Scroll down through Contrast and back, checking the selection and icons. |
| Picture Mode icon missing from the SCP | Reproduced with and without an SD look. | `acf42f1` supplies the SCP's own image slots, including its separate IDs for edited profiles. All three custom Color Profile names and corresponding icons appeared together in the SCP. Check after cycling looks and after changing the highlighted SCP cell. |
| Colour wheel and tone curve graphics missing | Labels and controls run. The C3D/OpenVG layer is absent from OM-Emu, including on models that use it in stock firmware. | Open. See the trace below. Check both graphics on camera after the next change, including redraw when turning the dials and after leaving and re-entering the editor. |
| ND32 and ND64 show only `-LV` | Reproduced by supplying the display-side ND settings. Stock ND16 provided a control. | `ae96e94` fills the two empty shooting-screen bitmap entries. ND16/32/64 drew the corresponding prefix with LV off and with the native suffix when LV was on. Confirm both levels, suffix behavior and exposure on camera. |
| Color Profiles 1–3 all show C2 | Reproduced. The carousel selects different IDs, and alpha8 aliases all three to the same stock picture. | The carousel, selected sidebar row, SCP and shooting overlay show the stock numbered Color artwork for the active slot. Check all three on camera. |
| Monochrome Profiles 1–3 all show M | Reproduced. The carousel selects different IDs, and alpha8 aliases all three to the same unnumbered picture. | The same screens show M1, M2 and M3. Check all three on camera and make one edit to exercise the SCP's edited-profile IDs. |

The carousel chooses image triples at `0x611b4970`, `0x611b4edc` and `0x611b7950`. The shooting overlay
table is at `0x6121586c`. SCP child 206 uses the image table at `0x61073540` and selects the row in
`0x60dcf6a9`. Color Profiles use `0x3d8a–0x3d8c` and `0x3d8e–0x3d90`. Monochrome uses
`0x3d82–0x3d84` and `0x3d86–0x3d88`. The candidate assembles the numbered artwork from E148 stock
bitmaps. It appends the artwork to resource record 37 and redirects 42 declared pointer words in record 0.
The stock bitmap bytes and the language and font records compare byte for byte. The new image record
lengths pass the compressed-stream checks. Camera boot and native resource loading still need verification.

For Live ND, `0x60eb627d` maps the setting to the shooting overlay index. The ND32 and ND64 rows at
`0x610eab18` and `0x610eab28` pointed to placeholder ID 1. The `-LV` suffix draws separately.
[Focused ND fixture](tests/README.md#live-nd-shooting-labels).

### Continue with the graphics

Alpha8 shows Color Profile children 4 and 2 through `pages_hook` at `0x60dad5f5`. This reaches the
CPU-drawn content on both pages. In an E148 focus trace through the wheel and tone rows, the
only `0x60f1175d` calls were the controller's `0xfffd` requests at `0x60dad4d3`.
The neighboring stock Color Creator and tone paths populate draw requests in blocks 278 and 279,
consumed at `0x60df1605` and `0x60dfaf61`. The restored profile pages have separate data and view
handlers. Trace the stock OM-3 editor with its creative dial in COLOR to establish the matching
profile draw commands and their arguments, then compare the E148 producer and the plane placement.
The observed trace does not establish which GPU commands or coordinates the physical E148 needs.

## Build and test

Use stock E148 1.1, GNU `mn10300-elf` binutils and OM-Emu's `fix/e148-ipi-stride` branch.
[Build and test commands](tests/README.md).

Preserve the alpha8 startup layout while working on the UI. The loader submits sections 1–10 in order.
The section-2 tail starts at `0x605af4b0` and contains `st_ptr` and the startup gates. The WB commit
body starts at `0x60829570` in section 4. The first shutter half-press checks all ten initialization
bits before the allocator runs in section 8. The unarmed PC probe rejects patch execution in
sections 3, 4 and 8 or later.

All 31 assembled sections in the UI candidate compare byte for byte with alpha8. The startup
probes passed the 1023 incomplete masks, task and handle checks, allocation retry and bounds,
unarmed PC scan, inert/applied refresh, and stale profile-number repair. Startup image stores
matched stock. The static stream and alignment rules passed. The 768 ND selector results match
the candidate's selector bytes.

All 19 look and menu regression cases passed on the strict candidate with zero extra image
stores. The six focused Live ND display cases also passed. The Windows host suite passed
with its two stock-image checks skipped, and the E148 release reproduction passed separately
with the stock image in WSL. Emulator checkout `bdb33470705b3be28db52cbe080c31d74db727d8`.
Local logs and screenshots are under `generated/ui-verified-regress`, `generated/ui-verified-startup`,
`generated/ui-verified-label-*` and `generated/ui-profile-named-fixed`.

[Previous handover and loader disassembly findings](https://github.com/xulfr/caduceus-om5/blob/1dfd7fdc95c1d3d014c6711ca1bc24e21252aee5/HANDOVER.md)
