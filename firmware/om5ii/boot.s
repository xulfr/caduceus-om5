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
 *     camera-run there; see research/OM5II-BACKGROUND-ARM-2026-11-28.md).
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
 ret [d2,d3,a2,a3],24

bg_name:
 .asciz "CAD_ARM"
