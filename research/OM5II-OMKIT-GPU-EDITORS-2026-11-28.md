# Borrowing Color Creator's GPU drawing, as OMKit does (2026-11-28)

**Research, no build of the GPU path.** A reading of OMKit (necrostaz/omkit at `cc55893`, 27 Nov 2026: code
Apache-2.0, docs CC BY 4.0) plus three OM-Emu probes of the GUI half on this project's `main` (`47a5865`, strict build,
OM-Emu `xulfr/om-emu` `bdb3347`). Nothing here ran on a camera. **OMKit's camera results are OMKit's**, for OMKit's
build: they show the method can work on E148 1.1, not that our build will. Addresses are runtime addresses of the
expanded main program (base `0x60021020`).

This supersedes the recommendation of [the c3d note](OM5II-C3D-GPU-WHEEL-2026-11-27.md) ("keep CPU drawing"). That
note assumed borrowing the Color Creator kind was impractical because our restored pages never send its START / DRAW /
END. Probe 2 below shows that one panel write, made after the stock item handler, makes our pages send all three.

## 1. OMKit's method (from its code and `docs/platform/om5m2/ui.md` §4.2–4.6)

E148 keeps the profile items' handlers and dial logic but no drawing for them. OMKit makes the GUI order the
**Color Creator** drawing for its profile items and replaces what Color Creator's renderer draws.

| Part | Site | What OMKit does |
|---|---|---|
| Item redraw table `0x611b79a8` (32 × `{u32 item − 6, u32 branch}`, section 7 data) | words `0x611b7a64` (5373), `0x611b7a6c` (5374), `0x611b7a74` (5375), `0x611b7aa4` (5029) | Each branch word points at a trampoline: the item's own handler (`0x60e4af24`, `0x60e4ac9b`, `0x60e4b018`), then the values are published, then the Color Creator "background" is written: panel `a3` + 4278 + 10 = `0xfff8`, +12 = 1, `a3` + 17 = 1; +8 = the Reset OK Hold hint, +9 = 0. Back to the dispatcher at `0x60e49e4a`. 5029 (the real Color Creator item) turns OMKit's mode off |
| Color Creator renderer entry `0x60ccf4f7` (task `C3D_MAIN`, **CPU 1**) | 5-byte `jmp` (back `0x60ccf4fe`; displaced `mov a0,a2; mov 0x60f580a8,a1`) | If the published mode is OMKit's, draw with the firmware's OpenVG, `eglSwapBuffers` (`0x60ccf0f8`) and return as the renderer does (`ret [d2,d3,a2,a3],212`); otherwise, or on any failure, the native code |
| OpenVG / EGL | `vgCreatePath 0x613dab09` … `vgClear 0x613daad8` (15 entries, `fw.ld`) | Called with the firmware's own call-site frames (`thunks.s`). First 8 bytes of every entry, and of the item handlers, checked before hooking |
| Shared block | 32 words, 64-byte aligned, used only through the uncached alias | Sequence counter odd while CPU 0 writes; the renderer retries up to three times, else leaves the frame to the native code |
| Renderer rules | `editor.c` `drv_edp_draw` | No cached core variable on CPU 1; constants through the uncached alias (sines copied to the stack once a frame); paths `VG_PATH_DATATYPE_S_16` in quarter pixels; no floating point (float parameters as bit patterns); one path and one paint per frame; arena work buffer (352 segments, 320 points); surface size from `0x625b475c` / `0x625b4760` (refused unless 256..1024) |
| Mode off | core loop | Off unless GUI state `0xa234f838` = `04 18` and setting 2148 (the item under the cursor) is the item |
| Install | core task at run time | Code (`0x60ccf4f7`) and table words written **at run time** through the uncached alias (`drv_code_jump`, `put_word`); CPUs 1 and 2 are not stopped (OMKit lists that as a residual risk) |

