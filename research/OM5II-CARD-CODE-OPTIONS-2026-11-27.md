# More room: card code, OMKit and an OM-3 Caduceus port (2026-11-27)

**Review of other projects' published work, plus our own measurements. Nothing was built or run.** The owner asked
what it would take to move Caduceus work onto the SD card, and whether that would allow a full OM-3 Caduceus port.

Sources read:

- **Caduceus for OM-3** (androidfanman/caduceus-om3), tag `v0.41-beta3` (`c038fa6`): `FILM-ROLLS-ROADMAP.md`,
  `research/NOTES.md` (firmware-space probes GX1–GX4), `README.md`, `firmware/src/editor.ld`.
- **OMKit** (necrostaz/omkit) `cc55893`: `docs/architecture.md`, `docs/sdk.md`, `docs/platform/om5m2/*`.
- The Atlas records for both.

Basis words below follow those projects' own labels: "camera" means reported by that project on its camera.

## 1. Where we are

- **Flashed code:** 9,753 of 10,592 bytes. 839 are free, 686 of them in `.ext2b`.
- **State:** a 1,544-byte heap block.
- **Big users:** the colour-wheel editor (~2.0 KB), the profile restore (~1.4 KB) and looks (~1.3 KB).
- **No further features without new room** ([v0.2.0 plan](../docs/V0.2.0-PLAN.md)).

## 2. Three ways to get room, each already working on a related body

### A. Code blocks from the card in the firmware heap (OM-3: GUIDES.BIN, FILMROLL.BIN)

- **How:** at the first half-press the camera reads a file, checks its size and tag, relocates it into a block from
  the firmware's `malloc` and runs it from the cached view. The flashed hooks shrink to "file loaded? call it,
  otherwise stock".
  - The OM-3 has done this since v0.20 (camera). Film Rolls (`FILMROLL.BIN`, 14,200 B) is the second such file.
  - Lessons: one file per firmware build (tag match); code must run cached (an uncached run rebooted the OM-3, "lk7");
    nothing may load at start-up; card writes stay off the shutter's task.
- **Limit:** one block is at most **16,448 B**, the allocator's largest class, which is also our P block's class. The
  OM-5 II's CPU-0 large class has 57 blocks of 16 KB, about 36 free a few seconds after start (OMKit, camera). The UI
  and video recording use the same heap: OMKit reports "REC heap(cache) not enough" when it runs short.
- **Suits:** moving 10–30 KB of UI code (wheel, tone and filter graphics, looks reader, editors). **Not** a full port.

### B. Grow a flashed section by moving its loaded-end word (OM-3: GX1–GX4)

- **How:** the OM-3 changed the section loader's end word (E147 `0x60045e9c`) so section 6 loads past its stock end.
  It proved the extension in four camera probes: +4 KiB, +64 KiB, +256 KiB, then to `0x6103f000`, about 1 MB.
  - Each probe wrote a pattern and logged it to the card.
  - Results: 0 bad words, through bursts, RAW+JPEG, 4K video and Wi-Fi.
  - The OM-3 now holds about 141 KB of code there (`.ext15` 139 KB) plus large buffers.
- **On E148:** the gaps after loaded sections (from the section table, `0x600284fc`) are:

  | After section | Gap | Compressed? |
  |---|---|---|
  | 1 | about 378 KB | no |
  | 2 | about 124 KB | no |
  | 4 | about 106 KB | no |
  | 8 | about 108 KB | no |
  | 9 | about 108 KB | no |
  | 6 | about 92 KB | yes |
  | 7 | about 650 KB | yes |

  - None is proven on an OM-5 II. A port needs its own GX-style probes, one camera round each.
  - It touches the boot path, which is where this project's black-screen failures came from. It is safest on the
    uncompressed sections.
  - **Our [plan](../docs/V0.2.0-PLAN.md) ranks this "highest risk, not planned for 0.2.0".** The OM-3's success on its
    sibling body lowers that risk but does not remove it.
- **Suits:** everything that must work **without a card**: the image pipeline, start-up and power-off paths. Hundreds
  of KB, if the probes pass.

### C. OMKit: a loader once, then core and modules from the card (OM-5 II 1.1)

- **How:** one 5-byte hook at `FastEndCb` `0x601b1362`, about 1.2 s after power-on, which only starts a low-priority
  task.
  - The task reads `OMKIT\CORE.BIN` into a **3.2 MiB DRAM gap** past resource record 0 (`0xa3456d74..0xa3791000`,
    camera pattern-tested 76 times, 0 differences).
  - It then loads modules written in C against a published SDK.
  - Hooks are written into the code at run time through the uncached view. Writing through the cached view resets
    the camera (memory protection). OMKit measured hooks working on CPUs 0–2 (camera).
  - With no card, or OK held at power-on, the camera runs stock.
  - Licence Apache-2.0, the same as ours.
- **Status:** v0.1.0 (2026-11-20), one developer camera. Wi-Fi and USB start paths are not verified. A crashing module
  resets the camera. Modules CREATPRF (restores CP1–3 / MONO1–3) and FILMLOOK (.ISP presets).
