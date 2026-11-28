# Bird detection autofocus on the OM-5 Mark II: feasibility (2026-11-28)

**Research only. Nothing built, nothing run.** The owner asked whether bird-detect AF is viable here, having heard it
was done on the E-M5 III and recently on the OM-5 II in the Korean "db firmware".

## What others have done

### E-M5 III notes (nsud-dev/olympus-firmware-notes)

Read at `4adfbf1`: `docs/features/subject-detection*.md`, `af-detect*.md`, `docs/hardware/soc-overview.md`,
`image-engine.md`. Docs are CC BY 4.0, tools MIT.

- **Their own detection network on the camera's image engine.** The engine is the pixel-processing unit that develops
  RAW files; the main CPUs hand it short "jobs". The engine program and the network are their own, with no Olympus code.
  - About 14 ms per 480 × 480 pass, and 35–41 passes a second beside live view, **on their E-M5 III** (test firmware).
- **Their own bird model.** It is trained on public picture sets, Open Images V7, COCO 2017 and CUB-200-2011, the last
  research-use only.
  - On 8,000 test pictures it scores body 0.68 (the E-M1X network 0.71), head 0.60 (0.51) and eye 0.26 (0.15).
  - About 1 in 15 bird-free pictures shows a false bird; the E-M1X network shows 2 in 5.
  - A cat / dog model also exists.
- **AF follows a detected bird in C-AF on their camera.** Tracking and re-finding a lost subject are not finished.
  Their status: "research in progress".
- **Not published:** the engine program, the models and the AF integration are not in the repository, only the
  documentation. They also used the E-M1X's own job as a benchmark and say they will not publish or ship it.

### db firmware (azqeurio/om-c-firmware)

The GitHub release notes were read up to **v0.4.6b (27 Nov 2026)**.

- **No release mentions bird, animal or AI subject detection for any body, the OM-5 II included.**
- The only subject-detection item is the OM-1 "v0.4 Alpha" pre-release, a port of OM-1 Mark II features onto the OM-1
  ("added person to subject detection; CAF + TR merged"). The OM-1 has its own detection hardware.
- An OM-5 II result may exist outside those release notes, in forums or posts. It was not found here; the owner may
  have a link.

## What the OM-5 Mark II has (from the notes, static)

| | OM-5 II (E148 1.1) | E-M5 III 1.7 |
|---|---|---|
| Chip | One "dc13" chip, the same as the E-M5 III and E-M1 III as far as the firmware shows. It runs the OM-5's image-engine jobs unchanged. | One dc13 chip |
| Memory | About 1 GB | About 1 GB |
| Stock detection | **Dormant code**: the "master half" of the E-M1X design (picture sender, subject list, AF-point setters). No network or weights. The menu offers face / eye only. | None |
| Face / eye detection | Yes, the same as the E-M5 III | Yes |

The E-M1X runs its bird network on the image engine of a second dc13 chip. The OM-5 II has one dc13 chip, like the
E-M5 III. So the E-M5 III result is the relevant one: one chip did fit a detection network beside live view.

**The OM-5 II's dormant subject list and AF-point setters may be a cleaner AF entry than the E-M5 III had.** It
would mean feeding detections into OM's own path rather than adding a new one. This is an inference, not traced.

## Verdict

**Technically plausible, but a large research project, and not one this project can start from published parts.**

What makes it plausible:

- The same chip and memory as the E-M5 III, where detection runs at a usable rate and AF follows a bird (their camera).
- OM's dormant subject-AF plumbing on the OM-5 II.
- Our card block now gives room for code. The network's weights (about 1.4 MB int16 per E-M1X-sized network) would
  also have to come from the card into unused DRAM. The gap past resource record 0 is about 3.2 MB, and `0xa3700000`
  is already taken by our block.

What it would take, each a project of its own:

1. **An image-engine program.** Image-engine jobs are a separate instruction set, decoded by atx (fenykl project, on
   the E-M10 II) and extended in the E-M5 III notes. None of that tooling is in our repo. This is new territory for
   Caduceus, entirely beyond the MN103 CPU code we write now.
2. **A model.** Training pipeline, data with a licence that allows shipping (CUB-200-2011 does not), int16
   calibration, and accuracy checks. The alternative is to ask the E-M5 III notes' author whether their model and
   engine program could be shared. That contact is the owner's to make.
3. **Feeding live-view frames to the engine and results to AF** on E148: tracing the dormant sender, the subject list
   and the AF-point setters, plus the frame timing beside live view.
4. **Display.** The subject frame (white, green when in focus) and the eye mark, on the OSD.
5. **Camera-only validation throughout.** OM-Emu runs neither the image engine nor AF, so almost nothing here can be
   checked in the emulator. Each step is a camera round.

## Recommended next steps (research, no build)

1. **Static trace (small):** on E148, the dormant subject-detect path (sender stub, subject list, AF-point setters).
   Record addresses, and whether a detection list written there would move the AF point. The E-M5 III notes' technical
   page names the E-M1X / OM-5 II functions to start from.
2. **Owner contact (optional):** ask the E-M5 III notes' author whether their engine program and bird model could be
   shared, or ported jointly. Ask the db firmware author whether an OM-5 II bird-detect build exists.
3. **Only then** decide whether to start the image-engine work. That is the largest piece.

## Not established

- Whether any OM-5 II bird-detect build exists (db firmware or elsewhere).
- Whether E148's dormant subject list really drives the AF point when filled.
- Image-engine headroom on the OM-5 II beside its own live-view jobs. The chip matches, but the OM-5 II's live-view
  load was not measured.
