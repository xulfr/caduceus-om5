# Roadmap: OM-3 Caduceus parity on the OM-5 Mark II (drafted 2026-11-28)

A plan, not a result. Nothing here has been built. Compared from
[androidfanman/caduceus-om3](https://github.com/androidfanman/caduceus-om3): `main` at `2c56343` (v0.40.3) and the
test branch `try/v0.41-beta4`. The OM-5 Mark II side is this repo's `main` after PR #15. OM-3 statuses are that
project's own reports on the OM-3 (E147). They are **not** evidence for the OM-5 Mark II (E148).

**Scope (owner, 2026-11-28).** Picture Mode controls and UI first, starting with the colour wheel's graphics.
- After parity: one look format and one editor with the other Caduceus projects (issue #4).

**Owner decisions (2026-11-28):**
- Split toning moves to its own row, as on the OM-3. This reverses the 2026-11-20 decision.
- Ranges match the OM-3.
- Keys copy the OM-3 v0.41.
- The Midtone Tint is deferred.
- Feature parity comes first, look compatibility afterwards.
- Out of scope: Film Rolls.
- Out of scope, as the OM-3 itself has done: video features.

## Where the two stand

### Picture Mode controls

| OM-3 (v0.41-beta4) | OM-5 Mark II now | Gap |
|---|---|---|
| **Colour wheel graphic** drawn by the camera's GPU (stock `DRAW_PROFILE` background, various-draw type 11) | Drawn by our code on the CPU with OM's OSD pen, as axis-aligned blocks (`gfx_wheel`, now in `CADUCEUS.BIN`) | E148 has no `DRAW_PROFILE`, but OMKit borrows the Color Creator drawing on E148. See phase 1 |
| **H / S / L bar** under the wheel: the selected colour's Hue, Saturation and Lightness together. INFO steps H → S → L. Front dial past the first colour gives "Sat. All". Delete does nothing on the wheel. "H/S/L INFO" hint | Key map and hint as the OM-3 v0.41 since 2026-11-28 (emulator only; the colour dial is the rear one on this body) | Bar graphic |
| **Split toning on its own row**: Shadows, Balance, Highlights, with a bar for the tint colour. Strength 0–10 in half steps. Tone Balance −5..+5. "Split Tone INFO" hint | Three tints (Shadow, Midtone, Highlight) on the wheel's Tint group, strength 1..5, no balance. **A separate split-tone row was abandoned here on 2026-11-20 (owner).** | Own row, as on the OM-3 (owner, 2026-11-28). Midtone Tint deferred |
| **Highlight & Shadow as one five-point curve**: pages Sh / Hi, Mid, Blk / Wht, with all five values in the top line. Reset and "*" follow the film's values | Tone page INFO steps Hi/Sh → Bl/Wh → Mid, −7..+7. The curve graphic shows all five. Hold OK goes to the look's values (emulator only) | Mostly there. Missing: all five values in the top line, and the INFO order |
| **Color Mix** row: R, G, B dots on a ring, Sat and Hue −7..+7, INFO picks the colour | None | New row and new image-path work |
| **RGB curves** row: five points per channel, −7..+7 | None. The R/G/B curve route is used inside, by Black / White and the tints | New row. The same route is camera-proven here for tints and Black / White |
| **WB Compensation** row in Picture Mode, with OK opening the camera's grid. Each film keeps its own A-B / G-M, and the camera's own modes keep the camera's | Each Color Profile remembers its own WB mode, Kelvin and shift (not camera-checked). There is no Picture Mode row | Row only |
| **"*" changed marks** on the profile name and on each changed row | OM's "Reset OK Hold" hint, which follows the look (emulator only) | Marks |
| Sharpness −5 (off) .. +2. Noise Filter and Vignette Correction rows per film | Sharpness and Contrast −2..+2, Shading −5..+5 | Small rows |

### Behind Picture Mode

| OM-3 | OM-5 Mark II now | Gap |
|---|---|---|
| Films and edits kept in the camera's own memory, so any card works (v0.29) | Profile values are kept in the camera. Looks and graphics come from the card at each switch-on | Looks in camera memory (later) |
| Ready at switch-on, no half-press (v0.30) | Same since PR #15 (emulator only) | Camera check |
| Super control panel dial steps COLOR 1–4, then FILM 1–20 | It shows the look's name. Looks are picked by trash on the Picture Mode row | Dial stepping (later) |
| Film name and recipe in each JPEG (photo code `om3.2.`) | None | Later |
| Effects: Glow / Clarity, Halation (+ Radius), colour Film Grain (1–5, size), Border, crop modes | Clarity is blocked on the Soft Focus weight getter. Colour grain is shelved: the stock grain pass is monochrome-only | Out of this roadmap's first phases |

## Why the OM-3's wheel can't simply be copied

- **On the OM-3**, the wheel is free: stock firmware already has the Color Profile editor. Its page controller asks the
  GPU layer for the profile wheel (`chgBackGround DRAW_PROFILE`, background `0xffec`). The OM-3 project reuses that
  wheel and adds pages and labels around it.
- **On the OM-5 Mark II**, OM removed the Color Profile feature. Caduceus restores it.
  - E148's controller sends only `0xfffd`, and its background table has no `0xffec`.
  - c3d's START switch accepts only kinds 1, 2, 6, 8 and 9: Part Color, Color Creator, ART, Scene top and Select shooting.
  - [WIP UI3](../research/OM5II-WIP-UI3-2026-11-16.md) and the
    [c3d note](../research/OM5II-C3D-GPU-WHEEL-2026-11-27.md) give the details.
- So a GPU wheel here means **putting a renderer back** that E148 no longer has. It is new code on the second CPU,
  on a GPU path OM-Emu cannot run, and only a camera test can prove it. This is the riskiest item on this page, not
  the easiest.
- **New, 2026-11-28:** OMKit (necrostaz/omkit) does exactly that on E148 1.1, camera-measured for OMKit: it makes the
  GUI order the **Color Creator** drawing for the profile items and draws its own editors in Color Creator's renderer
  on CPU 1. In OM-Emu our pages reach the same sites and order that drawing after one panel write.
  [Study and probe plan](../research/OM5II-OMKIT-GPU-EDITORS-2026-11-28.md).

## Phases

Each phase ends with an emulator-checked build, the owner's camera test and a camera report with the package
SHA-256, before the next phase builds on it.

### Phase 1: the colour wheel's graphic (research done 2026-11-28: go, as a switchable probe)

1. **Static trace and study: done.** [OMKit GPU editors note](../research/OM5II-OMKIT-GPU-EDITORS-2026-11-28.md):
   borrow the Color Creator kind as OMKit does. No clash with our hooks; hooks static in flash rather than OMKit's run-time
   writes; the renderer in C from OMKit's `editor.c`, compiled with OMKit's GCC and committed as assembly, in
   `CADUCEUS.BIN`; the H / S / L bar on the OSD; the curve sampled on CPU 0.
2. **Emulator tooling: not needed for the probe.** OM-Emu tests the GUI half; a host bench tests the renderer's
   geometry. The `c3drun` port stays optional.
3. **Probe g1**: a calibration picture on the wheel page, only with `OM5MOD/GPU.ON` on the card; without it, today's
   CPU drawing exactly. Camera test by the owner (where the surface lands, entering and leaving, stock Color Creator).
   Then g2 (the wheel with values) and g3 (tone curve, filter ring). Build plan in the note, §9.

**Fallback, if the probe fails on the camera:** make the CPU wheel look closer to OM's.
- The card block gives the drawing code room now. The limit is OM's OSD command buffer, about 1,000 commands per
  repaint.
- Options: filled colour sectors in the screen's palette, a ring as stacked spans instead of dots, the H / S / L bar
  from phase 2.
- This needs no second CPU and no GPU, and OM-Emu shows the result.

### Phase 2: the v0.41 colour wheel and tone page controls (CPU drawing)

Everything here is UI over values the OM-5 Mark II already has. The risk is in Picture Mode screen code, not the
image path.

1. **H / S / L bar** under the wheel: the selected colour's three values, drawn in `CADUCEUS.BIN`.
2. **Key map as on the OM-3 v0.41: done 2026-11-28 (emulator only).** INFO steps H → S → L; the colour dial past the
   first colour gives "Sat. All" (OM's own ring; the colour dial is the **rear** dial on this body, the front on the
   OM-3), skipped on Hue and Lightness; Delete does nothing on the wheel; hint "H/S/L [INFO]". Test
   `tests/run_wheel_keys.py`. **The tints have no key until phase 3**: stored tints still apply. Phase 2 should not
   go to the camera without phase 3.
3. **Tone page:** all five values in the top line. INFO order Sh / Hi → Mid → Blk / Wht, as on the OM-3.
4. **"*" changed marks** on the profile name and rows, from the look defaults already in place.

Tests: new OM-Emu cases per key path, as `run_bw_tint.py` and `run_look_defaults.py` do. `check.py fast`, then `full`
before the camera build.

### Phase 3: split toning on its own row, as on the OM-3

**Step 3a done 2026-11-28 (emulator only):** the row under the wheel (OM's colour editor a second time), Shadows ↔
Highlights by INFO, "Split [INFO]" hint, Picture Mode reopening on the wheel row, Midtone values cleared.
[Note](../research/OM5II-SPLIT-TONE-ROW-2026-11-28.md). **Step 3b done:** strength 0–10 and Tone Balance (907 / 911 / 915). **Open:** the row's own icon, hiding OM's
value label on the tint pages.

- **The row:** Split toning, under the colour wheel. INFO steps Shadows → Balance → Highlights. A bar shows the tint's
  colour. Hint "Split Tone INFO". On Balance only the bar shows, and the rear dial sets Tone Balance (−5..+5).
- **Ranges as on the OM-3:** strength 0–10 in half steps, 0 = off.
- **The wheel's Tint group goes away.** INFO on the wheel is then H / S / L only (phase 2).
- **Midtone Tint (deferred):** not offered on the camera for now. A Midtone value saved by earlier builds is cleared,
  so nothing applies that can't be seen. The engine code for it can stay if space allows, for when it comes back.
- **Image path:** unchanged, the camera-proven R/G/B curve route.
- **Main risk, the row itself.** An earlier row (`claude/split-tone-row`, 2026-11-19) worked in the emulator and was
  dropped at the owner's call on 2026-11-20. No technical fault is recorded.
  - An 18 Nov scratch test found that a row needs entries in more than the dispatch table and the row list
    ([Black / White note](../research/OM5II-BLACKS-WHITES-2026-11-18.md)).
  - The row record table holds 17 entries
    ([rows note](../research/OM5II-PICTURE-MODE-ROWS-2026-11-19.md)).
  - Start from that branch, and settle how rows are added once, because phase 4 adds three more.

### Phase 4: new image controls on the camera-proven R/G/B route

1. **RGB curves** row: five points per channel, −7..+7, into the R/G/B tables that tints and Black / White already
   write. It needs per-profile storage for 15 more values. Where they live is a research step: settings storage
   versus the card versus the heap.
2. **Color Mix** row: needs its own hook. The OM-3 moves R, G and B toward their neighbours while greys stay grey.
   Its E148 site is not located yet. Static trace first.
3. **WB Compensation row** in Picture Mode, on top of the existing per-profile WB.
4. **Sharpness −5 (off) .. +2**, as on the OM-3.

During parity these values are kept in the camera, per Color Profile. `LOOKS.BIN` stays version 1 until the
compatibility work below, so a look does not carry them yet.

### After parity: one look format with the other Caduceus projects (issue #4)

**Why later costs little:** the new controls copy the OM-3's ranges and meanings, and the shared panel already knows
the OM-3's versions of them (`tone_balance`, `rgb`, `mix`, `split`). Mapping them later should be a translation, not
a redesign.

**The aim:** a look made or shared for one Caduceus body opens on the others. That means one editor, the shared
Control Panel in [cakelesscoder/caduceus-ep7](https://github.com/cakelesscoder/caduceus-ep7), with the OM-5 as a
camera profile and an export target, instead of a third separate LookLab.

**Background:**
- The owner agreed on #4 on 18 Nov.
- The study is [SHARED-CONTROL-PANEL](../research/SHARED-CONTROL-PANEL-2026-11-18.md) (PR #10).
- cakelesscoder answered its five open questions on #4 on 23 Nov:
  - Contrast and Sharpness come from `advice`, and Shading from `vignette`.
  - Hue arrays are copied unchanged. The sign is still open for the OM-3 too.
  - The OM-5 target must refuse leading and trailing spaces in names.
  - The OM-3 films are already in the panel.
  - The preview has not been compared with an OM-5 photo.
- The OM-3 still has its own LookLab. Its roadmap lists one shared panel (its #71) as in progress.

**What the shared look format already has**, read from caduceus-ep7 `6b421a4` (`webapp/src/pack.ts`):

| Our control (this roadmap) | Shared field | In packs and share codes? | OM-5 `LOOKS.BIN` today |
|---|---|---|---|
| Hue, Lightness, Saturation ×12 | `hue`, `light`, `sat` | Yes | Yes (v1) |
| WB shift | `wb` | Yes | Yes |
| Shadows, Midtones, Highlights | `tone` | Yes | Yes |
| Black / White | `tone.blacks`, `tone.whites` | Yes | **No**: not part of a look yet |
| Split toning | `split`: Shadows and Highlights, colour 0..11, strength −5..5 | Yes | **No**. Ours also has a Midtone Tint, which the shared format lacks |
| Tone Balance | `tone_balance` | **No**: OM-3 bank looks only | No |
| RGB curves | `rgb` (5 points × R G B, −7..7) | **No**: OM-3 bank looks only | No |
| Color Mix | `mix` | **No**: OM-3 bank looks only | No |
| Contrast, Sharpness, Shading | `advice.contrast`, `advice.sharpness`, `vignette` | Yes | Yes |

**Steps:**
1. **OM-5 target in the shared panel, on today's file (OM5F v1).** This is the study's order:
   - A PR to caduceus-ep7 adding a `cameras.ts` profile and `targets/om5.ts` at `status: 'soon'`.
   - Byte-for-byte fixtures from `card/mklooks.py`: the starter looks, no WB, all extremes, a 12-character name, 10 looks.
   - An optional `LOOKS.BIN` import.
2. **Owner camera check** of one panel-exported `LOOKS.BIN`, with its SHA-256 recorded. Then the target goes `ready`.
3. **Point OM-5 users at the shared panel.** Switch the links in README, USING, FAQ and the site. Keep LookLab as a
   local preview and debug page, and keep `looklab/films.json` and the Python / JavaScript parity tests: release
   builds and tests depend on them.
4. **New fields go to the shared format first.** Before any phase 2–4 control is saved in a look:
   - Use the shared field where one exists: Black / White and split toning.
   - Open a "Look field" issue on caduceus-ep7 to promote Tone Balance, RGB curves and Color Mix from OM-3-only
     fields into packs and share codes, with neutral defaults. The OM-3 project should be part of that agreement too.
   - Then add an **OM5F version 2** record that carries them. The camera must keep accepting version 1 files.
5. **Shared open question:** the direction of + hue. One same-scene camera test here answers it for this body. The
   OM-3 and E-P7 projects have the same question open.

PRs and issues on the other projects go out only with the owner's go-ahead.

### Later (not scheduled)

- Looks kept in the camera's memory, so the card is needed only to bring in new looks.
- Super control panel dial stepping through the profiles and looks.
- A photo code in the JPEG, with LookLab reading it.
- Noise Filter and Vignette Correction rows.
- Midtone Tint: bring it back, as a shared field or as an OM-5 extra.
- Effects: Clarity (blocked on the Soft Focus weight), Glow, Halation, colour grain (shelved).

## Decisions (owner, 2026-11-28)

1. **Split toning:** its own row, as on the OM-3 (phase 3). The Midtone Tint is deferred.
2. **Ranges:** match the OM-3.
3. **Key map:** copy the OM-3 v0.41, including trash doing nothing on the wheel.
4. **Order:** feature parity first, then look compatibility (#4).

## Enablers already in place

- `OM5MOD/CADUCEUS.BIN` (PR #15): Picture Mode drawing code is loaded from the card, so UI work no longer competes
  for the last bytes of flash (`.ext2b` 390 bytes free, section 10 154). Emulator only.
- Background start-up (PR #15): controls are live without a half-press. Emulator only.
- The R/G/B curve route reaches live view and JPEGs on this camera (tints, Black / White).
