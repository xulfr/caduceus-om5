# OM-5 Mark II handover

## Baseline

The owner confirmed that the full **v0.1.0-alpha8** update boots on an **OM-5 Mark II (E148, firmware 1.1)**.
The trash button cycles through SD-card looks in the Color Profile carousel, look names appear there and on
the super control panel, HSL and tone controls are available, and Live ND32/64 work. The camera report links
these observations to the exact release and records the limits of the test.

[Camera report](research/OM5II-ALPHA8-CAMERA-2026-11-15.md) · [Alpha8 manifest](releases/v0.1.0-alpha8/patch.json) · [Emulator results](tests/alpha8-results.json)

## UI candidate

The strict source build at `ae96e94` produces package SHA-256
`7ba9aba03cefb22969b9abde3cd387cd1d3390dc263b4117cbe52c509fb92508`.
It has been exercised in OM-Emu. Alpha8 is the camera-tested release.

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
