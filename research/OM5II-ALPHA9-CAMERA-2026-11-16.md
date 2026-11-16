# Alpha9 camera report

The owner reported a successful boot of `v0.1.0-alpha9` on a physical OM-5 Mark II (E148, stock firmware 1.1) on
16 November 2026, relayed in the development session. Release package SHA-256:
`2e9777ce08163fa6e4a97930683cd8eb0ce73197dfd5ac4a64d8928af98fbc50` (releases/v0.1.0-alpha9). The report did not
quote the hash of the flashed file; it is recorded here as the alpha9 release package, which `patch.py` checks
before writing. Confirm the hash before changing the release's `camera_status`.

## Confirmed on the camera

- The camera boots.
- The colour wheel drawn by the patch (CPU-rendered blocks) works "perfectly".
- Shading works in Monochrome Profiles. Film grain works in Monochrome Profiles (grain is visible in pictures).
- ND32 and ND64 appear in Gear menu › CP Button Settings.
- "Everything else is working as intended", apart from the defects below.

## Defects

| Defect | Observed behaviour |
|---|---|
| Shading row in Color Profiles | The selection bar shows a grey circle instead of a green one. Moving it makes the circle disappear and the value does not go up or down as expected. |
| Monochrome Color Filter | No colour wheel / filter graphic and no sidebar icon. Known placeholder `0x38cb` since alpha8. |
| Monochrome Film Grain | No icon in the sidebar or the grain carousel; the setting works. Known placeholders `0x38e7..0x38ee`. |
| ND32 / ND64 from the CP button | Holding CP and turning the dial does not offer ND32 or ND64 even when they are ticked in CP Button Settings. |

## Requests

- Colour grain in Color Profiles: not on the roadmap; add if simple, otherwise defer with the other effects.
