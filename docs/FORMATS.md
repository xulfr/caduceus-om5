# File formats

## `C:\OM5MOD\LOOKS.BIN` (OM5F, version 1)

Little-endian. 32 + 80 × n bytes, n = 1..10 (at most 832 bytes).

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | magic `OM5F` |
| 4 | 4 | total length |
| 8 | 4 | CRC-32 (zlib) of bytes 12..end |
| 12 | 2 | version 1 |
| 14 | 2 | look count n |
| 16 | 16 | zero |
| 32 | 80 × n | looks: a 64-byte record, then a 16-byte name |

Record (signed bytes; the offsets are those of the OM-3 project's `LOOKS.BIN` record):

| Offset | Field | Range |
|---|---|---|
| 0 | Hue, 12 colours | −7..7 |
| 12 | Lightness, 12 colours | −7..7 |
| 24 | Saturation, 12 colours | −5..5 |
| 36 | WB shift on (0: the camera sets the shift to 0) | 0 / 1 |
| 37, 38 | WB A/B, G/M | −7..7 |
| 41 | Contrast | −2..2 |
| 42 | Sharpness | −2..2 |
| 43 | Shading | −5..5 |
| 44, 45, 46 | Shadows, Midtones, Highlights | −7..7 |

Colours run clockwise from Yellow, as on the camera's wheel: Yellow, Orange, Orange-red, Red, Magenta, Violet,
Blue, Blue-cyan, Cyan, Green-cyan, Green, Yellow-green. Bytes 39, 40 and 47..63 are not read (write zero).
Name: 1–12 printable ASCII characters, zero-padded. `@` is not allowed: the camera treats it as a display
command. The camera checks the first 12 name bytes and rejects an empty name, `@`, control characters and
non-ASCII bytes. Older saved names containing these bytes display `?` in their place; stored settings are
not rewritten. LookLab and the Python writer also reject leading and trailing spaces.

The camera checks the length, magic, version, count, CRC and every byte in the table against its range; a file
that fails is ignored as a whole. Writers: `card/mklooks.py`, LookLab (`looklab/app.js`), byte-identical.

## Where a look lives in the camera

A look is written to the slot's own settings (profile p = 0..2): Saturation 928 + 12p + colour, Hue / Lightness in
part 1 of the same cells (`0x4831` tag, hsl.s), Contrast 908 + p, Sharpness 904 + p, Shading 912 + p, Highlights /
Midtones / Shadows 976 + 3p .. 978 + 3p, the WB shift in the current WB mode's shift settings (wb.s then keeps the
profile's WB record). Its name and number are in part 1 of four otherwise unused cells: 916–919 (slot 1), 924–927
(slot 2), 972–975 (slot 3): word 0 = `0x464C` << 16 | number << 8, words 1–3 = 12 name bytes.
