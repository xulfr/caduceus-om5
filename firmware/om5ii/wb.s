/* OM-5 Mark II 1.1 (E148 build 1100) per-profile white balance, ported from
 * the OM-3 patch. NOT tested on a camera; exercised in OM-Emu only.
 * The section-2 gate reaches the section-4 body and section-8 profile
 * helper only after arming. */
ST_BUSY = 12
.section .wb_hook,"ax"
 jmp wb_load
.section .wb_extension,"ax"
/* Only picture-mode (111) and WB edits enter the wrapper; others replay. */
wb_load:
 /* The wrapper calls stock_ui_write, in section 6, which
  * boot loads after section 2. The submission flag at 0xa26e2698 can
  * precede decompression; use 0xa26e2694, set after the completion wait
  * and constructors, before touching section-6 code or state. */
 movbu (loaded_bits),d2
 btst 0x20,d2
 beq wb_original
 /* Not armed (no half-press since power-on): the stock commit for every
  * setting. The state block is in the heap (see hsl.s); a0/a1 are kept and
  * a2 = the block for wb_commit. */
 add -8,sp
 mov a0,(4,sp)
 call st_ptr,[],8
 mov a0,a2
 mov (4,sp),a0
 add 8,sp
 cmp 0,a2
 beq wb_original
 mov d0,d2
 add -904,d2
 cmp 126,d2
 bcc wb_not_profile
 /* Blacks 965..967 (hsl.s bw_ids) -> profile id - 965 */
 add -61,d2
 cmp 3,d2
 bcs wb_go_bk
 jmp wb_profile
wb_go_bk:
 jmp wb_bk
wb_not_profile:
 cmp PM_ID,d0
 beq wb_enter
 cmp 1578,d0
 beq wb_enter
 cmp 1632,d0
 beq wb_enter
 cmp 1580,d0
 blt wb_original
 cmp 1605,d0
 bgt wb_original
wb_enter:
 jmp wb_commit
wb_original:
 mov d1,a2
 mov d0,d3
 exthu d3
 mov d3,d0
 jmp commit_resume

.section .wb_body,"ax"
/* Blacks 965..967 -> profile id - 965, then the profile commit (stock commit,
 * then refresh of each context showing that profile). */
wb_bk:
 mov d0,d2
 mov d1,d3
 add -965,d0
 jmp wb_profile_have
/* Replaces the first five bytes of the native commit routine. Its caller
 * already saved d2,d3,a2,a3 in a 20-byte frame. Nested commits use stock. */
wb_commit:
 /* a2 = the state block (wb_load). Nested commits use stock. */
 movbu (ST_BUSY,a2),d2
 cmp 0,d2
 beq wb_begin
 jmp wb_original
wb_begin:
 mov d0,d2
 mov d1,d3
 mov 1,d0
 movbu d0,(ST_BUSY,a2)
 add -8,sp
 cmp PM_ID,d2
 bne wb_do_commit
 call wb_current,[d2,d3,a2,a3],20
 mov d0,a2
 call wb_save,[d2,d3,a2,a3],44
wb_do_commit:
 mov d2,d0
 mov d3,d1
 call wb_original,[d2,d3,a2,a3],20
 mov d0,(4,sp)
 cmp PM_ID,d2
 bne wb_edit
 call wb_current,[d2,d3,a2,a3],20
 cmp a2,d0
 beq wb_done
 call wb_recall,[d2,d3,a2,a3],40
 bra wb_done
wb_edit:
 cmp 1578,d2
 beq wb_store_edit
 cmp 1632,d2
 beq wb_store_edit
 mov d2,d0
 sub 1580,d0
 cmp 26,d0
 bcc wb_done
wb_store_edit:
 call wb_current,[d2,d3,a2,a3],20
 call wb_save,[d2,d3,a2,a3],44
wb_done:
 call st_ptr,[],8
 cmp 0,a0
 beq wb_done_ret
 clr d0
 movbu d0,(ST_BUSY,a0)
wb_done_ret:
 mov (4,sp),d0
 add 8,sp
 ret [d2,d3,a2,a3],20
/* Return base: Color Profile 1..3 (111 = 54..56) => 904,908,912; every other
 * mode => 920 (916 stays unused). No cached bank/profile pointer. */
wb_current:
 mov PM_ID,d0
 call stock_get,[],4
 sub 54,d0
 cmp 3,d0
 bcs wb_current_color
 mov 4,d0
wb_current_color:
 asl 2,d0
 add 904,d0
 ret [d2,d3,a2,a3],20
