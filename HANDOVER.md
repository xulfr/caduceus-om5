# OM-5 Mark II handover

## Baseline

The owner confirmed that the full **v0.1.0-alpha8** update boots on an **OM-5 Mark II (E148, firmware 1.1)**.
The trash button cycles through SD-card looks in the Color Profile carousel, look names appear there and on
the super control panel, HSL and tone controls are available, and Live ND32/64 work. The camera report links
these observations to the exact release and records the limits of the test.

[Camera report](research/OM5II-ALPHA8-CAMERA-2026-11-15.md) · [Alpha8 manifest](releases/v0.1.0-alpha8/patch.json) · [Emulator results](tests/alpha8-results.json)

## Next session — UI defects

1. **Color Profile row icons cluster at the bottom.** Scroll below the carousel through rows such as Tone Curve.
   The owner can reproduce this in OM-Emu.
2. **Super control panel Color Profile icon is missing.** The custom look name appears in the Picture Mode cell.
3. **Colour wheel and tone curve graphics do not render on camera.** The HSL header and colour indicator are
   visible, and the physical dials operate the controls.
4. **Live ND32/64 shooting labels are missing.** The display reads `-LV` instead of `ND32-LV` or `ND64-LV`.

## Build and test

Use stock E148 1.1, GNU `mn10300-elf` binutils and OM-Emu's `fix/e148-ipi-stride` branch.
[Build and test commands](tests/README.md).

Preserve the alpha8 startup layout while working on the UI. The loader submits sections 1–10 in order.
The section-2 tail starts at `0x605af4b0` and contains `st_ptr` and the startup gates. The WB commit
body starts at `0x60829570` in section 4. The first shutter half-press checks all ten initialization
bits before the allocator runs in section 8. The unarmed PC probe rejects patch execution in
sections 3, 4 and 8 or later.

[Previous handover and loader disassembly findings](https://github.com/xulfr/caduceus-om5/blob/1dfd7fdc95c1d3d014c6711ca1bc24e21252aee5/HANDOVER.md)
