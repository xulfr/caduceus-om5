# E148 1.1 static analysis

This tooling reads firmware; it does not build, patch, install or flash it. Keep
stock, expanded images, Ghidra projects and reports in ignored `generated/`.
Python 3.10+ is required for the host tools. Ghidra scripts use bundled Jython.

## Install (PowerShell, Windows)

1. Install a Java 21 JDK, e.g. Eclipse Temurin 21, and set `JAVA_HOME` to its
   installation directory. Verify `& "$env:JAVA_HOME/bin/java.exe" -version`.
2. Download the official [Ghidra 11.4.2 release](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_11.4.2_build),
   verify the release checksum, and extract `ghidra_11.4.2_PUBLIC_20250826.zip`
   into an installation directory. Set `$ghidra` below to that directory.
3. Install the processor module at the pinned revision, using the
   [upstream installation procedure](https://github.com/nsud-dev/ghidra-mn103/blob/01fc3928802d227b2d5f06b83f40543ecbe92f40/README.md).
   From this repository root:

```powershell
$ghidra = 'C:/Tools/ghidra_11.4.2_PUBLIC'
python -m pip install PyYAML==6.0.3
git clone https://github.com/nsud-dev/ghidra-mn103.git generated/ghidra-mn103
git -C generated/ghidra-mn103 checkout --detach 01fc3928802d227b2d5f06b83f40543ecbe92f40
Copy-Item -Recurse generated/ghidra-mn103/MN103 "$ghidra/Ghidra/Processors/"
& "$ghidra/support/sleigh.bat" "$ghidra/Ghidra/Processors/MN103/data/languages/mn103.slaspec"
git clone https://github.com/xulfr/om-firmware-atlas.git generated/atlas
git -C generated/atlas checkout --detach f36e141d5ad4f069381218ce0495230c84a9be60
```

Use a fresh MN103 destination to avoid mixing module revisions. This module's
documented profile is Ghidra 11.4.2 / Java 21; it is not evidence of an E148 import.
On Linux use `support/sleigh`, `support/analyzeHeadless` and `cp -R` instead.

## Generate reports and import

```powershell
$env:OM5_STOCK = 'C:/Private/E1489999.BIN'
python tools/space_map.py
python tools/symbols_export.py --atlas generated/atlas
python tools/ghidra/headless.py --atlas generated/atlas --ghidra $ghidra --analyze
```

The stock BIN must match the full pinned SHA-256
`9de5d77e1d290fa2ed4ebc7d75cee0ed490befbc89566722467d1d421d66d637`.
No firmware is downloaded by these scripts. Symbol export requires local Atlas
records and fails if missing. Conflicts remain in JSON and produce exit code 2;
the importer refuses them. Input hashes retain provenance. The module revision
and Atlas revision above were inspected on 2026-11-18.

`space_map.py` decodes component 0x100 with `oly_container` / `oly_compress` and
uses `om5ii_boot_audit.loader_regions` to validate the native descriptor table,
end selector and expanded-stock hash. Its JSON lists every uniform 00/FF run
inside the ten loaded ranges (including one-byte runs), every all-alignment
absolute LE32 pointer hit, each manifest range, and used/candidate-free counts.
The text summary is under 40 lines. `--min-run 16` is an optional smaller report;
it excludes short runs. `--built PATH` accepts an expanded main of the same size
and reports changed bytes, including changes outside declared manifest ranges.
Region capacities stop at the next overlay or the native loaded end.

**Candidate free bytes are not a placement approval.** Uniform zeros can be
live data. Absolute pointer matches are retained even when they might be
coincidental instructions or end bounds (e.g. ext10). Space-map schema 2 reports
each pointer target as a one-byte `reference_ranges` interval, preserves all
source hits, and subtracts that interval together with declared patch usage.
It also reports the remaining `candidate_free_ranges` within referenced runs.
A pointer establishes an address, **not the pointee's extent**; those extents
remain explicitly unknown. Hits inside already-used code do not erase a free
tail: the baseline manifest now reports ext5 = 184 and ext10 = 190 candidate
free bytes. Relative branches, computed pointers, table extents and runtime
ownership need separate review. No static dword scan proves their absence.
File offsets identify the encoded BIN section starts; compressed sections have
no linear address-to-file mapping. Expanded stream spans can exceed loaded ends.
In particular, the pinned Atlas section-7 record gives `0x61343800` as its end;
that is the expanded stream span, while the native loaded end is `0x612a5000`.
The exporter preserves that source label; the importer uses the native map.
The exhaustive one-byte-run JSON can be large (about 486 MB for this stock).
Use `space-map.txt` for routine reading and `--min-run 16` for a smaller targeted
report; neither report authorizes placement without a reference/ownership audit.

`headless.py` repeats input validation, writes private inputs under
`generated/ghidra/` (including a small loader-only map), and imports with
language `MN103:LE:32:AM33-2`. The pre-script
replaces BinaryLoader's whole-file block with the ten native loaded sections.
It additionally maps the prefix from `0x60021020` to section 1 as
`resident_prefix` for boot/allocator analysis; that analysis convenience does
not make the prefix a free-space region. Inter-section padding and the suffix
are unmapped. Symbols outside mapped memory are labels only. No label is
automatically declared a function. Auto-analysis runs before the module's
`MN103FixCallFrames.java`. Without `--analyze`, no auto-analysis runs.
Omit `--ghidra` to prepare inputs only. Existing projects are not overwritten.

## Query existing analysis

```powershell
& "$ghidra/support/analyzeHeadless.bat" generated/ghidra/projects E148-1100 `
  -process main.expanded.bin -readOnly -noanalysis `
  -scriptPath tools/ghidra -postScript find_refs.py 0x60023818
```

Find the `OM5_REFS ` marker in Ghidra's output: it prefixes one compact JSON
object with `address`, `xref_count`, `xrefs`, `callers` and `truncated`. An optional
second argument limits entries (default 100). Callers cover returned xrefs, so
they too are incomplete when truncated. Empty results mean no references in
the current analysis, not no references in the firmware. Indirect calls and
code not reached by auto-analysis may require manual disassembly. Inspect raw
instructions with GNU `objdump -m am33-2`; upstream documents ABI, operand and
decompiler limitations. Follow-up analysis needs the call-frame fixer again.

## Validation in this environment (2026-11-18)

Verified official stock decoding, all ten loader bounds, report generation and
Atlas symbol export. Host-side unit tests cover native gaps, unaligned cached
and uncached pointers, usage, missing/wrong stock, import planning, input hash
validation, conflicts, label sanitization and bounded query formatting.

Installed Ghidra 11.4.2 and Temurin JDK 21.0.9+10 privately under
`generated/runtime/`, after verifying the official Ghidra SHA-256
`795a02076af16257bd6f3f4736c4fc152ce9ff1f95df35cd47e2adc086e037a6` and the
Temurin release's SHA-256 file. [JDK archive and checksum](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.9%2B10).
SLEIGH compilation succeeded with upstream warnings about 1282 NOP constructors
and one unread temporary. The pinned MN103 module imported stock successfully,
using the bundled Jython adapter: 11 memory blocks, 184 labels. Import logs are
in `generated/ghidra-import.log`.

This bounded read-only smoke test passed:

```powershell
& "$ghidra/support/analyzeHeadless.bat" generated/ghidra/projects E148-1100 `
  -process main.expanded.bin -readOnly -noanalysis -scriptPath tools/ghidra `
  -postScript verify_import.py -postScript MN103FixCallFrames.java `
  -postScript find_refs.py 0x60023818 -postScript find_refs.py 0x6002384a
```

`verify_import.py` checks resident/loaded memory and the `malloc` label, checks
two native gaps remain unmapped, and disassembles only the known caller range
`0x6002424e..0x6002426b`. Both direct-call xrefs were found: `0x60024251` to
`0x60023818`, and `0x60024263` to `0x6002384a`. The call-frame fixer set four
entries with zero frame conflicts. Both query scripts returned compact JSON
with the expected xref. Logs: `generated/ghidra-query.log`. The read-only run
discards these temporary analysis changes; the saved project has no full
analysis. Use `--out generated/ghidra-analyzed --analyze` for a fresh analyzed
import. Full auto-analysis and complete caller discovery were **not run**.

GNU binutils 2.43 in WSL provided the primary static allocator disassembly.
No emulator, firmware build, camera update or release check was run for this
analysis-only task. `python scripts/check.py fast` passed 39 tests with two
existing skips: E144 built-output checks and E148 release reproduction need
external input/build settings. The 17 new tooling tests use synthetic fixtures.