/* d0 base, frame has 24 local bytes. Checksum is written last. */
wb_save:
 mov d0,d2
 add 3,d0
 mov 1,d1
 mov 0,a0
 call active_write,[d2],8
 mov 1578,d0
 call stock_get,[],4
 mov d0,(4,sp)
 mov 1632,d0
 call stock_get,[],4
 mov d0,(8,sp)
 mov 39,d0
 call stock_get,[],4
 and 255,d0
 mov d0,d3
 mov 132,d0
 call stock_get,[],4
 and 255,d0
 asl 8,d0
 or d3,d0
 mov d0,(12,sp)
 mov (4,sp),d1
 xor d1,d0
 mov (8,sp),d1
 xor d1,d0
 xor 0x57420101,d0
 mov d0,(16,sp)
 mov sp,a2
 add 4,a2
 mov 4,d3
wb_save_loop:
 mov (a2),a0
 mov d2,d0
 mov 1,d1
 call active_write,[d2],8
 inc d2
 inc4 a2
 add -1,d3
 bne wb_save_loop
 ret [d2,d3,a2,a3],44
/* d0 base; invalid/uninitialised words inherit the current WB. */
wb_recall:
 mov d0,d2
 mov d0,a3
 mov sp,a2
 add 4,a2
 mov 4,d3
wb_read_loop:
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 mov d0,(a2)
 inc d2
 inc4 a2
 add -1,d3
 bne wb_read_loop
 mov (4,sp),d0
 mov (8,sp),d1
 xor d1,d0
 mov (12,sp),d1
 xor d1,d0
 xor 0x57420101,d0
 mov (16,sp),d1
 cmp d1,d0
 bne wb_inherit
 mov (4,sp),d0
 mov wb_modes,a0
 clr d3
wb_find_mode:
 movbu (d3,a0),d1
 cmp d1,d0
 beq wb_mode_valid
 inc d3
 cmp 13,d3
 bne wb_find_mode
 bra wb_inherit
wb_mode_valid:
 mov (8,sp),d0
 cmp 2000,d0
 blt wb_inherit
 cmp 14000,d0
 bgt wb_inherit
 mov (12,sp),d0
 mov d0,d1
 lsr 16,d1
 cmp 0,d1
 bne wb_inherit
 extb d0
 cmp -7,d0
 blt wb_inherit
 cmp 7,d0
 bgt wb_inherit
 mov (12,sp),d0
 asr 8,d0
 extb d0
 cmp -7,d0
 blt wb_inherit
 cmp 7,d0
 bgt wb_inherit
 mov (4,sp),d1
 mov 1578,d0
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 mov (8,sp),d1
 mov 1632,d0
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 mov (12,sp),d1
 extb d1
 mov d3,d0
 add 1580,d0
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 mov (12,sp),d1
 asr 8,d1
 extb d1
 mov d3,d0
 add 1593,d0
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 ret [d2,d3,a2,a3],40
wb_inherit:
 mov a3,d0
 call wb_save,[d2,d3,a2,a3],44
 ret [d2,d3,a2,a3],40
wb_modes:
 .byte 0,18,3,1,6,17,7,8,13,14,15,16,9

/* Color and Monochrome Profile settings (E147 descriptors 0x605b905c..:
 * 904-906, 908-910, 912-914, 928-963, 976-984 and SET1-3 of 990-1029 carry
 * refresh handlers 0x60400fc0 / 0x6040466d..).
 * E148 has no such handlers, so a profile edit would not reach the effective
 * settings until the next picture-mode change. After the stock commit, refresh
 * each context (0 and 1) whose picture mode is that profile, as E147 does. */
.section .wb_profile,"ax"
wb_profile:
 mov d0,d2
 mov d1,d3
 /* Monochrome Profile settings 990..1029 -> 3 + profile (0xff: none) */
 add -985,d0
 cmp 45,d0
 bcc wb_profile_color
 mov wb_mono_map,a0
 movbu (d0,a0),d0
 cmp 0xff,d0
 beq wb_profile_none
 bra wb_profile_have
wb_profile_color:
 mov d2,d0
 add -904,d0
 cmp 12,d0
 bcc wb_profile_sectors
 /* 904+4k+p: Sharpness, Contrast, Shading (k 0..2) of profile p. p = 3 is
  * Color Profile 4's cell, which E148 lacks; v0.2.0 keeps Color Profile
  * grain there: 907 / 911 / 915 = profile k (cp_nd.py, hsl.s). */
 mov d0,d1
 and 3,d0
 cmp 3,d0
 bne wb_profile_have
 lsr 2,d1
 mov d1,d0
 bra wb_profile_have
wb_profile_sectors:
 mov d2,d0
 add -928,d0
 cmp 36,d0
 bcc wb_profile_tone
 mov 12,d1
 bra wb_profile_div
wb_profile_tone:
 mov d2,d0
 add -976,d0
 cmp 9,d0
 bcc wb_profile_none
 mov 3,d1
wb_profile_div:
 mov 0,a2
