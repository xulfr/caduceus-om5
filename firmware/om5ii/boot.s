/* Caduceus for OM-5 Mark II (E148 1.1): arm in the background after start-up.
 * NOT tested on a camera; exercised in OM-Emu only.
 *
 * Until now everything waited for the first shutter half-press. That keeps
 * start-up stock, but the looks, the extra Picture Mode controls and the
 * profile's own settings are asleep until the user half-presses. Here a
 * background task does the safe part of arming soon after start-up instead:
 *
 *  1. FastEndCb (0x601b1362), a fast-startup callback that runs once per
 *     power-on about 1.2 s in, after the live view (OMKit's loader site,
 *     camera-run there; see research/OM5II-BACKGROUND-ARM-2026-11-27.md).
 *     The hook only creates one low-priority task and returns. Nothing else
 *     runs during start-up.
 *  2. The task waits until every section is initialised (loaded_bits, the
 *     finaliser's word 0xa26e2694, not the submission word +4), and gives up
 *     if the patch is already armed or OK is held at that moment (then the
 *     half-press arms, as before).
 *  3. It allocates the state block P (hsl.s arm_alloc: memory only, no
 *     setting is written) and marks the start-up refresh as pending.
 *  4. Once the card is mounted it links the extra setting descriptors and
 *     reads LOOKS.BIN (films.s fl_entry: RAM structures and a file read; no
 *     setting is written).
 *  5. The profile refresh (hsl.s arm_refresh) writes settings, the work that
 *     froze OM-3 builds at power-on, so it stays with the user: it runs at
 *     the first half-press (hp_entry), in the HLS_EVENT task, as before.
 *
 * Frames follow the firmware's: `call f,[regs],N` writes the return address
 * at the caller's (0,sp), so a function that calls keeps (0..3,sp) free. */
ST_PEND  = 16                   /* P+16: 1 = armed in the background, the start-up refresh not yet run */
CB_STATE = 17                   /* P+17: CADUCEUS.BIN 0 not tried, 1 loaded, 2 tried: none / bad */
CB_TAB   = 20                   /* P+20: the block's entry table (cached address), 0 = none */
CB_BUF   = 0xa3700000           /* the file, read through the uncached view (see research/OM5II-CARD-BLOCK-2026-11-27.md) */
CB_HDR   = 256                  /* header: magic, ABI, body length, CRC-32 of the body, n, n x {address, word} */
CB_BODY  = 0x63700100           /* the body runs through the cached view; cardblock/block.ld links it here */
CB_MAX   = 0x10000              /* header and body */
CB_MAGIC = 0x42444143           /* 'CADB' */
CB_ABI   = 1
CB_NCHK  = 29
BG_PRIO  = 66                   /* below every firmware service task (OMKit's OMK_LOAD uses the same) */
BG_STACK = 0x800

/* FastEndCb's first two instructions (movm [a2],(sp); add -4,sp), replaced. */
.section .bg_site,"ax"
 jmp bg_hook

.section .ext2b,"ax"
/* Entered by the jump above at FastEndCb's entry: its arguments are in d0, d1,
 * a0, a1 and its return address in mdr / (sp). Keep them all, start the task,
 * then run the two displaced instructions and go on. */
bg_hook:
 add -24,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 mov mdr,d0
 mov d0,(20,sp)
 call bg_start,[],16
 mov (20,sp),d0
 mov d0,mdr
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 24,sp
 movm [a2],(sp)
 add -4,sp
 jmp fastend_resume

/* acre_Task(start d0 = 2, d1 = 0, name a0, entry a1; (4,sp) priority,
 * (8,sp) stack size from the kernel pool, (12,sp) 0). Writes no memory of
 * ours. call bg_start,[],16 */
.global bg_start
bg_start:
 mov BG_PRIO,d0
 mov d0,(4,sp)
 mov BG_STACK,d0
 mov d0,(8,sp)
 clr d0
 mov d0,(12,sp)
 mov 2,d0
 clr d1
 mov bg_name,a0
 mov bg_task,a1
 call acre_task,[d2,d3,a2,a3],56
 ret [],16

/* The task. Ends with ext_tsk on every path. */
bg_task:
 add -8,sp                       /* (0..3,sp): the return slot of every call below */
 mov 300,d2                      /* sections: up to 30 s */
bt_sec:
 mov (loaded_bits),d0
 and 1023,d0
 cmp 1023,d0
 beq bt_ready
 mov 100,d0
 call dly_tsk,[d2],8
 add -1,d2
 bne bt_sec
 bra bt_end
bt_ready:
 call st_ptr,[],8
 cmp 0,a0
 bne bt_end                      /* the half-press got there first */
 mov 4,d0                        /* OK held: 0. Then leave it to the half-press */
 call key_up,[d2,d3,a2,a3],24
 cmp 0,d0
 beq bt_end
 mov 100,d2                      /* the HLS event manager holds the handle word: */
bt_hls:                          /* wait until it is set up, as arm_gate checks */
 movhu (hls_tid),d1
 cmp 0,d1
 beq bt_hls_wait
 btst 0x8000,d1
 beq bt_arm
bt_hls_wait:
 mov 100,d0
 call dly_tsk,[d2],8
 add -1,d2
 bne bt_hls
 bra bt_end
