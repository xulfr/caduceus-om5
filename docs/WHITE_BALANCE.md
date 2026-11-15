# E148 per-Color Profile white balance

This is an emulator-tested port of the [OM-3 per-profile WB design](https://github.com/androidfanman/caduceus-om3).
It intercepts the E148 native settings commit at `0x602d19b6`, using the E148
stock getter (`0x602d000d`), UI writer (`0x60855cdc`) and active-setting accessors.
The overlay uses picture-mode setting 111: values 54, 55 and 56 identify Color
Profile 1–3. Other picture modes share a separate WB record.

Each record uses four part-1 cells: Color Profile 1 at IDs 904–907, Profile 2
at 908–911, Profile 3 at 912–915, and non-COLOR at 920–923. IDs 916–919 hold the first look slot's name
and index; 924–927 and 972–975 hold the other two look slots. A record holds WB mode, custom Kelvin, signed A/B and
G/M corrections, and an XOR check word. The first use of a profile inherits the
current WB configuration. Native tint tables and one-touch measurements remain
shared.

The commit gate sits in the section-2 tail at `0x605af780`. It checks section 6's initialization bit
(`0x20` of `0xa26e2694`) for the stock UI writer, then checks the armed state via `st_ptr` in section 2.
The armed WB body starts at `0x60829570` in section 4 and uses byte 12 of the allocated heap state block
to guard against nested commits. The same commit hook
also refreshes the effective settings after a Color Profile setting changes
(see the README). The refresh writes effective IDs 916–927 in part 0; the WB
records stay in part 1. In OM-Emu the 9/9 recall test covered first-use
inheritance, switching Profiles 1 and 2, custom Kelvin, and returning to a
non-COLOR picture mode. The part-1 ownership diff found no changes outside the
declared WB and H/L ranges during the exercised flow. It does not cover reset,
custom modes, backup/restore, live capture, or physical-camera persistence.
