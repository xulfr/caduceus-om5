# E148 1.1: Ghidra tone curves, Soft Focus and spare-setting writes

Static research, 2026-11-18. No photo development, emulator run, camera update
or firmware build was performed. OM-Emu does not develop photographs. Findings
below are observations of stock bytes/analysis, followed by explicitly labelled
inferences or hypotheses. Q1 and Q3 have positive static answers; **Q2's weight
getter remains unidentified**, although its downstream flag reader is located.

## Inputs and reproducible project

**Observation.** Branch base is `3803ff8` from
`origin/codex/space-map-tooling`. The plan and effects map were read with
`git show origin/claude/sharp-cray-0up4d3:PATH`, at observed remote revision
`388c023`; no firmware branch was checked out or merged.

- Official E148 1.1 BIN SHA-256:
  `9de5d77e1d290fa2ed4ebc7d75cee0ed490befbc89566722467d1d421d66d637`.
- Expanded main SHA-256:
  `7ae7d4c60990cc859c070e0ceb6cbe612f9c5b260713f2f1256e51d137851c61`.
- Ghidra 11.4.2; Temurin Java 21.0.9+10; MN103 module
  `01fc3928802d227b2d5f06b83f40543ecbe92f40`. Ghidra release checksum verified.
- Private project: `generated/ghidra/projects/E148-1100.gpr` and its `.rep/`
  directory. Native loader section bases plus the resident prefix were imported;
  184 exported symbols were applied. Images, databases, indexes and raw results
  remain ignored, since the project contains proprietary firmware bytes.
- Full auto-analysis ran once: manager time **611 seconds**, seed/fix/report
  interval **627.407 seconds**, process wall time **637.044 seconds**. It found
  **50,424 functions / 3,305,241 instructions**, without timeout. Six explicit
  indirect callbacks were subsequently added without another full pass, bringing
  the saved function count to **50,430**; instruction count remained unchanged.
- Full-pass warnings: constructor resolution at `0x6159dd31`, `0x60fca668`;
  the frame fixer skipped four targets inside instructions. It reported zero
  conflicting frames. These limits prevent treating discovery as exhaustive.

**Observation.** The sorted immediate index has 1,829,500 value/address records
(14,636,000 bytes). An eleven-query stock batch took 11.360 seconds; a later
six-query verification batch took 8.182 seconds, including JVM startup. Queries
use the saved project with `-readOnly -noanalysis` and emit bounded JSON with an
explicit `ghidra_run` field. Installation and query commands are in the
[Ghidra README](../tools/ghidra/README.md).

**Observation.** Research function names and the six manually discovered
callbacks are reproducible through `seed_functions.py` and
`tools/ghidra/e148_research_seeds.json`. These change Ghidra metadata only.
They do not create firmware patches or claim camera validation. All original
exported labels remain available. Raw query batches/results are under
`generated/ghidra/`; no cached firmware-build results were used.

## Q1: tone / gamma stage

**Observation, high confidence.** The E148 RGB gamma stage is `0x603e69ae`.
It obtains R/G/B curve pointers from `0x603e644a`, then calls the three-pointer
setter **`0x603e6974` at `0x603e6b3e`**. The development stage sequence
`0x603e8fba` calls this stage at `0x603e8ffa`, after `0x603e509a` and before
`0x603e5ed6` and the later tone/luminance stages.

**Observation.** GNU MN103 objdump independently confirms the setter's actual
register ABI: a0 = output O, a1 = R table, d0 = G table, d1 = B table. It stores
those pointers at **O+2596 / O+2600 / O+2604** (`0xa24/0xa28/0xa2c`) and clears
bit `0x1000` in O+4. Do not infer the d/a argument order from Ghidra's displayed
C parameter order; the module cannot express the split register ABI fully.

**Observation.** There are two decoded direct calls to the setter:

| Call site | Containing function | Static role |
|---|---|---|
| `0x603e6b3e` | `0x603e69ae` | Normal gamma stage, selected R/G/B pointers, cache-aware |
| `0x603e6f0b` | `0x603e6e21` | Special-filter path, including distinct channel tables |

**Observation.** `0x603e6e21` handles subtypes `0x0b00..0x0b05`; subtype 0x0b02
selects tables at `0x6053ed38`, `0x6053ef38`, `0x6053f138`. Those are 256-entry
u16 tables with 12-bit-range values. A normal example at `0x60533138` has
256 u16 values, minimum 0 and maximum 4095. The selector `0x603e644a` composes
the request key from R+8/R+9/u16 R+10 and uses rows at `0x605745b0` and a
handler table at `0x60575c20`; not every hashed branch is recovered as C.

