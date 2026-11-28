# Code from the card: OM5MOD/CADUCEUS.BIN (2026-11-27)

**Emulator only (OM-Emu `bdb3347`). Not run on a camera.** This is the first step of route A in
[card code options](OM5II-CARD-CODE-OPTIONS-2026-11-27.md): move UI code that does not decide the photo into a file
on the card, so the flashed tails have room again.

## What moved

The Picture Mode page graphics moved unchanged from hsl.s into `firmware/om5ii/cardblock/gfx.s`:

- the colour wheel (`gfx_wheel`, `gfx_dot`, `gfx_save` / `gfx_restore`, `gtab_sin`);
- the tone curve (`gfx_tone`, `gfx_curve`, `gtab_bump`);
- the Monochrome filter ring (`gfx_filter`, `gf_block`, `ftab_*`).

`gfx_bar` and `gtab_col` stay flashed: `wheel_swatch` (the selected-colour fix) uses them, and the block calls
`gfx_bar`.

- **Freed in the flashed tails:** about 1 KB in ext5 / ext10. The block's body is 1,071 bytes.
- **Without the block:** each stub returns at once. The pages keep their labels, values and controls but show no
  graphic, as builds before alpha8 did.

## The file

`tools/mkcardblock.py` links the block at `0x63700100` against the flashed build's `patch.elf`, then writes the file:

| Offset | Field |
|---|---|
| 0 | magic `CADB` |
| 4 | ABI 1 |
| 8 | body length |
| 12 | CRC-32 of the body (zlib, checked with films.s `fl_crc`) |
| 16 | n checks, at most 29 |
| 20 | n × {4-aligned address, the word the build has there} |
| 256 | body: the entry table first (+0 `gfx_wheel`, +4 `gfx_tone`, +8 `gfx_filter`), then the code |

The checks cover every flashed symbol the block uses that lies in a patched range, plus `cb_find` and `hp_entry`.
Seven checks for this block. They tie the block to one build: after any firmware change the addresses or words differ
and the block is refused. `tools/mkrelease.py` makes the block for each release and records its SHA-256. `patch.py`
copies it next to the update every time, never keeping an old one.

## Loading (`boot.s` `cb_load`)

- **When:** once per power-on, in the background task after `LOOKS.BIN`, or at the first half-press when the
  background did not run or had no card.
- **How:** it reads at most 64 KiB through the firmware's `fopen` / `fread` into `0xa3700000`, the uncached view.
  It refuses the file unless the size, magic, ABI, length, CRC and every check match. Check addresses must be
  4-aligned and inside the main image. Then it publishes the entry table at `0x63700100` (cached view) in P+20.
  P+17 records the state: 0 not tried, 1 loaded, 2 none / refused.
- **Stubs:** `gfx_wheel`, `gfx_tone` and `gfx_filter` in hsl.s each call `cb_find` (d1 = entry offset). That returns
  the entry, or 0 when no block is loaded. The stub then `jmp`s into it with the frame its caller built, or returns.

### Where the block lives

`0xa3456d74..0xa3791000` is the part of resource record 0's slot that the record does not fill. The record is
`0xa3091000..0xa3456d74`; the next records start at `0xa3791000`.

- **OMKit's evidence** (`docs/platform/om5m2/memory.md`, `fw1100/system.md`):
  - No literal in the firmware points into the gap.
  - OM-Emu saw no access to it.
  - On the camera, 3.06 MiB at `0xa3470000..0xa3780000` was pattern-tested 76 times, during a session with shooting,
    with 0 differences.
- **Not covered by that test:** Pro Capture, Live ND, high resolution shot, focus bracketing, Wi-Fi, USB, HDMI and
  sleep.
- **Our patch and record 0:** our resource edit only re-points words inside record 0 (aliases), so the record's
  length cannot change. Our block starts about 2.6 MB past the record's end.
- **Conflict with OMKit:** this is OMKit's arena. Caduceus and OMKit cannot be installed together anyway (section 2 and
  9 tails; see the options note).

### Caches

The file is written only through the uncached view, and this range has run no code in the power-on before it.
It is then executed and read through the cached view on CPU 0 (the GUI task). That is the rule both OMKit (module
images) and the OM-3 (`GUIDES.BIN`; an uncached run rebooted the camera, "lk7") follow. OM-Emu has no cache model, so
this is camera-only.

## Emulator results

- **`tests/run_page_graphics.py`: 11 of 11.** Wheel, edits, colours, hue axis, tints, group hint, tone curve, Shadows,
  with the block on the card (`tests/card_block.py` makes it for the build under test).
- **`tests/run_mono_filter.py`: passed.** 12 dial steps; the ring and header follow.
- **`tests/run_boot_arm.py`:** the block is loaded in the background and at a half-press. A missing block, a block
  whose check word is from another build and a block with a bad CRC are all refused.

## Next candidates for the block

These are UI code only; whatever decides the photo stays flashed. Each move frees flashed room and is tested the same
way:

- the tone page labels (`tone_labels`, `tl_*`);
- the colour editor's text drawing (`tx_draw`, `paint_axis` text);
- the look name handling (`fl_name`, `pg_title`);
- the `LOOKS.BIN` checks (`fl_check`, `fl_crc`).
