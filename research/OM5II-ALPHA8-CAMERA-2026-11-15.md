# Alpha8 camera report

The owner reported a successful boot and working Color Profile controls on a physical OM-5 Mark II
(E148, stock firmware 1.1) on 15 November 2026. The report covers the full Caduceus
`v0.1.0-alpha8` build from `1dfd7fd`. The supplied update's SHA-256 is
`709ca9d4e3a4a050a3586a57109ae892da8a142c6b1d85bec58bda22a68f3b68`.
The owner booted the camera and exercised the Color Profile carousel with looks on an SD card,
the HSL and tone controls, the super control panel, and Live ND in shooting mode.

## Confirmed on the camera

- The camera boots. The trash button on the Color Profile carousel cycles through preset looks from the SD card.
- HSL and tone controls are available in Color Profiles. The HSL header and colour indicator show, and turning
  the physical dials changes the controls.
- The selected custom look's name appears in the carousel and on the super control panel.
- Live ND32 and ND64 can be selected and work.

## UI defects to investigate

| Defect | Observed behaviour |
|---|---|
| Color Profile row icons cluster at the bottom | Scrolling down to rows such as Tone Curve exposes icons bunched together at the bottom. The owner has also reproduced this in OM-Emu. |
| Super control panel icon missing | The Color Profile icon is missing from the Picture Mode cell. The custom look name is visible. |
| Colour wheel and tone curve missing | Neither graphic renders on camera. The HSL header and colour indicator render, and the physical dials still operate the controls. |
| Live ND label missing | Selecting ND32 or ND64 leaves only `-LV` on the shooting screen. The expected labels are `ND32-LV` and `ND64-LV`. |

The report establishes boot and the functions above on one camera. Repeated boots with a saved profile,
persistence across card swaps or power cycles, and the effect of HSL and tone changes on JPEG output
remain unverified by this report.