**Observation.** Consumer **`0x6037ccd2`** reads O+0xa24/0xa28/0xa2c and expands
256 u16 entries per active channel into 32-bit working tables. It distinguishes
equal R/G/B pointers from three different pointers, and also consumes the
optional luminance table pointer at O+0xa30. Its callers are `0x6037be36` and
`0x6037be58` inside the hardware-output preparation function `0x6037bd59`.

**Observation.** A second concrete LUT location is **`0x603e863e`**. It obtains
the brightness/luminance table through `0x603e85de` and installs O+0xa30. When a
mutable copy is required, it copies **256 x u16 into O+0xa34** and points O+0xa30
there. `0x603e85de` can itself compose a 256-entry table into a supplied buffer:
`out[i] = secondary[base[i]]`, with a fallback at `0x6053fd42`. Base selection is
at `0x603e7f72`; optional secondary-table selection is at `0x603e85aa`.

**Inference, high confidence.** These are E148's counterparts of the referenced
RGB gamma/luminance stages. The setter closely matches the
[E-P7 gap-6 description](https://github.com/cakelesscoder/caduceus-ep7/blob/0cb1dbcc50595cd87f56648810762ffbbb8e17f3/docs/FUJI_GAPS.md#6-gap-6-luminance-dependent-colour-split-toning-crossover).
The [OM-3 split-toning notes](https://github.com/androidfanman/caduceus-om3/blob/e2ec3f00fc01039b2b434f42822579af942ec551/research/NOTES.md#split-toning-research-2026-11-07-static--emulator-only-no-camera-build-scripts-in-researchsplittone)
describe a different representation: three job-owned 640-byte copies. E148's
observed path installs pointers and later expands 256-entry tables; transplanting
OM-3's O+1252/1892/2532 layout would be unsupported.

**Hypothesis, untested.** A cache-aware intervention after pointer selection,
using owned mutable tables, could support Blacks/Whites or split toning. This
research does not establish buffer lifetime, a safe hook or rendered results.
The exact connection from effective settings 383/691/382 into these tables was
not proved. `0x6044dde6` remains ruled out as the curve stage; it is the previously
identified register packer. No firmware edit is proposed here.

## Q2: Soft Focus weight getter and downstream 0x80 readers

**Observation, high confidence.** Work-list builder **`0x6038d263`** tests the
job flag **0x80 at `0x6038de55`**. Its flag word is at work-context+0x10.
Depending on the byte at context+0x2c4d, it queues one of two sequences:

| Branch | Queued callback addresses |
|---|---|
| Byte 0..3/default branch | `0x603932cb`, `0x6039333d`, `0x603934ba` |
| Byte 4..8 branch | `0x6039352b`, `0x603936a6` |

**Observation.** Predicate helpers `0x6038c8cb` (test at `0x6038c8d1`) and
`0x6038c8f6` (test at `0x6038c8fc`) also read 0x80 alongside other Art-effect
flags. The work-list branch above is connected to actual callback scheduling,
rather than merely another unrelated use of the integer 128.

**Observation.** Following these callbacks reaches jobs with format `0xf005`
and phase IDs `0x400..0x403`: `0x603937f8` prepares phase 0x400, `0x603938fd`
prepares 0x401, `0x60393342` prepares 0x402, and the alternate callback
`0x6039352b` can prepare 0x403. They submit work through `0x6038a98c`.
`0x603934bf` registers completion callback `0x6039374d`, which also changes
the phase to 0x402 on its observed format branch. These are concrete next
anchors for following the blur/blend executor.

**Observation / limitation.** Ghidra initially had code labels, but no functions,
at six of these indirect callbacks. They were explicitly seeded, then the
call-frame fixer was run without repeating full auto-analysis. The entry at
`0x6039333d` is a five-byte prologue that falls into separately callable
`0x60393342`; `callees.py` now exposes this as a `shared_entry_successors`
relationship instead of implying that its empty direct-call list describes
the whole shared body. Function sizes are database bodies, not proof of unique
machine-function extents.

**Observation, negative result.** Searching decoded scalar 600 (`0x258`) produced
201 instructions in 164 groups. Paging, targeted decompilation and bounded GNU
checks ruled out the known timing helpers at `0x602f87c0`/`0x602f87d1` and
`0x602fa544`/`0x602fa56d`, the division helper `0x6034e0a8`, size/timing code
around `0x60333384` and `0x60351a41`, and the constructor at `0x6086008e`.
Searching 0x600 as a separate numeric interpretation did not establish a weight
getter either. None of these functions is relabelled as the missing getter.

**Inference / unresolved.** The queued F005 jobs are a stronger lead than a
constant search, but the function satisfying the OM-3 getter contract has **not
been established**. The OM-3 source's Q10 sharp-input weight, decimal 600 default,
and context offset 48 must not be transferred to E148 by assumption. E148's
observed gamma context uses offset 52 for its key, but this alone does not prove
the Soft Focus executor uses that same context type.

**Hypothesis / next investigation.** Follow the F005/0402 handoff through
`0x6038a98c` / `0x6038b6a9` to its executor, including indirect/hash dispatch and
unmapped external library calls. Determine where the blend coefficient comes
from before naming a getter or selecting a hook. Empty Ghidra xrefs and absence
of a literal 600 are not absence proofs. Confidence is high for the flag reader
and queue addresses, **unresolved for the weight getter**.

## Q3: stock writes to 907, 911 and 915

**Observation, high confidence: yes, all three.** Literal-immediate searches
alone missed the relevant writes because these paths iterate ROM ID lists.
Two selected store-copy lists contain every requested ID:

| ID | Entry in list based at `0x604df6a0` | Entry in list based at `0x604e0210` | Default-value word |
|---:|---|---|---|
| 907 | `0x604dfb84` | `0x604e06f6` | `0x604dc084` = 0 |
| 911 | `0x604dfb8c` | `0x604e06fe` | `0x604dc094` = 0 |
| 915 | `0x604dfb94` | `0x604e0706` | `0x604dc0a4` = 0 |

**Observation.** Default lookup **`0x602e1554`** reads the u32 default at
`0x604db258 + 4*ID` for IDs below 0x8d9. The three words above are zero in pinned
stock. Default/store initialization **`0x602e131b`** loops over the 0x5b7-entry
list at `0x604e0210`, gets each default, and calls **`active_write` `0x602f5121`
at `0x602e1335` for store indices 0 and 1**. All three IDs lie within the loop.
GNU objdump independently confirms ID in d0, store in d1 and value in a0 at
that call. The writer accepts these IDs (its bound is ID < 0x8d9).

**Observation.** Reset wrapper **`0x602e0cea`** passes the 0x966-entry list at
`0x604dde2e` to **`0x602e0ef3`**, which reads defaults, calls `0x602f5243` and
`0x602f5396`, and writes both active stores. The list contains ID 907 at
`0x604de4f6`, 911 at `0x604de4fe`, and 915 at `0x604de506`.

**Observation.** Store-save **`0x602e1153`** selects one of the two copy lists,
then reads the working value through `wc_get` and writes the selected active
store through `0x602f5121` at **`0x602e11fc` / `0x602e1222`**. Restore
**`0x602e1071`** reads through `active_read` and writes through `wc_set`.
**`0x602e1237`** copies another store source through `0x602f52ea`, then uses
`active_write` at `0x602e12e0` / `0x602e1306`. These loops include all three IDs,
even though no literal `mov 915` setting-write instruction is required.

**Inference, high confidence.** These IDs are not storage that stock universally
leaves untouched. Reusing them for grain must account for normal store copies,
default initialization and reset. Copies may appropriately preserve grain;
the fact that a stock write exists does not by itself establish a grain bug.
Which owner UI actions reach each path, and the behavior of Claude's current
grain implementation, were not executed or changed in this task.

## Validation and remaining work

**Observation.** `python scripts/check.py fast` is run before every commit.
The tooling tests use synthetic fixtures; stock report generation and Ghidra
queries were separately executed on the pinned private image. E144 output
checks and E148 release reproduction remain skipped without their configured
input/build settings. Linux install commands are documented but not executed.
No firmware/emulator integration, camera rendering or physical-camera claim
follows from this research.

**Outstanding.** Q2's weight getter; complete indirect-call recovery; the exact
383/691/382-to-curve connection; gamma cache/ownership and safe intervention
timing; camera validation of any future effect. No firmware, installer, release
or emulator-runner code was changed, and nothing was merged into main.
