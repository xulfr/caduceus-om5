# OM-5 Mark II alpha4 audit and alpha5 fixes

Reviewed `d85fbbb` (alpha4), E148 firmware 1.1 build 1100, before a first camera test. Before any change the
strict source build reproduced the alpha4 package `590c2959…d713d648` and the host suite passed (16 pass, the
E144 built-output check skipped). The review covered films.s, hsl.s and wb.s (call/ret frames, register
preservation, heap-block bounds, setting IDs, task interplay), the stock code each new store writes into,
patch.py, the launchers, LookLab and the Python writer. This is emulator and static work, not a camera test.

## Findings

| # | Finding | Alpha4 reproduction | Alpha5 change |
|---|---|---|---|
| 1 | `pg_title` (added in alpha4 to keep a look's title after returning from the lower rows) stored the title id with a 32-bit `mov`. Stock reads the RAM row descriptor as halfwords: u16 +0 kind, u16 +4 title id, u16 +6 the title's style index, which `direct_layout` reads for every row kind at `0x60f05459`. The store zeroed +6. | A probe at the updater's last call (`0x60dad5f5`) and after `pg_title` showed +6 change from 1 to 0 on every layout of a named slot. The new `layout_guard.mjs` check fails on alpha4 in `title-redraw` and `next-film`. | 16-bit accesses only: `movhu d3,(4,a0)`; the kind is read with `movhu` as stock does. The guard runs in every emulator case. |
| 2 | A look without a WB shift kept the shift left by the previous look. LookLab previews such a look with no shift, so the camera's result depended on stepping order. In the starter bank Portra 160 inherited Portra 400's +1/+1 and Kodachrome64 inherited Ektar 100's −1/0. | `next-film` (Portra 400 with 3/−2, then Velvia 50 without a shift) with the new WB assertion: alpha4 fails `slot 0 WB shift record` (3/−2 kept). | A look without a shift writes 0/0 to the current WB mode's A/B and G/M, through the same UI writer and wb.s record path. LookLab, USING and FORMATS say so. |
| 3 | Comments and guides disagreed with the code. hsl.s named 690 as the effective midtone (the code uses 691) and listed 383/691/382 as Highlight/Shadow/Mid. USING and FAQ still described the generic "Picture Mode" title for every slot after returning from the lower rows. | Stock groups 383/382/691 as the user tone trio (e.g. `0x60e4a437`, `0x60eb0347`). In OM-Emu the camera's own tone editor changed 978 for **Sh** and 977 for **Mid**, so 976/977/978 + 3p are Highlights/Midtones/Shadows → 383/691/382. films.s and FORMATS were already right. | Comments corrected (no byte changes). USING and FAQ now say a slot holding a look keeps its name; only an empty slot reads "Picture Mode" there. |

**Severity.** Finding 1 had **no visible effect in OM-Emu**: for this row kind, style indices 0 and 1 resolve
to the same style word (0x0d in all six rows of the table at `0x6124aedc`), and the icon branch that also reads
+6 is only taken for kinds 3 and 12. Alpha4 and alpha5 frames are pixel-identical in the probe run. It was still a
write into stock state outside the intended field, and stock refreshes the descriptor before each layout, so
it was transient. Finding 2 changes what a look does: owners who want looks without a shift to leave the
camera's shift alone should say so, and the step can be changed back.

A "Reset OK-hold" hint appears on the strip after a look step. It is identical in alpha4 and alpha5 and is not
caused by either fix. It was not investigated further.

## Checked, not defects

- The look writer's saturation writes go to the stock UI writer `0x60855cdc` directly. The hue/lightness
  write hook replaces only the editor's call at `0x6091c6bd`, so a wheel left on Hue or Lightness cannot
  divert them.
- The title label's last-laid-out id (+130) is a 16-bit field in stock (`movhu` at `0x60d91bbe` and others);
  the existing `movhu` invalidation is correct.
- Every call into films.s and hsl.s helpers matches its `ret` register list and frame, and every function
  that makes calls keeps its locals clear of `(0,sp)`.
- The heap block holds the state (0..67), names (68..145) and the bank read (152..984) within 1024 bytes.
  The read is at most 833 bytes, so a trailing byte is detected.
- `fl_check` validates all 47 used record bytes and the twelve displayed name bytes; fread errors fall
  through as oversized.
- patch.py, the launchers and the writers: no new defects found. By inspection the patcher's import path
  uses nothing newer than Python 3.8 (walrus, `unlink(missing_ok=True)`); it was not run on 3.8 here.

## Build and checks

Alpha5 package: **90,832,896 bytes**, SHA-256
`98bd2433bef76706f4c71706439feb23d05524477b4d078135c1675ab97880c2`. The release holds authored byte edits and
the starter bank (byte-identical to alpha4), not OM firmware.

- Toolchain: GNU binutils 2.42 built for `mn10300-elf` from the Ubuntu orig tarball with the handover's
  configure flags. Python 3.13.18, Node 22.23.4, OM-Emu `bdb33470705b3be28db52cbe080c31d74db727d8`.
- `OM5_STOCK=... bash tools/dev/build.sh WORK --record` re-recorded ext6, ext7 and ext10 and ended with a strict
  build. A second strict build after the comment-only edits gave the same package.
- `tests/audit_build.py` against alpha4: 417 changed expanded-main bytes, all in declared ext6 (3), ext7 (1)
  and ext10 (413). Native loader bounds and resources unchanged; the ND selector passes 768 inputs. Tail
  space left: 416, 192 and 926 bytes. Evidence: [alpha5-build-audit.json](../tests/alpha5-build-audit.json).
- Emulator: see [alpha5-results.json](../tests/alpha5-results.json). Startup fault injection
  (`tests/startup_assert.mjs`, arming entry unchanged at `0x613f2f7f`) passes; its image stores equal the
  matching stock session.
- Host suite with `OM5_STOCK`: 17 tests, 16 pass, the E144 built-output check skipped. Release reproduction
  covers alpha1 to alpha5. patch.py now selects alpha5 and wrote the recorded package, a byte-exact copy of
  OM's 1.1 as the restore file and the starter bank.

## Repeating the checks

From the repository root with `OM5_STOCK` set to the pinned E148 file and the MN103 tools on PATH:

```sh
bash tools/dev/build.sh generated/alpha5-strict
python tests/audit_build.py --build generated/alpha5-strict --previous generated/alpha4-strict --stock "$OM5_STOCK" --out generated/build-audit.json
python -m unittest discover -s tests -v
python tests/run_emulator.py --emu generated/om-emu --build generated/alpha5-strict --stock "$OM5_STOCK" --out generated/alpha5-regressions
```

`generated/alpha4-strict` is a strict build of `d85fbbb`. Use new output directories.

## Remaining limits

No camera has run alpha5. Three earlier builds caused boot loops. Physical startup, the second processor,
cache behaviour, the real loader, settings persistence, image processing, ND32/64 exposures and recovery
remain unverified. `camera_tested` stays false and the `UNTESTED` gate remains. The super control panel's
missing Color Profile cell icon in OM-Emu is still open.
