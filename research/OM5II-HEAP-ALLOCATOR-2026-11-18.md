# E148 1.1 stock allocator/free: static findings

Status: static analysis only, 2026-11-18. No allocation, emulator execution,
firmware modification or camera test was performed for this investigation.

## Inputs and reproduction

- Repository base: `a72851a4ada5eab8eed02f7a06afd7f9297bbe81` (`main`).
- Official OM-5 Mark II E148 1.1 BIN SHA-256:
  `9de5d77e1d290fa2ed4ebc7d75cee0ed490befbc89566722467d1d421d66d637`.
- Expanded component 0x100 SHA-256:
  `7ae7d4c60990cc859c070e0ceb6cbe612f9c5b260713f2f1256e51d137851c61`.
  Decoded with the existing `oly_container.parse` and
  `oly_compress.expand_image`; expanded file offset = address - `0x60021020`.
- Disassembler: GNU binutils 2.43, `objdump -D -b binary -m am33-2` in WSL.
  This investigation did not use Ghidra decompiler output.
- Atlas reference revision: `f36e141d5ad4f069381218ce0495230c84a9be60`.
  [OM-3 allocator/free records](https://github.com/xulfr/om-firmware-atlas/blob/f36e141d5ad4f069381218ce0495230c84a9be60/records/reference/om3-1100.yaml).

Prepare a private expanded input (no Ghidra installation needed):

```powershell
python tools/ghidra/headless.py --atlas generated/atlas --stock $env:OM5_STOCK
```

With a GNU MN103 objdump executable, disassemble these exact ranges, saving
logs under `generated/`:

```sh
OBJDUMP=/path/to/mn10300-elf-objdump
"$OBJDUMP" -D -b binary -m am33-2 --adjust-vma=0x60021020 \
  --start-address=0x60023818 --stop-address=0x600238e2 \
  generated/ghidra/main.expanded.bin > generated/heap-wrappers.asm
"$OBJDUMP" -D -b binary -m am33-2 --adjust-vma=0x60021020 \
  --start-address=0x60023b01 --stop-address=0x60023e80 \
  generated/ghidra/main.expanded.bin > generated/heap-pools.asm
"$OBJDUMP" -D -b binary -m am33-2 --adjust-vma=0x60021020 \
  --start-address=0x6002424e --stop-address=0x6002426c \
  generated/ghidra/main.expanded.bin > generated/heap-stock-caller.asm
```

## Observation: the pair is 0x60023818 / 0x6002384a

The linker already names `malloc = 0x60023818`. Its `ST_POOL` comment calls
`0x6002385f` free; that address is **inside** the wrapper, 21 bytes after entry.
No linker, assembly or manifest file was changed by this task.

| Role | Stock entry | Arguments/result seen in stock | Evidence |
|---|---|---|---|
| Size-selecting allocation wrapper (`scheap_phyalloc`) | `0x60023818` | requested bytes in d0, pointer in a0 | compares size, selects class, calls `0x60023b01`, returns `ret [],4` |
| Pointer-selecting free wrapper (`scheap_phyfree`) | `0x6002384a` | pointer in a0 | begins `mov a0,d0`, selects pool by pointer bounds, calls `0x60023d65`, returns `ret [],4` |
| Internal class allocator | `0x60023b01` | class in d0; returns a0 | indexes pool base/count/stride tables, returns selected block |
| Internal class free | `0x60023d65` | class in d0, original pointer in a0 | subtracts pool base, divides by stride, checks remainder/index, updates free bookkeeping |

Exact decisive instructions:

```text
60023818  fa c8 80 00        cmp 128,d0
60023821  fa c8 00 08        cmp 2048,d0
6002382b  fa c8 00 40        cmp 16384,d0
60023833  cd ce 02 f0 1c     call 0x60023b01,[d2,d3,a2,a3],28
60023847  df 00 04           ret [],4
6002384a  f1 d0              mov a0,d0
6002385f  fc c8 80 7d e2 a1  cmp 0xa1e27d80,d0
60023867  fc c8 c0 2a e3 a1  cmp 0xa1e32ac0,d0
60023885  cd e0 04 f0 20     call 0x60023d65,[d2,d3,a2,a3],32
60023897  df 00 04           ret [],4
```

The allocating wrapper selects class 0 for unsigned sizes <=128, class 1 for
129..2048, and class 2 for 2049..16384. Larger values take a diagnostic path
through `0x6002372a` and return a0 = 0. The diagnostic strings at `0x60028317`
and `0x60028334` are `scheap_phyalloc: Size Over :` and
`scheap_phyfree: not allocated pointer :`, respectively.

The free entry tests three uncached address ranges, with exclusive upper bounds:

| Class | Base | End | Blocks (table `0x60028298`) | Stride (table `0x600282c8`) |
|---|---|---|---:|---:|
| 0 | `0xa1a8e380` | `0xa1a96900` | 178 | 192 |
| 1 | `0xa1e27d80` | `0xa1e32ac0` | 21 | 2112 |
| 2 | `0xa1c7c740` | `0xa1d29200` | 43 | 16448 |

Bases are also present as LE32 words starting at `0x60028288`. For class 1,
21 * 2112 = 44,352 = `0xad40`, exactly the wrapper's pool span. The internal
allocator uses base + index * stride, then moves the result to a0 at
`0x60023bbe`. The free implementation validates an exact block base rather
than an arbitrary interior pointer (`0x60023d97..0x60023db8`).

A native caller provides an independent argument/return pairing:

```text
6002424e  mov 16384,d0
60024251  call 0x60023818,[],4
60024256  mov a0,a2
60024257  call 0x60024330,[d2,d3,a2,a3],48
6002425c  mov a2,a0
6002425d  call 0x60023595,[d2,d3,a2,a3],28
60024262  mov a2,a0
60024263  call 0x6002384a,[],4
```

An all-byte scan for relative `cd` (signed LE16) / `dd` (signed LE32) call
encodings found 802 candidates targeting `0x60023818`, 819 targeting
`0x6002384a`, and zero targeting `0x6002385f`. These are **byte-pattern candidate
counts**, not a validated call graph. The native caller above was independently
disassembled. Raw candidate lists are private generated output, not evidence
that every pattern is an instruction.

A Ghidra 11.4.2 / Java 21.0.9+10 live static smoke test independently generated
both xrefs after bounded disassembly of `0x6002424e..0x6002426b`, using the pinned
MN103 module `01fc3928802d227b2d5f06b83f40543ecbe92f40`. `find_refs.py` returned
the expected call sites for both addresses. The call-frame fixer ran with no
frame conflicts. This validates the tooling adapter and the two decoded call
instructions, not allocator execution; full auto-analysis was not run.

## Inference and comparison with OM-3

The two E148 wrappers are the size/pointer-selecting allocation/free pair sought
by the task. `malloc` is a project convenience name: this is a fixed-class pool
interface, not evidence of general-purpose, unbounded C-library malloc.

Atlas records OM-3 1.1 malloc `0x60024068` / free `0x6002409a` and class-1 pool
`0xa2852000..0xa285d280`. Both E148 entries are `0x850` lower, and both pairs
are separated by `0x32` bytes. The same class/pool role is consistent with a
shared implementation lineage. **No OM-3 binary was decoded or byte-matched**;
the delta and role are a comparison with the Atlas record, not a cross-model
ABI proof or a transfer of its physical-camera validation.

Calling `0x6002385f` as an ordinary free entry would skip `mov a0,d0` and the
class-0 bounds checks. Its outcome would depend on d0's incoming value. It is
ruled out as the general entry; no call into it is proposed. Likewise, copying
OM-3's absolute addresses into E148 is ruled out: E148 `0x6002407b..0x600240a4`
is a byte-string comparison loop; `0x6002409a` lies inside that loop. Decoding
from `0x60024068` does not expose an allocator wrapper.

## Hypotheses / outstanding validation

- The class-1 pool may be suitable for future state/table allocations up to
  2048 bytes, subject to availability and correct task/initialisation timing.
  This is a hypothesis, not a recommendation to add a call now.
- The 64-byte difference between request thresholds and strides does not prove
  those extra bytes belong to clients. Treat threshold sizes as limits.
- Exhaustion behavior, concurrency, pool lifetime, cache alias policy, and
  whether null is accepted by free need validation. The observed free wrapper
  does not special-case null before its range checks.
- Existing hooks' usage, valid scheduling context and camera behavior were not
  audited. No firmware behavior or safety status changes follow from this note.

The [Atlas section and heap hazards](https://github.com/xulfr/om-firmware-atlas/tree/f36e141d5ad4f069381218ce0495230c84a9be60/records/reference)
remain applicable: runtime state must not be placed in loaded image padding,
and readiness is not the section-request bit. The [tooling README](../tools/ghidra/README.md)
documents the bounded Ghidra test, unrun stages and space-candidate limitations.
