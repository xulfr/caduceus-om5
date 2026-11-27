# Can the GPU (c3d) draw our wheel and curve? (2026-11-27)

**Static analysis of the stock E148 1.1 image, plus a review of third-party tooling. Nothing was run on a camera, and
the GPU probe was not run in OM-Emu (see "Emulator probe").** Addresses are runtime addresses of the expanded main
program, base `0x60021020`.

## Question

Our colour wheel, tone curve and Monochrome filter ring are drawn on the CPU. They use OM's OSD pen
(`gfx_wheel`, `gfx_tone`, `gfx_filter`; about 1–1.5 KB of code; see the
[WIP UI3 note](OM5II-WIP-UI3-2026-11-16.md)). Can the stock vector GPU (c3d, a DMP OpenVG library) draw them instead?

## The GPU tooling on record

The Atlas (`knowledge/subsystems/display.md`, `knowledge/emulation/coverage.md`) points to the E-M5 III notes
(nsud-dev/olympus-firmware-notes, revision `4adfbf1` reviewed here):

- `tools/om-emu-c3d/patches`: 11 OM-Emu patches. 0001 shows the 32-bit IMG plane c3d draws into.
- `tools/om-emu-c3d/c3d`: `c3drun.mjs` runs the camera's c3d tasks. `c3dvg.mjs` is a JavaScript stand-in for the
  OpenVG/EGL library.

This is **not GPU emulation**. It runs the camera's own c3d code against a software OpenVG stand-in. With it, the
stock Color Creator, ART and Part Color screens drew on the E-M5 III 1.7, in the emulator only. OM-Emu itself
(`xulfr/om-emu` `bdb3347`) has no GPU or C3D model; its roadmap lists the GPU as not started.

## What the E148 c3d has (observation, static)

- The kind-name table at `0x60f57128` (strings from `0x60f570ac`) still lists all nine names: PART_COLOR,
  COLOR_CREATOR, COLOR_CREATOR2, MONOCHROME_CREATOR, SHADING_CONTROL, ART_FILTER, TOUGH_GEAR, SCN_TOP and
  SELECT_SHOOTING.
- `c3d_exe` START at `0x60cceaa0` dispatches on byte 0 of the block, the kind, 1-based. It accepts only these:

  | Kind | Name | Work buffer | Branch |
  |---:|---|---|---|
  | 1 | Part Color | 7 MB | `0x60cceabc`, two variants chosen by `0x6005faa9` |
  | 2 | Color Creator | 7 MB | `0x60cceb01` |
  | 6 | ART | 12 MB | |
  | 8 | Scene top | 10 MB | |
  | 9 | Select shooting | 10 MB | |

  Any other kind goes to the error path at `0x60cceb72`.
- **Missing:** Color Creator 2, Monochrome Creator, Shading Creator and Tough Gear. On the E-M5 III those are the four
  kinds with **empty renderers**. The notes' "own renderer" route plugs into one of them, and the E-M5 III profile
  editors draw through Color Creator 2 / Monochrome Creator that way, as proven on that camera.
- **Discrepancy with the notes.** The notes' table (docs/hardware/c3d-gpu.md, "Other bodies") gives the OM-5 1.2 /
  OM-5 II 1.1 five kinds as "no CC, CC2, MC, SC". On E148 the START switch keeps Color Creator (kind 2) and drops
  Tough Gear instead. This was read from the START switch only; the per-kind DRAW renderers were not traced. Worth a
  scoped Atlas note.
- **Consistent with the earlier finding** ([WIP UI3](OM5II-WIP-UI3-2026-11-16.md)): E148 has no `DRAW_PROFILE` and no
  profile kind. The GUI's various-draw names at `0x60b93876` still include COLOR_CREATOR2 and MONOCHROME_CREATOR, but
  c3d no longer serves them.

## What this means for replacing our drawing (inference)

1. **The stock kinds cannot show our data.** On the E-M5 III, Color Creator's update is 4 bytes (one hue / saturation
   cursor) and Part Color's is 4 bytes (one hue). Our wheel shows 12 independent values per axis (−7..+7) plus
   tints. Our tone page shows a five-control curve; the filter page shows a ring of eight swatches. A stock kind could
   at most be a backdrop behind our marks.
   - Its fixed layer position on the E-M5 III is Color Creator 256² at (432, 112) and Part Color 192² at (500, 144).
     Both clash with our layout: the wheel centre is (290, 222) and the labels are on the right.
2. **No empty kind to plug into.** Our own OpenVG renderer would have to take over Color Creator's (or Part Color's)
   renderer while a Color Profile page is open, and give it back otherwise.
   - `c3d_exe` runs on **CPU 1** on the camera, so our renderer would run there too.
   - It would read our state through the uncached alias, which is the cross-CPU cache issue `st_ptr` already guards
     against.
   - It would need the start / update / end sequence from the GUI, which the restored pages never send.
3. **Little or no space saved.** A renderer that builds paths and paints is unlikely to be smaller than the block
   drawing it replaces (`gfx_wheel` about 0.5 KB in section 5). The request plumbing adds more. The real gains would be
   looks (antialiased arcs, colour) and escaping the OSD command-buffer limit (about 1,000 commands per repaint).
4. **Risk.** New code on CPU 1, a GPU path OM-Emu cannot run, and a camera test as the only proof. This is the
   boot / reset class of risk this project has hit before.

**Recommendation:** keep the CPU-drawn graphics. Revisit only if the look of the wheel becomes a priority. If so, the
first step is a static trace of the Color Creator kind's renderer and its GUI request on E148 (view `0x60df1605`,
data block 278), not an emulator port.

## Emulator probe (not run)

- The notes' patches 0001–0003 do not apply to `xulfr/om-emu` `bdb3347`. They target upstream `ccfe2e0`, and
  `display.mjs`, `vsc.mjs` and `vsccompose2.mjs` have diverged. 0004 was not checked.
- `c3drun.mjs` and `c3dvg.mjs` hard-code about 60 E-M5 III 1.7 addresses: the c3d tasks and queues, the CPU-1 task
  bodies, the resource reader, the DMP driver task and every OpenVG / EGL entry. The notes found the same library and
  name table on E148 (vgDrawPath `0x613dacf3`), so the library side could be mapped by name. The task and queue side
  needs its own trace.
- Porting both would take days, and it would answer only point 2 above in the emulator, with a stand-in GPU. The
  static result already settles point 1, so the port was not started.

## Not established

- Which E148 GUI screen starts kind 2, and with what block. Views `0x60df1605` (block 278, Color Creator) and
  `0x60dfaf61` (block 279, Partial Color) make draw requests, per WIP UI3.
- Whether the E148 renderers for kinds 1 and 2 match the E-M5 III's.
- Anything on a camera.
