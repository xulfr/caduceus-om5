# Arming in the background after start-up (2026-11-27)

**Emulator only (OM-Emu `bdb3347`). Not run on a camera.** Addresses are runtime addresses of the expanded E148 1.1
main program.

## Why

Until this change, nothing of Caduceus ran before the first shutter half-press (alpha7's rule, after the alpha5/6
boot loops). The patch then armed in the HLS_EVENT task. Start-up stayed stock, but the looks, the extra Picture Mode
controls and the profile's own settings stayed asleep until a half-press. The owner wants no half-press needed, and
fast start-up kept as the priority.

## What arming does, by risk (static, from hsl.s / films.s)

| Step | Where | Kind |
|---|---|---|
| `arm_gate` | ext8 | Allocates and clears the state block P (`malloc` `0x60023818`, the uncached `scheap_phyalloc` pool), then publishes its handle. Memory only. It required the HLS_EVENT task. |
| `arm_refresh` | ext10 | Repairs a stale profile number (`stock_ui_write`), then runs `pm_refresh` for contexts on a profile. **Writes settings.** |
| `fl_entry` | ext10 | Links the ND32/64 and Black/White / tint descriptors into the RAM descriptor hash. The link is idempotent: each id is checked with `desc_find`, and a node is filled before the one store that publishes it. Then it reads `LOOKS.BIN` once per power-on. RAM structures and a file read only. |

Writing settings at power-on is what hung the OM-3 Caduceus (caduceus-om3 `research/NOTES.md`, dr3–dr7: settings
written from the HLS_EVENT task, then from a worker, both hung, sporadically and with the dial moved while off). So
the settings-writing step stays with a user action.

## Design (`firmware/om5ii/boot.s`)

1. **Hook.** `FastEndCb` `0x601b1362` gets a 5-byte `jmp`. Its stock bytes are `cf 20 f8 fe fc`
   (`movm [a2],(sp)`; `add -4,sp`).
   - It is a callback entered by `calls` (the previous function ends at `0x601b135f`), and nothing branches into
     `0x601b1364..0x601b1367`.
   - OMKit's camera-run loader uses the same site. On OMKit's camera it runs about 1.2 s after power-on, once, after
     the live view (OMKit `docs/platform/om5m2/fw1100/patch.md`).
   - `bg_hook` saves d0, d1, a0, a1 and mdr. It creates the task (`acre_Task` `0x60051d5c`, priority 66, 2 KiB stack
     from the kernel pool), restores the registers, replays the two instructions and resumes at `0x601b1367`. It
     writes no memory of ours.
2. **Task `CAD_ARM`.** `bg_task` works through these steps:
   - It waits for `loaded_bits` `0xa26e2694` = `0x3ff`, polling every 100 ms for up to 30 s.
     - This is the finaliser's word, set after decompression and constructors (`0x600465be`, see
       [startup fix](OM5II-STARTUP-FIX-2026-11-06.md)).
     - OMKit waits on `0xa26e2698`, which is set when a section's load request returns (`0x600464bf`); that is earlier.
   - It ends if the patch is already armed or OK is held (`0x60130fb8` with code 4 → 0). In both cases the half-press
     path arms as before.
   - It waits for the HLS event manager's task id (the handle word lives in that object's padding, as `arm_gate`
     checks).
   - It calls `arm_alloc`, `arm_gate` after its task check, and sets P+16 (`ST_PEND`).
   - It waits up to 10 s for a medium to read MOUNT OK, then runs `fl_entry` and `cb_load` (the
     [card block](OM5II-CARD-BLOCK-2026-11-27.md)).
   - Every path ends with `ext_tsk` `0x6003167e`.
3. **First half-press.** `ext_halfpress` now points to `hp_entry`. While `ST_PEND` is set it clears it and runs
   `arm_refresh`, in the HLS_EVENT task as before. Then it runs `fl_entry` and `cb_load` (both no-ops once done).

## What changes for the user

- **Soon after switch-on:** a second or two after the live view, the extra Picture Mode controls, looks (trash on
  the mode strip) and the page graphics work without a half-press. The `bg-look-without-halfpress` case shows a look
  applied with no half-press.
- **Before the first half-press:** the profile's one-time catch-up refresh still runs at the first half-press, which
  precedes every photo. Profile values set in a previous session stay in the effective settings over power-off, so
  photos are unaffected.
- **OK held at switch-on:** this skips the background arming; the half-press then arms. This is a way back if the
  background path ever misbehaves.

## Emulator results (`tests/run_boot_arm.py`, 11 cases, all pass)

OM-Emu does not run E148's `FastEndCb` and does not publish the section bits itself (`sess.mjs --ready` does). It also
runs only firmware tasks its lab allows. `tests/boot_pre.mjs` therefore calls `bg_start` as the hook would, then allows
the new task.

| Case | Result |
|---|---|
| Background arm | Armed, refresh pending, `LOOKS.BIN` loaded (4 looks), card block loaded, no half-press |
| Look without a half-press | Trash on Color Profile 1 applies look 0 |
| Then a half-press | Pending refresh run and cleared |
| No card | Armed. `LOOKS.BIN` not tried after the 10 s wait; the half-press tries again |
| No / other-build / damaged block | Refused (state 2, no entry table) |
| Half-press only (task not started) | As before boot.s: armed at the half-press, block loaded |
| Neither | Stays unarmed |

## Not established (camera only)

- That `FastEndCb` runs on every power-on of this build, and when. Also whether it runs after sleep or on the
  updater path; the armed check and OK bypass cover a second run.
- Start-up timing and feel, with and without a card, with a slow card, and on the start-up paths OMKit lists as
  unverified (Wi-Fi, USB).
- Whether arming about 1–2 s after the live view, then UI hooks becoming active while the GUI starts, is free of the
  OM-3's sporadic start-up hangs. Those hangs came from writing settings at power-on, which this design does not do.
  Their remaining cause was never found.
- A race between the background arm and a very early half-press is unlikely. If it happens, a second state block is
  allocated and the first leaks (about 1.5 KB until power-off). Each path re-checks `st_ptr` first.
