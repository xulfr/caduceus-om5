# OM-5 Mark II alpha3 audit and alpha4 fixes

Reviewed `fecc12954125714028605bb2317abfd9707cdc2b` (alpha3), E148 firmware 1.1 build 1100.
The host suite reproduced all three existing releases before changes. This audit covers the patch's
assembly, startup gates, look loading and settings writes, installer output, declared byte ranges,
native loader bounds, release reproduction and bounded OM-Emu regressions. It is not a camera test.

## Findings and reproductions

| Finding | Alpha3 reproduction | Alpha4 change |
|---|---|---|
| Look names were interpreted as camera display commands | A valid bank with name `@A034@` loaded and drew a trash icon in the title. Both public writers accepted it. The new `name-markup` rejection case failed with load state 1 instead of 2. | Reject `@`, control and non-ASCII bytes in the twelve displayed name bytes before applying any look. Both writers reject `@`. The string getter substitutes `?` for unsafe bytes in already-saved names without rewriting their cells. |
| Look title lost after returning from lower rows | Two looks with identical values but different names produced identical frames after returning to the strip and pressing Delete twice (`row-return-title`). The existing row-return test checked settings only. | Restore the named slot's title id in the controller's RAM row descriptor before layout, only for row kind 4 and an armed Color Profile. Keep the existing repaint invalidation. |
| Installer reruns erased custom look banks | A temporary `card/OM5MOD/LOOKS.BIN` containing custom data was replaced by the release's starter bank. | Preserve an existing look bank and report that it was kept. Fresh outputs still receive the starter bank. |
| Installer could publish an update without preparing recovery, and wrote directly over existing files | Making `card/restore` a regular file caused alpha3 to raise `FileExistsError` after publishing `DCOLYMP/E1489999.BIN`. Its direct `write_bytes` also truncates an existing destination before the write finishes. | Prepare recovery first and publish the install last. Write through a temporary sibling, flush and sync it, then replace the destination. Fault-injection tests verify that failed writes preserve an existing complete image and that recovery failure prevents a new install from being published. |
| Mac launcher reported success after a patcher failure | With a Python stub returning 23 and a newline for the closing prompt, alpha3's launcher returned 0 under Bash. | Save and return the patcher's status; alpha4 returns 23 in the same check. Keep `.command` files at LF line endings. This is a Bash launcher check under WSL, not a macOS desktop test. |

These are confirmed display/data-handling defects. The name test demonstrated an icon substitution, not a
crash or a boot loop. No new cause of a physical boot failure was established.

## Build and checks

Alpha4 package: **90,832,896 bytes**, SHA-256
`590c2959206e8e06f5ab12efe4635f6674ac69e20879012e55ec6a798713d648`.
The release contains authored byte edits and a starter bank, not OM firmware.

- The source record step ended with a strict build using GNU MN103 binutils 2.43. Hook preimages,
  declared ranges, compression, component hashes and package checksums passed.
- The independent [build audit](../tests/alpha4-build-audit.json) found exactly 1,020 changed expanded-main
  bytes relative to alpha3, all in declared sections 6, 7 and 10. Section 7 changes two branch-operand bytes.
  Native loader descriptors, section ends and the resource component are unchanged. The modified tails
  retain 416, 192 and 936 bytes of space respectively.
- The Live ND selector passed 768 inputs, and the audited image contains those exact tested selector bytes.
- The look/menu suite has 19 cases: all 15 alpha3 cases plus row-return title, display-command rejection,
  control-byte rejection in the final record, and unsafe names previously saved by older releases.
  The persisted-name case checks all three label-id families and verifies no rewrite of saved name cells.
  Results are in [alpha4-results.json](../tests/alpha4-results.json).
- Startup fault injection exercises all 1,023 incomplete section masks, invalid or mismatched task IDs,
  a failed task query, null allocation and retry, state-clear bounds and handle bounds. These checks call
  the actual arming code, with task lookup and allocation outcomes controlled by the test. The real
  loader and its scheduling are not emulated. Its image-store counts equal the matching stock session.
- The default installer selects alpha4 and produces the recorded package, an exact copy of the pinned
  E148 stock restore and the release's starter bank. Host tests also reproduce all earlier releases.
- Host suite: 17 tests, 16 passed and the E144 built-output test explicitly skipped (this audit targets E148).
  Generated site pages and local links pass. Emulator revision: `bdb33470705b3be28db52cbe080c31d74db727d8`;
  Node: 26.13.0; host Python: 3.10. The firmware build uses WSL Python and binutils.

## Repeating the checks

From the repository root, with `OM5_STOCK` set to the pinned official E148 file and the MN103 tools on PATH:

```sh
bash tools/dev/build.sh generated/alpha4-record --record
python tools/mkrelease.py v0.1.0-alpha4 generated/alpha4-record/strict "$OM5_STOCK"
python tests/audit_build.py --build generated/alpha4-record/strict --previous generated/alpha3-record/strict --stock "$OM5_STOCK" --out generated/build-audit.json
python -m unittest discover -s tests -v
python tests/run_emulator.py --emu generated/om-emu --build generated/alpha4-record/strict --stock "$OM5_STOCK" --out generated/new-regressions
```

The first two commands are for recording a deliberate source revision; use the strict builder without
`--record` for ordinary verification. Preserve the starter bank from alpha3 when creating alpha4.
See [tests/README.md](../tests/README.md) for the separate startup probe. Use new output directories.

## Remaining limits

No camera has run alpha4. Three earlier versions caused boot loops. Physical startup, the second processor,
cache behaviour, capture-time settings ownership, real settings persistence, image processing, ND32/64
exposures and recovery remain unverified. `camera_tested` stays false and the `UNTESTED` gate remains.

The super control panel still has no Color Profile cell icon in OM-Emu; its name is visible and checked.
This known cosmetic issue is logged here as open, not presented as fixed. The original OM-5 pre-alpha
guide remains pinned to its alpha2 donor revision; this audit does not change that candidate.