wb_profile_div_loop:
 cmp d1,d0
 bcs wb_profile_divided
 sub d1,d0
 inc a2
 bra wb_profile_div_loop
wb_profile_divided:
 mov a2,d0
wb_profile_have:
 mov d0,a2
 mov d2,d0
 mov d3,d1
 call wb_original,[d2,d3,a2,a3],20
 mov d0,a3
 mov PM_ID,d0
 call stock_get,[],4
 mov a2,d1
 add 54,d1
 cmp d1,d0
 bne wb_profile_ctx1
 clr d0
 call pm_refresh,[d2],88
wb_profile_ctx1:
 mov 1,d0
 mov 2,d1
 mov PM_ID,a0
 call ctx_get,[d2],8
 mov a2,d1
 add 54,d1
 cmp d1,d0
 bne wb_profile_done
 mov 1,d0
 call pm_refresh,[d2],88
wb_profile_done:
 mov a3,d0
 ret [d2,d3,a2,a3],20
wb_profile_none:
 mov d2,d0
 mov d3,d1
 jmp wb_original
/* 985..1029: E147 SET1-3 of sharpness 990, contrast 994, grain 999, toning
 * 1003, filter 1007, level 1012, shading 1017, tone 1021 (three per profile);
 * SET4 and 985..989, 998, 1011, 1016 are not profile settings here. */
wb_mono_map:
 .byte 0xff,0xff,0xff,0xff,0xff, 3,4,5,0, 3,4,5,1, 0xff, 3,4,5,0xff
 .byte 3,4,5,0xff, 3,4,5,0xff, 0xff, 3,4,5,0xff, 0xff, 3,4,5,2
 .byte 3,3,3,4,4,4,5,5,5

/* ---- Split tone (v0.2.0-dev): tint the photo's R/G/B curve tables ----
 * Hooks the entry of E148's three-pointer curve setter 0x603e6974 (a0 = the
 * job output O, a1 / d0 / d1 = R / G / B tables, 256 x u16, 0..4095; callers
 * 0x603e6b3e and 0x603e6f0b, both call ...,[d2,a2],8). The 5 replaced bytes
 * are mov a0,a2; inc4 a2; mov d1,d2; mov d0,d1; mov (a2),d0 (replayed).
 * When armed and the active Color Profile's Split tone amount A (P+1128, set
 * by hsl.s bw_refresh, 0 in other modes) is non-zero and its buffer exists
 * (P+1132), tinted copies are built there and passed instead:
 *   u = i - 128, d = A u |u| / 2^14, R' = R + d, G' = G, B' = B - d (0..4095)
 * +A: teal shadows, orange highlights; -A the reverse; the middle unchanged.
 * The buffer is uncached heap memory owned by Caduceus; concurrent jobs write
 * identical values. research/OM5II-SPLIT-TONE-2026-11-19.md */
ST_A = 1128
ST_BUF = 1132
.section .st_hook,"ax"
 jmp st_entry
.section .wb_body,"ax"
st_entry:
 mov a0,a2
 call st_ptr,[],8
 cmp 0,a0
 beq st_replay
 movhu (ST_A,a0),d2
 exth d2
 cmp 0,d2
 beq st_replay
 mov (ST_BUF,a0),a0
 cmp 0,a0
 beq st_replay
 call st_build,[d2,d3,a2,a3],20
st_replay:
 mov a2,a0
 mov a0,a2
 inc4 a2
 mov d1,d2
 mov d0,d1
 mov (a2),d0
 jmp setter_back
/* a0 = buffer, a1 / d0 / d1 = R / G / B, d2 = A -> a1 / d0 / d1 = tinted tables */
st_build:
 mov d0,a2
 mov d1,a3
 clr d3
st_loop:
 mov d3,d0
 add -128,d0
 mov d0,d1
 mul d0,d1
 mul d2,d1
 asr 14,d1
 cmp 0,d0
 bge st_pos
 mov d1,d0
 clr d1
 sub d0,d1
st_pos:
 movhu (a1),d0
 add d1,d0
 call st_clamp,[],0
 movhu d0,(a0)
 movhu (a2),d0
 movhu d0,(512,a0)
 movhu (a3),d0
 sub d1,d0
 call st_clamp,[],0
 movhu d0,(1024,a0)
 add 2,a0
 add 2,a1
 add 2,a2
 add 2,a3
 inc d3
 cmp 256,d3
 bcs st_loop
 add -512,a0
 mov a0,a1
 mov a0,d0
 add 512,d0
 mov a0,d1
 add 1024,d1
 ret [d2,d3,a2,a3],20
st_clamp:
 cmp 0,d0
 bge st_c1
 clr d0
 retf [],0
st_c1:
 cmp 4095,d0
 ble st_c2
 mov 4095,d0
st_c2:
 retf [],0
