/* The card block (OM5MOD/CADUCEUS.BIN): one section at the address boot.s runs it from (CB_BODY), the flashed
 * build's symbols from its patch.elf (tools/mkcardblock.py passes --just-symbols). */
SECTIONS {
 .text 0x63700100 : { *(.text) *(.rodata*) *(.data) }
 /DISCARD/ : { *(.bss) *(COMMON) }
}
ASSERT(SIZEOF(.text) <= 0x10000 - 0x100, "the card block is larger than boot.s reads (CB_MAX)")
