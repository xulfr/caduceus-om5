# Alpha10 camera report

The owner flashed the v0.1.0-alpha10 release on an OM-5 Mark II (E148, stock firmware 1.1).
Package SHA-256:
`056aefb3c3f40b7cf41728cd9f466ba161a52d887db6ecebd2f0377bb0a38454`
([release package specification](../releases/v0.1.0-alpha10/patch.json)).

## Confirmed on the camera

- The camera boots.
- The owner reported the rest of the [first-flash checklist](../docs/FIRST_FLASH.md)
  as expected, apart from the two defects below.

## Defects

| Defect | Observed behaviour |
|---|---|
| D1. ND32 / ND64 in the CP carousel | Hold the CP button and turn the dial. ND32 and ND64 have no icons. Both can be selected and work. |
| D2. Monochrome Color Filter page | Select a Monochrome Profile and move down to the Color Filter row. The screen flashes black, the profile reappears briefly, then the camera restarts. It does not enter a boot loop. The next power-off “turns off a bit weirdly”, then it boots normally. |

Use the camera-checked alpha9 baseline until the fix is checked on the camera:

```sh
python3 patch.py --release v0.1.0-alpha9
```