What OMKit draws (§4.3): Color/Vivid as a 12-gon in the hue colours with a polygon of the 12 saturations (about 60
fills and strokes); Color/Level as a 48-sector hue ring with filter ticks, level circles and a needle (about 90 fills);
the tone curve as a 200 × 200 frame, cubic curve through Sh / Mid / Hi and seven-segment numbers (about 80 calls). The
renderer's stack use is 430–630 bytes of the task's 4 KB (OMKit's bench).

## 2. What OM-Emu shows on our build (the GUI half only)

Scratch PRE modules traced the stock sites on `main`'s strict build; the keys were Color Profile 1 → wheel → `main+1`
→ tone page → `sub+1` → up to the strip.

1. **Probe 1, stock sites run on our pages.** The item dispatcher reaches `0x60e49e31` → `0x60e4ac9b` (5374) on arrival
   at the wheel and on each dial step, and `0x60e49e43` → `0x60e4b018` (5375) on the tone page. The panel is the same
   object each time (`a3 = 0x61ad0730`). So OMKit's trampoline sites apply to our restored pages, although our pages
   are the direct screen's children 2–5 shown by `pages_hook` and drawn by our view paint hooks.
2. **Probe 2, one panel write starts the GPU order.** Writing OMKit's bytes at `0x60e49e4a` after the 5374 / 5375
   handlers (panel + 4278 + 8..12 = `00 00 f8 ff 01`, panel + 17 = 1): API `0x10308` background start once, START to
   the camera side (`0x6030f09a`) once, then the order builder (`0x60887fba`) and send (`0x608882f9`) once per redraw
   (5 orders), and `0x10309` / background end when leaving to the strip. **Without the write: none of these.** The
   direct screen's own `chgBackGround(0xfffd)` calls (36 in both runs) do not stop it.
3. **Probe 3, OM-Emu cannot show it.** Once the background is active OM-Emu's compositor stops with
   `FMT_UNMODELLED` and writes no frame until it ends: no screenshot of our OSD page while the GPU path is on.

The camera side (the C3D interface task, `C3D_MAIN` on CPU 1, OpenVG) does not run in OM-Emu at all.

## 3. Hooks and addresses: OMKit's against ours

Checked mechanically against every range of `firmware/om5ii/patch.json` (127 + the new `cursor_pointer`) and its 79
data edits.

| OMKit site | Ours | Clash |
|---|---|---|
| Item branch words `0x611b7a64` / `6c` / `74` / `a4` | none in that table (our rows use other slots; [rows note](OM5II-PICTURE-MODE-ROWS-2026-11-19.md)) | No |
| C3D entry `0x60ccf4f7`, `eglSwapBuffers` `0x60ccf0f8`, OpenVG `0x613da235..0x613dadc8` | none | No |
| Color Creator layout words `0x610c174c..0x610c18de`, item 5374 picture word `0x611b4ce2` | `paint_pointer` `0x610c1540` (the wheel view's paint slot, a different widget) | No |
| Settings object methods `+0` / `+4` / `+8` (`0x60bb6ad0`) | `def_pointer` `+152` (`0x60bb6b68`) | No (different words) |
| Panel + 4278 + 8..12, + 17 (the Color Creator background block) | Our Reset OK Hold hint uses the row status at panel + 4300 + 9 / + 10 ([look defaults](OM5II-LOOK-DEFAULTS-2026-11-27.md)) | No overlap. Whether + 4278 + 8 (Color Creator's own Reset hint) shows on our page is unknown: a probe writes 0 there |
| Loader: `FastEndCb` `0x601b1362`, cave `0x605af4c0..0x605af800`, flag `0x615ee7c0` | `bg_site` (same site, PR #15), `ext2` / `wb_extension`, `ext9` | **Yes**, as already recorded: Caduceus and OMKit cannot be installed together |
| String getter hook `0x60d52edb` | `hook_str` `0x60d52ed5` | Adjacent, not overlapping; irrelevant (no coexistence) |
| Arena `0xa3470000..0xa375ff00` | `CADUCEUS.BIN` at `0xa3700000` | Same reason |

New today: `cursor_pointer` `0x61211cf4` (phase 2, below) is the colour editor's vtable slot +100, not used by OMKit.

**The one real difference is how hooks are made.** OMKit writes code and section-7 words at run time through the
uncached alias. This project keeps hooks static in flash and stores nothing into the loaded image, since the
8 November failure began at the first stores into it ([fault note](OM5II-IMAGE-STORE-FAULT-2026-11-11.md); those were
cached-alias stores, OMKit's are uncached). Every OMKit site above can be static here instead:

- the four item words are data pointers, the same kind as `paint_pointer` and `cursor_pointer`;
- the C3D entry is a 5-byte `jmp` like our other code hooks. Its trampoline would run on CPU 1 on **every** Color
  Creator frame from start-up, including the stock Color Creator mode. Its unarmed path must be a few instructions:
  read one published word through the uncached alias, and if it is 0, replay the displaced instructions and jump back.

Recommendation: static hooks, with the trampolines in `.ext2b` (section 2, 390 bytes were free; phase 2 used 138).

## 4. Carrying the renderer into Caduceus

| Route | For | Against |
|---|---|---|
| **A.** Build OMKit's C renderer with its toolchain (GCC 13.3.0 + binutils 2.45, `toolchain/build-toolchain.sh`, `-Os -ffreestanding`) into `CADUCEUS.BIN` | Reuses code that draws on the camera for OMKit almost unchanged | Every builder needs GCC (about 3.5 GB of build tree, pinned version); our testers' setup and CI gain a compiler |
| **B.** Port to hand assembly | One toolchain, as now | About 950 lines of C (`editor.c` 560–1654 without comments; 380 of them are film-look code we do not need) of fixed-point path building: errors only a camera would show |
| **C.** A, but commit the compiler's assembly output next to the C | Builds and testers keep binutils 2.42 only; the C stays the source; a check regenerates the `.s` and compares when GCC is present | One generated file in review; GCC's ABI (args d0, d1, then stack; d2, d3, a2, a3 kept) must match our callers, as OMKit's `thunks.s` shows it does |

**Recommendation: C.** Take `editor.c`'s pen, path, sine and OpenVG-call code with its Apache-2.0 header, drop the film
look parts, and add our drawings (§6).

**Where CPU-1 code may live and run.**
- `CADUCEUS.BIN` is written only through the uncached view, at an address no CPU has run code from before in the
  power-on. That is the rule OMKit's core image follows (`0x6345a010`, also run on CPU 1 by its renderer). Its 64 KiB
  limit has room: the block is 1,071 bytes now, the renderer an estimated 3–6 KB (not compiled yet).
- On CPU 1, read nothing through a cached view that CPU 0 writes: not `st_ptr` (its handle is in cached `.bss`), not
  P. The shared block should be a fixed, 64-byte-aligned block inside the card block's area, used through
  `0xa37…` only, with OMKit's sequence counter.
- The card block's existing checks (CRC, build words) still gate it. The OpenVG / EGL entries and the item handlers
  get fingerprinted at load on CPU 0. On any mismatch the GPU path stays off and nothing changes.

## 5. The fixed 256 × 256 surface against our page

- The surface size is fixed by `C3D_MAIN` (`0x625b475c` / `60`). OMKit's docs say it is centred over live view, in
  the image layer under the OSD. Not measured for our pages. Centred would be x 232..488, y 112..368.
- Our page (OM-Emu frames): the left column to x 88; the axis title top right (about y 20–50); "Color" and its swatch
  at about (500–610, 100); "Vivid ±n" at about (500–610, 377); the hint at (290–432, 420–462). Our CPU wheel is centred
  at (290, 222) with an outer radius of about 124.
- So a centred surface clears the column and the right-hand labels but sits about 70 px right of the CPU wheel. A GPU
  wheel would replace the CPU wheel, not overlay it. The band between the surface and the hint (y 368..420) has room
  for the H / S / L bar.
- The OSD is drawn over the image layer. Our page must not paint opaque over the surface: it does not on OM-Emu's
  model; the camera has to confirm.
- **First camera question: where the surface lands.** The first probe therefore draws a calibration frame, not a wheel.

## 6. What to draw

- **Colour wheel (item 5374).** OMKit's 12-gon frame in the hue colours (yellow at the top, clockwise, as ours), with
  the polygon and spoke of the **active axis**. Our cells are −5..+5 on Saturation, and a look can set −7..+7; scale
  by the axis. Sat. All: the whole polygon outlined, as OMKit's "all hues".
- **The v0.41 H / S / L bar: on the OSD**, with our pen, in the band under the surface. Axis-aligned blocks are cheap
  for the OSD pen (the 1,000-command limit hits slanted lines only), and OM-Emu can test it. The OM-3 draws its bar on
  the OSD too (the guide plane).
- **Tone curve, five points (item 5375).** The GUI side (CPU 0) samples the curve our image path makes (Black, Sh,
  Mid, Hi, White) into 64 points and publishes them with the five handles. The renderer only draws a polyline and
  crosses, as OMKit's film-look curve does. One curve definition, kept on CPU 0.
- **Filter ring (item 5373).** OMKit's Color/Level ring. Its filter order (`filter_pos`: none, Ye, Or, R, then G, GY,
  M, B, C by angle) must be checked against our `gfx_filter` table (`ftab_*`) before reuse.

## 7. Testing

| What | How | Can it prove it? |
|---|---|---|
| Hooks are armed only with the switch file; GUI order START / ORDER / END on our items and none elsewhere | OM-Emu, a test like probe 2 counting the sites | GUI half only |
| Our OSD pages unchanged with the switch off | The existing runners (`run_page_graphics.py` and the rest) | Yes, in OM-Emu |
| Our OSD pages with the switch on | Not with OM-Emu as it is (probe 3). A small `xulfr/om-emu` change could skip the unmodelled layer | Not yet |
| The renderer's geometry | A host bench: compile the drawing code for the host with a software stand-in for the 15 OpenVG calls (fill S16 polygons into a 256 × 256 PNG) and compare with reference pictures. OMKit's bench is not in its public repo; only `tests/host/test_edtrig.c` is | Geometry only |
| CPU-1 rules | Link map check: the renderer touches only its stack, the uncached aliases and the card block | Static only |
| Running on CPU 1 with the real GPU | The camera. The E-M5 III `c3drun` port (days of work) runs c3d against a stand-in, not the GPU; not needed for a probe | Only the camera |

## 8. Licence

- Code taken from OMKit (Apache-2.0, same as ours): keep its copyright header in each file, mark our changes, and add
  OMKit's attribution to `NOTICE` ("OMKit, Copyright 2026 The OMKit Authors").
- Documentation facts used here and in earlier notes (addresses, the arena test, the `FastEndCb` site) come from OMKit's
  CC BY 4.0 docs. `NOTICE` now credits them (this commit). The code line is added with the first code taken.
- Nobody at OMKit was contacted.

## 9. Recommendation and the first probe build

**Go, as a switchable probe.** OMKit shows the method on this firmware (for its build). OM-Emu shows our pages reach
the same sites and order the drawing. What is left is CPU-1 code that only a camera can test, so the probe must fall
back to today's CPU drawing by default and with any check failing.

**Probe g1: "is it there, and where"** (one build, wheel page only):
1. **Switch.** `OM5MOD/GPU.ON` read by the background task after `CADUCEUS.BIN`. Without it nothing is published and
   no panel byte is written, so the GUI never orders the drawing: today's behaviour exactly. OK held at switch-on
   already skips the card.
2. **Static hooks.** Item word 5374 → a trampoline in `.ext2b`: the stock handler as the stub calls it; then, only if
   armed, block loaded, fingerprints good and the switch on, publish mode 1 and write panel + 4278 + 9..12 and + 17
   (+ 8 = 0). Item word 5029 → mode 0, then its stub, so Color Creator keeps its own ring. Leaving the PM screen any
   other way: the renderer also requires GUI state `04 18` (read uncached on CPU 1), else native.
3. **CPU-1 trampoline** at `0x60ccf4f7`: mode word (uncached) 0 → displaced instructions, back. Otherwise call the
   card block's renderer entry; 1 → `ret [d2,d3,a2,a3],212`, 0 → native.
4. **Renderer g1** draws a calibration picture: the surface's border, a centre cross, corner marks and a plain 12-gon.
   The CPU wheel is still drawn, so the owner can report the offset between the two.
5. **Tests before the camera:** strict build; `check.py full`; all page runners with the switch off; a GUI-half test
   with the switch on; the host bench for the picture.
6. **Camera checklist (owner):** with and without `GPU.ON`: start-up; open and leave the wheel page 20 times by
   up / down, OK, MENU and a half-press; stock Color Creator mode shows its own ring; sleep and wake; where the
   picture lands against "Color", "Vivid" and the hint (photo).

Then **g2**: the wheel with values on 5374, the CPU wheel hidden while the GPU one is on, the H / S / L bar on the OSD.
**g3**: the tone curve (5375) and the filter ring (5373).