- **Conflicts with Caduceus as flashed today (static, from the addresses):**
  - OMKit's trampoline and loader body use the section 2 tail `0x605af4c0..0x605af64a`. That overlaps our `.ext2`
    (`0x605af4b0..0x605af771`) and their tail reservation runs to `0x605af800`, over our `wb_extension`.
  - Its once-per-boot flag `0x615ee7c0` is inside our `.ext9` (`0x615ee5c8..0x615ee7ff`).
  - **So the two cannot be installed together without one moving.**
  - CREATPRF duplicates our profile restore.
  - Its arena sits next to resource record 0, which our patch edits (pointer aliases only; the record's expanded length
    is expected to be unchanged, **not checked**).
- **Suits:** the most room by far (MBs), C instead of assembly, and updates by copying files. The price is depending
  on a young outside project and its loader, or forking it.

## 3. What a full OM-3 Caduceus port means

The OM-3 Caduceus (README, v0.41) has:

- 20 films in the Picture Mode list, kept in camera memory.
- Colour Mix and RGB curves.
- Hue, saturation and luminance for 12 colours.
- Split toning with Tone Balance.
- Blacks / Whites.
- WB shift ±7 and white balance per film.
- Sharpness / Noise Filter / Vignette / Shading / Glow / Clarity rows.
- Halation.
- Colour grain from the image processor.
- Button Function and Creative Dial mapping.
- The recipe in the EXIF.
- A debug log.
- Film Rolls.
- A `*` after a changed COLOR's name, using E147's own `*` title pictures (string ids 15710..15713). That is the star
  the owner expected on our build (see the [look defaults note](OM5II-LOOK-DEFAULTS-2026-11-27.md)).

Its code is about **150–300 KB** (flashed `.ext15` 139 KB, plus `.ext4` / `.ext8`, the section-6 regions, and two
card blocks of about 16 KB each). That is **15–30 times our whole flashed budget**. So:

- **Route A alone cannot hold it.** It would need 10–20 heap blocks of 16 KB from a heap the UI and video depend on.
- **Route B or C is required.** B keeps the OM-3's "any card works" property (v0.29); C does not, unless the
  essentials stay flashed.
- It would also mean a re-port per feature. The OM-3 code is E147 assembly at E147 addresses. Our existing port shows
  that most UI sites differ on E148, and E148 lacks native features E147 has (for example `DRAW_PROFILE`, see
  [c3d note](OM5II-C3D-GPU-WHEEL-2026-11-27.md)). Each feature needs its own trace, emulator tests and a camera round.

## 4. Firmware or card: a proposed split

Rule of thumb: **what decides the photo, or runs at start-up or power-off, stays flashed. UI and optional extras can
come from the card.**

| Keep flashed | Move to the card (or to new flashed room) |
|---|---|
| Profile restore data and refresh (CP1–3, MONO1–3), profile-number repair, custom-mode reset | Colour wheel, tone and filter graphics (~1.3 KB) |
| Applying H/L, Black/White and tints to the image (builder, curve and gamma hooks) | Editor UI: axis switching, labels, hints, look defaults |
| Per-profile WB commit hook, ND32/64 data, Picture Mode timeout | Reading `LOOKS.BIN`, look names |
| Arming gate and a card loader (A or C) | New features: film rolls, halation, RGB curves, Colour Mix, EXIF recipe, debug log, the `*` |

Without the card, saved values would still reach photos, but you could not edit the extra axes, step looks or use
new features.

## 5. Recommendation and decisions for the owner

1. **Near term (v0.2.x): route A for our UI code.**
   - Move the graphics and editor UI (~5–8 KB) into one `CADUCEUS.BIN` block. The OM-3's GUIDES.BIN pattern is the
     model: tag per build, first half-press, cached, hooks fall back to stock.
   - This frees the flashed tails for the image-path code and lets the next features ship.
   - About one emulator cycle and two camera rounds (loader, then moved code).
2. **For a full OM-3 port: choose B or C first.** This is the owner's call:
   - **B (grow a section)** keeps one self-contained firmware and "any card works". It needs E148 GX-style probes on
     the camera, the first touching the loader end word.
   - **C (OMKit)** gives MBs and C modules, but makes Caduceus depend on OMKit's loader (or a fork of it). It also needs
     the overlaps in section 2 / 9 resolved, either by moving our tails or by Caduceus becoming OMKit modules.
     It may be worth asking the OMKit authors (issues on their repo) whether they would want Caduceus as modules.
     That contact is the owner's to make.
3. **Either way, port feature by feature.** Start with what users ask for most, and keep the camera-test-per-step
   rule.

## Not established

- **E148 loader end words:** their addresses and whether moving one behaves as on E147.
- **Heap headroom on our build:** free 16 KB blocks on a camera running Caduceus, during video.
- **OMKit beside Caduceus:** whether its loader could live elsewhere, and whether our resource record 0 edit keeps
  the record's length.
- **E148 star pictures:** whether E148 still carries `*` title pictures for Color Profiles.
