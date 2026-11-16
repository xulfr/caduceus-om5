# v0.1.0-alpha12

For the OM-5 Mark II (E148) on stock firmware 1.1.

Package SHA-256 `cddd7a1f1320e7680bec9e8430e25c69857c2f4bf764e571d6bfffb775acd3fa`.

## Owner’s camera findings

On 16 November 2026 the owner reported completing the alpha12 camera checks and
said all defects from the last round were fixed. In that round the remaining
issue was the missing graphic on the Monochrome Color Filter page. The owner
had already confirmed that alpha11 resolved the filter-page restart and
restored the ND32 and ND64 CP carousel icons.

The hash above is the release manifest’s expected package hash. The owner’s
follow-up identified alpha12 and gave an overall result. It did not include an
installer hash readout or a step-by-step record of the checks. The installer
therefore retains its experimental-build acknowledgement.

## What changed

Alpha12 draws the filter swatches, selected outline and centre colour over the
stock filter page. It retains the stock labels and layout and the alpha11 CP
carousel artwork. The out-of-range image lookup remains the leading hypothesis
for alpha10’s restart.

[Alpha11 report](../../research/OM5II-ALPHA11-CAMERA-2026-11-16.md) ·
[Camera checklist](../../docs/FIRST_FLASH.md#alpha12-camera-checks) ·
[Automated results](../../tests/alpha12-results.json) ·
[Safety](../../docs/SAFETY.md)
