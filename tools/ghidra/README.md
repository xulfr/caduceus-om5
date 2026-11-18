# E148 1.1 static analysis

This tooling reads firmware; it does not build, patch, install or flash it. Keep
stock, expanded images, Ghidra projects and reports in ignored `generated/`.
Python 3.10+ is required for the host tools. Ghidra scripts use bundled Jython.

## Install (PowerShell, Windows; executed)

From the repository root, install privately in ignored `generated/`. Sources:
[Ghidra 11.4.2 release/checksum](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_11.4.2_build),
[Temurin 21.0.9+10 archives/checksums](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.9%2B10),
and the [pinned processor module](https://github.com/nsud-dev/ghidra-mn103/blob/01fc3928802d227b2d5f06b83f40543ecbe92f40/README.md).
These are the commands used to provision this worktree in the earlier tooling
task; this task reused that installation and rechecked the Ghidra checksum and
module revision.

```powershell
New-Item -ItemType Directory -Force generated/runtime | Out-Null
gh release download 'jdk-21.0.9+10' --repo adoptium/temurin21-binaries --pattern 'OpenJDK21U-jdk_x64_windows_hotspot_21.0.9_10.zip' --pattern 'OpenJDK21U-jdk_x64_windows_hotspot_21.0.9_10.zip.sha256.txt' --dir generated/runtime
gh release download Ghidra_11.4.2_build --repo NationalSecurityAgency/ghidra --pattern 'ghidra_11.4.2_PUBLIC_20250826.zip' --dir generated/runtime
$jdkArchive = 'generated/runtime/OpenJDK21U-jdk_x64_windows_hotspot_21.0.9_10.zip'
$jdkExpected = (Get-Content "$jdkArchive.sha256.txt").Split(' ')[0]
if ((Get-FileHash $jdkArchive -Algorithm SHA256).Hash -ne $jdkExpected) { throw 'JDK checksum mismatch' }
if ((Get-FileHash generated/runtime/ghidra_11.4.2_PUBLIC_20250826.zip -Algorithm SHA256).Hash -ne '795a02076af16257bd6f3f4736c4fc152ce9ff1f95df35cd47e2adc086e037a6') { throw 'Ghidra checksum mismatch' }
python -c "import zipfile; zipfile.ZipFile('generated/runtime/OpenJDK21U-jdk_x64_windows_hotspot_21.0.9_10.zip').extractall('generated/runtime'); zipfile.ZipFile('generated/runtime/ghidra_11.4.2_PUBLIC_20250826.zip').extractall('generated/runtime')"
$env:JAVA_HOME = (Resolve-Path 'generated/runtime/jdk-21.0.9+10').Path
& "$env:JAVA_HOME/bin/java.exe" -version
$ghidra = (Resolve-Path generated/runtime/ghidra_11.4.2_PUBLIC).Path
python -m pip install PyYAML==6.0.3
git clone https://github.com/nsud-dev/ghidra-mn103.git generated/ghidra-mn103
git -C generated/ghidra-mn103 checkout --detach 01fc3928802d227b2d5f06b83f40543ecbe92f40
Copy-Item -Recurse generated/ghidra-mn103/MN103 "$ghidra/Ghidra/Processors/"
& "$ghidra/support/sleigh.bat" "$ghidra/Ghidra/Processors/MN103/data/languages/mn103.slaspec"
git clone https://github.com/xulfr/om-firmware-atlas.git generated/atlas
git -C generated/atlas checkout --detach f36e141d5ad4f069381218ce0495230c84a9be60
```

Use fresh archive/module destinations; do not overlay another installation.
If reusing this worktree, verify the existing archives and module commit and
set `JAVA_HOME` / `$ghidra`; no download or recompilation is needed.

## Install (Linux x86-64; documented, not executed here)

```sh
mkdir -p generated/runtime
gh release download 'jdk-21.0.9+10' --repo adoptium/temurin21-binaries --pattern 'OpenJDK21U-jdk_x64_linux_hotspot_21.0.9_10.tar.gz' --pattern 'OpenJDK21U-jdk_x64_linux_hotspot_21.0.9_10.tar.gz.sha256.txt' --dir generated/runtime
gh release download Ghidra_11.4.2_build --repo NationalSecurityAgency/ghidra --pattern 'ghidra_11.4.2_PUBLIC_20250826.zip' --dir generated/runtime
(cd generated/runtime && sha256sum -c OpenJDK21U-jdk_x64_linux_hotspot_21.0.9_10.tar.gz.sha256.txt)
printf '%s  %s\n' '795a02076af16257bd6f3f4736c4fc152ce9ff1f95df35cd47e2adc086e037a6' 'generated/runtime/ghidra_11.4.2_PUBLIC_20250826.zip' | sha256sum -c -
tar -xf generated/runtime/OpenJDK21U-jdk_x64_linux_hotspot_21.0.9_10.tar.gz -C generated/runtime
unzip -q generated/runtime/ghidra_11.4.2_PUBLIC_20250826.zip -d generated/runtime
export JAVA_HOME="$PWD/generated/runtime/jdk-21.0.9+10"
export GHIDRA_HOME="$PWD/generated/runtime/ghidra_11.4.2_PUBLIC"
"$JAVA_HOME/bin/java" -version
python3 -m pip install PyYAML==6.0.3
git clone https://github.com/nsud-dev/ghidra-mn103.git generated/ghidra-mn103
git -C generated/ghidra-mn103 checkout --detach 01fc3928802d227b2d5f06b83f40543ecbe92f40
cp -R generated/ghidra-mn103/MN103 "$GHIDRA_HOME/Ghidra/Processors/"
"$GHIDRA_HOME/support/sleigh" "$GHIDRA_HOME/Ghidra/Processors/MN103/data/languages/mn103.slaspec"
git clone https://github.com/xulfr/om-firmware-atlas.git generated/atlas
git -C generated/atlas checkout --detach f36e141d5ad4f069381218ce0495230c84a9be60
```

The Linux commands require `gh`, `tar`, `unzip`, `sha256sum` and Python 3.10+.
`unzip` preserves executable bits for Ghidra's native support programs.

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
automatically declared a function by the importer. With `--analyze`,
`analysis_start.py` seeds eight documented entry points, then full auto-analysis
runs before `MN103FixCallFrames.java`, `analysis_report.py` and
`ExportImmediateIndex.java`. The report records elapsed time, functions,
instructions and timeout status. Without `--analyze`, no auto-analysis runs.
Omit `--ghidra` to prepare inputs only. Existing projects are not overwritten.

## Query existing analysis

The portable host wrapper sets the private JDK path automatically on this
Windows worktree. Elsewhere set `JAVA_HOME` and `GHIDRA_HOME`, or pass
`--java-home` and `--ghidra` before the query name:

```powershell
python tools/ghidra/query.py find_refs 0x602d000d
python tools/ghidra/query.py callees malloc
python tools/ghidra/query.py func_at 0x604239db
python tools/ghidra/query.py find_imm 600 --near 0x60400000
python tools/ghidra/query.py decomp malloc --max-lines 32
```

These open the saved project with `-readOnly -noanalysis`, print compact JSON
(normally one physical line), and save Ghidra noise under
`generated/ghidra/query-logs/`. Every payload states `ghidra_run`; missing
installations/projects yield `false` and exit nonzero. An empty result from a
live query still means incomplete static coverage, not an absence proof.
Unknown functions return null; ambiguous names and decompiler failures are
explicit errors. Decompilation defaults to 32 lines/12,000 characters and a
45-second timeout. Other lists are bounded to 30 groups/xrefs and eight sites
per group, with truncation flags. `--near` means +/-64 KiB in instruction
addresses. `find_imm` includes scalar displacement operands as well as literal
immediates; inspect the instruction text to distinguish their roles.
Use `find_imm VALUE --offset 30` (then 60, etc.) to page through large result
sets without increasing each JSON response; `function_group_count` gives the
total number of groups.

For several cheap queries in one JVM, use `--batch FILE.json`: an array of up to
20 objects such as `[{"script":"func_at","args":["0x60023818"]}]`. Results retain
that order. `find_imm` uses the sorted immediate index when available, validates
its stock-image hash and instruction count, and verifies each hit against the
live instruction. Otherwise it explicitly reports `listing-scan` mode. After
changing instruction discovery, regenerate the index with
`-postScript ExportImmediateIndex.java generated/ghidra/immediates.idx`.
The index covers decoded instructions only; data tables and unanalysed code
require separate research.

```powershell
& "$ghidra/support/analyzeHeadless.bat" generated/ghidra/projects E148-1100 `
  -process main.expanded.bin -readOnly -noanalysis `
  -scriptPath tools/ghidra -postScript find_refs.py 0x60023818
```

Find the `OM5_REFS ` marker in Ghidra's output: it prefixes one compact JSON
object with `address`, `xref_count`, `xrefs`, `callers`, `data_refs` and `truncated`. An optional
second argument limits entries (default 30). Callers cover returned xrefs, so
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
discarded those temporary analysis changes. The subsequent full analysis below
is saved in the project.

## Full project and query validation (2026-11-18)

The existing project at `generated/ghidra/projects/E148-1100.gpr` was opened
once with full auto-analysis, using these exact Windows commands:

```powershell
$env:JAVA_HOME = (Resolve-Path 'generated/runtime/jdk-21.0.9+10').Path
& generated/runtime/ghidra_11.4.2_PUBLIC/support/analyzeHeadless.bat generated/ghidra/projects E148-1100 -process main.expanded.bin -scriptPath tools/ghidra -preScript analysis_start.py generated/ghidra/analysis-report.json -postScript MN103FixCallFrames.java -postScript analysis_report.py generated/ghidra/analysis-report.json
& generated/runtime/ghidra_11.4.2_PUBLIC/support/analyzeHeadless.bat generated/ghidra/projects E148-1100 -process main.expanded.bin -readOnly -noanalysis -scriptPath tools/ghidra -postScript ExportImmediateIndex.java generated/ghidra/immediates.idx
```

Linux uses the same arguments with `"$GHIDRA_HOME/support/analyzeHeadless"`.
For a fresh import, `headless.py --analyze` performs the import, seeding, full
analysis, call-frame repair, reporting and indexing automatically. Do not repeat
full analysis for ordinary queries. The eight seeds are documented in
`analysis_start.py`; all other exported symbols remain labels.

The full analysis manager reports **611 seconds**. Seeding through call-frame
repair/reporting took **627.407 seconds**, and the complete process including
JVM/project startup and save took **637.044 seconds**. The saved project has
**50,424 functions and 3,305,241 instructions**. Timeout status was false.
The fixer visited 50,405 entries, updated/re-disassembled 1,750, reported zero
conflicting frames, and skipped four targets inside another instruction.
The analysis log also reports unresolved constructors at `0x6159dd31` and
`0x60fca668`. Completed analysis does not establish complete/correct discovery.
Logs and machine-readable metrics: `generated/ghidra/full-analysis.log`,
`analysis-report.json`, and `analysis-process.json`. The immediate index has
1,829,500 distinct value/address records (14,636,000 bytes).

All five query adapters and the index exporter were also executed against a
small synthetic MN103 project in `generated/query-fixture/`: expected call
reference, callee, containing function, immediate 600, and truncated decompiler
output all passed. This is a Ghidra runtime check, separate from CPython tests.

GNU binutils 2.43 in WSL provided the primary static allocator disassembly.
No emulator, firmware build, camera update or release check was run for this
analysis-only task. `python scripts/check.py fast` completed 48 tests with two
existing skips: E144 built-output checks and E148 release reproduction need
external input/build settings. The other 46 passed. Linux installation was not
executed. Query coverage and research limits are recorded in the dated findings.
