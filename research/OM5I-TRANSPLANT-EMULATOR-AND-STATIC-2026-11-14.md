# Original OM-5 (E144) candidate: how far it gets without a camera (2026-11-14)

Candidate: the E144 developer build from `patches/ports/om-5-i-from-ii` on the alpha2 donor, package SHA-256
`70788992f032dad53bfa4e145b2147e376d3f25a62e2b1ce2929973fec26d1b4`. This candidate is the Mark II (E148 1.1)
program and its Caduceus patch, placed in OM-5 1.2's update layout with OM-5 1.2's controller firmware (010e).
**Everything below is emulator or static evidence. No camera has run it, and nothing here shows that it boots.**
Compact numbers: `tests/e144-emulator-static.json`.

## 1. OM-Emu's original OM-5 model cannot run it

Stock OM-5 1.2 boots in OM-Emu's E144 model and reaches the super control panel and menu. The candidate does not
start there: `PlayError: UI_IN record count: 0x501104e2 starts with a0, not mov imm8,d3`. The model's handlers are
written against OM-5 1.2's code addresses, so it rejects any other program, whatever the hardware would do. This is
a limit of the tool, not a result about the camera.

## 2. In OM-Emu's Mark II model it behaves exactly as the Mark II build

OM-Emu models the Mark II on the **same board family as the OM-5** (`board: { family: 'E144' }`, same MMIO map:
ISC 0x8fe00000, VSC 0x9c000000, engine 0x9c100000, SRAM 0x8ff00000). Its authors ported the Mark II from the OM-5
model and paired 9.50 M instructions with 41 conflicts. That supports, but does not prove, that the two cameras
share their main SoC and memory map.

With the candidate's main program and resource block in that model:

- all 13 film regression cases pass (`tests/run_emulator.py --build` on the candidate), with no image stores beyond
  the stock baseline;
- a 23-step tour (shooting screen, super control panel, Picture Mode, menus, INFO, playback) gives frames
  byte-identical to the alpha2 Mark II build.

**What this does not test:** OM-Emu places the resource block itself. A watch over flash 0x42d40000..0x46c40000
saw no reads, so the 21 resource addresses the builder relocates to OM-5 positions are not exercised. Nor are the
sensor, IBIS, charger, controller (010e) link, bootloader, or the OM-5's own settings block.

## 3. Static comparison of the two stock programs

`tools/dev/xbuild.mjs` (OM-Emu's cross-build map) pairs OM-5 1.2 with Mark II 1.1:

- 17,468 of 20,298 OM-5 function starts pair with a Mark II function; 4.20 M instructions paired, 68 conflicts.
- 100 paired instructions carry a different constant in 0x80000000..0x9fffffff:
  - 7 are the resource-range bounds at 0x60021772..0x6002192c (uncached aliases 0x863c/0x869e on OM-5,
    0x8662/0x86c4 on Mark II). **The candidate already uses the OM-5 values** (the builder's relocation covers them).
  - 91 are numbers like 0x80000012 → 0x80000015, 0x80800004 → 0x80800005, 0x88000009 → 0x8800000a: they shift by
    one to three in step, the pattern of renumbered identifiers (the Mark II added entries), not of addresses. The
    candidate keeps the Mark II values, which matches the Mark II program it is. If any of them is an identifier
    exchanged with the controller (010e, kept from OM-5), that exchange would disagree; not established either way.
  - 2 are in the on-chip SRAM, below.

### On-chip SRAM 0x8ff00000

`tools/dev/sram_compare.py`: each program addresses this 4 KiB SRAM 708 times. 445 of the 446 accesses paired by
surrounding code use the same address. The layout differs in one place, a 0x40 shift:

| Use | OM-5 1.2 | Mark II 1.1 |
|---|---|---|
| region argument passed by 0x6040d585 / 0x60411fd3 | 0x8ff00450 | 0x8ff00410 |
| byte used by the module at 0x61518f97..0x6151a28c / 0x6151b702..0x6151cac7 (5 accesses) | 0x8ff00490 | 0x8ff00450 |

The candidate's program is wholly the Mark II's, so it is consistent with itself. It matters only if code outside
the update (boot ROM, a loader, the controller) reads these SRAM offsets with OM-5 1.2's layout. Not found, not
excluded.

### Controller firmware (010e)

Both are 262,080 bytes with 220,160 used; 55.9 % of bytes are equal at the same offset. They are different builds.
The candidate pairs the Mark II application with OM-5 1.2's controller, so their message protocol is the largest
unknown. Not analysed further.

## What would move this forward

1. A camera test, by the owner only, after the Mark II alpha has run on a Mark II. Not before.
2. Static: trace the identifiers above to see whether any crosses to the controller or the second core.
3. Static: find who else reads SRAM 0x8ff00410..0x8ff004a0 (boot ROM, loader).
4. Emulator: an OM-Emu E144 model that can run Mark II code (its handlers mapped through `port_via`) would exercise
   the relocated resource addresses. That is work in OM-Emu, not here.

The candidate stays **developer-only**: no consumer release, no install file by default, no install advice.
