# OM-5 Mark II 1.1 (E148): how the Picture Mode screen repaints

Found on 2026-11-14 with OM-Emu call traces (`tools/dev/calls.mjs`, `tools/dev/calltree.py`). **Emulator
observations only.** Addresses are runtime addresses of the expanded main program, firmware 1.1 build 1100.

## The path of a key press (screen state 0x0418)

1. The GUI task's loop dispatches events through `0x60d41952`. A key is an event (`0x9008` left, `0x9016`
   trash, …) that reaches the screen's action table and then `screen_forward` (`0x60ed5c18`).
2. `screen_forward` loads the screen object from the global `0x61e588f4` and calls its handler `0x60ec8d94`.
   The handler passes the command to the widget tree (`(0,screen)`, vtable entry 0). If that returns 1 (a value
   changed) it calls the **panel updater**: the object at `(4,screen)`, vtable entry 0 (`0x60e49c2b`).
3. The panel updater rebuilds the screen's data blocks and stores them with `0x60d42f31(d0 = block id,
   d1 = size, a0 = data, a1 = 1)`. Block `0x115` (252 bytes, at updater + 16) describes the highlighted row.
   Storing a block marks it dirty for its listeners and posts event `0x1900` to the window (`0x60d521db`).
4. On `0x1900` the window sends `0x1901` to its children. The page controller (`0x60dad480`) fetches its
   children 14 and 15 (`child_get`, `0x60dad302`) and calls `direct_layout` (`0x60f05251`), which hsl.s already
   wraps at `0x60dad5f5` (`pages_hook`). `direct_layout` gives child 15, the title label, its string id with
   `0x60f04cda` → `0x60d91c97`.
5. A widget that changed invalidates itself (`0x60d49294`), which posts the paint event `0x1002`. The label's
   paint (`0x60d921c7`) asks the string getter (`0x60d52ed5`) for its text then.

## Why a film step did not repaint

- Stepping a film from the trash handler changed settings but never ran step 2's panel updater, so nothing was
  posted. Forwarding `0x900c` or rewriting setting 111 does not reach it either.
- The title label keeps the string id it last laid out at `+130` (u16). `0x60d91c97` returns early when the new
  id equals it. A film step keeps the id (2749 "Color Profile 1" …) and only changes what the getter answers, so
  the label was never invalidated. The first step on a slot appeared to work only because the "Reset OK Hold"
  mark was shown beside it and its region was painted too.
- The text is fetched at paint time, so running the updater twice (stock title, then film) inside one handler
  changes nothing: the label sees the same id both times.

## What films.s does now

- `fl_delete` ends by setting `FL_DIRTY` (state block P + 67) and calling the panel updater exactly as the
  screen handler does (`(scr_obj)` → `(4,·)` → vtable entry 0).
- `pg_title` (section 6, called first in `pages_hook`) consumes `FL_DIRTY`: it sets the title label's stored id
  (child 15, `+130`) to `0xffff`, so the `direct_layout` that follows lays the same id out again and the label
  invalidates itself. No other widget is touched; without the flag the hook is stock behaviour plus one test.

## The highlighted row

Updater object + 136 (block `0x115` + 120) is the kind of the highlighted row's control: **4** on the Picture
Mode row (the strip of modes), 0 on the colour wheel, tone, Shading, Sharpness and Contrast rows (those set
`+20 = 4`, a slider, instead). `+140` is the title's string id for the Picture Mode row: the mode's name on
entry, 203 ("Picture Mode") after coming back from the lower rows. `fl_delete` steps a film only when `+136`
reads 4. In the colour wheel the container consumes the press first (axis switch), as before.

## Super control panel

The panel's top line is the highlighted cell's name through the same string getter, so it shows the film's
name while the Picture Mode cell is highlighted. In the emulator the cell itself draws no icon for a Color
Profile; not investigated.

## Not established

Everything above is OM-Emu behaviour. Whether the camera's GUI task, heap and event queue behave the same
under real timing is not known. No camera has run this code.