bt_arm:
 call st_ptr,[],8
 cmp 0,a0
 bne bt_end
 call arm_alloc,[d2,d3,a2,a3],36
 call st_ptr,[],8
 cmp 0,a0
 beq bt_end
 mov 1,d0
 movbu d0,(ST_PEND,a0)
 mov 40,d2                       /* the card: up to 10 s for a medium to mount */
bt_card:
 mov 61440,d1                    /* MOUNT OK, as fl_entry checks */
 mov (MS_A),d0
 cmp d1,d0
 beq bt_load
 mov (MS_B),d0
 cmp d1,d0
 beq bt_load
 mov (MS_C),d0
 cmp d1,d0
 beq bt_load
 mov 250,d0
 call dly_tsk,[d2],8
 add -1,d2
 bne bt_card
 bra bt_end                      /* no card: the half-press links and tries again */
bt_load:
 calls fl_entry                  /* descriptors, then LOOKS.BIN once per power-on */
 call cb_load,[d2,d3,a2,a3],24   /* then the card block */
bt_end:
 call ext_tsk,[a2],8

/* hsl.s arm_ext: the half-press extension (entered by calls, every
 * half-press once armed). Run the start-up refresh the background arm left
 * pending, then the films' entry as before. */
.global hp_entry
hp_entry:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 call st_ptr,[],8
 cmp 0,a0
 beq hp_films
 movbu (ST_PEND,a0),d0
 cmp 0,d0
 beq hp_films
 clr d0
 movbu d0,(ST_PEND,a0)
 call arm_refresh,[d2,d3],16
hp_films:
 calls fl_entry
 call cb_load,[d2,d3,a2,a3],24   /* no-op once tried */
 ret [d2,d3,a2,a3],24

/* Read OM5MOD\CADUCEUS.BIN once per power-on (armed, a medium mounted) into
 * CB_BUF and accept it only whole: size, magic, ABI, length, CRC-32, and every
 * {address, word} check of the flashed code it calls (tools/mkcardblock.py
 * lists them), so a block made for another build is never run. Then publish
 * its entry table. call cb_load,[d2,d3,a2,a3],24 */
cb_load:
 call st_ptr,[],8
 cmp 0,a0
 beq cl_out
 mov a0,a2
 movbu (CB_STATE,a2),d0
 cmp 0,d0
 bne cl_out
 mov 61440,d1
 mov (MS_A),d0
 cmp d1,d0
 beq cl_go
 mov (MS_B),d0
 cmp d1,d0
 beq cl_go
 mov (MS_C),d0
 cmp d1,d0
 bne cl_out                      /* no medium yet: a later call tries */
cl_go:
 mov 2,d0
 movbu d0,(CB_STATE,a2)
 mov cb_path,a0
 mov cb_mode,a1
 call fopen,[],4
 cmp 0,a0
 beq cl_out
 mov a0,(4,sp)
 mov a0,a1
 mov CB_BUF,a0
 mov 1,d0
 mov CB_MAX + 1,d1
 call fread,[d2,d3,a2,a3],24
 mov d0,d2
 mov (4,sp),a0
 call fclose,[d2,a2,a3],16
 cmp CB_HDR + 4,d2
 bcs cl_out
 cmp CB_MAX,d2
 bhi cl_out
 mov CB_BUF,a3
 mov (a3),d0
 cmp CB_MAGIC,d0
 bne cl_out
 mov (4,a3),d0
 cmp CB_ABI,d0
 bne cl_out
 mov (8,a3),d1
 mov d1,d0
 add CB_HDR,d0
 cmp d2,d0
 bne cl_out
 mov a3,a0
 add CB_HDR,a0
 call fl_crc,[d2,d3],12
 mov (12,a3),d1
 cmp d1,d0
 bne cl_out
 mov (16,a3),d3
 cmp CB_NCHK,d3
 bhi cl_out
 add 20,a3
cl_chk:
 cmp 0,d3
 beq cl_ok
 mov (a3),d0                     /* a word of the main image's code, 4-aligned */
 mov d0,d1
 and 3,d1
 bne cl_out
 cmp 0x60021020,d0
 bcs cl_out
 cmp 0x617e1020,d0
 bcc cl_out
 mov d0,a0
 mov (a0),d0
 mov (4,a3),d1
 cmp d1,d0
 bne cl_out
 add 8,a3
 add -1,d3
 bra cl_chk
cl_ok:
 mov CB_BODY,a0
 mov a0,(CB_TAB,a2)
 mov 1,d0
 movbu d0,(CB_STATE,a2)
cl_out:
 ret [d2,d3,a2,a3],24

/* hsl.s's graphics stubs: d1 = entry offset -> a1 = the block's entry, or 0
 * when no block is loaded. Keeps a0 and d0. call cb_find,[],12 */
.global cb_find
cb_find:
 mov a0,(8,sp)
 call st_ptr,[],8
 cmp 0,a0
 beq cf_none
 mov (CB_TAB,a0),a1
 cmp 0,a1
 beq cf_none
 add d1,a1
 mov (a1),a1
 bra cf_out
cf_none:
 mov 0,a1
cf_out:
 mov (8,sp),a0
 ret [],12

cb_path:
 .asciz "C:\\OM5MOD\\CADUCEUS.BIN"
cb_mode:
 .asciz "rb"

bg_name:
 .asciz "CAD_ARM"
