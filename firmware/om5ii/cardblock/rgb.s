/* Caduceus for OM-5 Mark II (E148 1.1): per-profile R / G / B curves (roadmap phase 4), in the card block.
 * NOT tested on a camera; exercised in OM-Emu only.
 *
 * The curve model is the OM-3 project's (androidfanman/caduceus-om3, research/rgbcurves/model.py on
 * try/v0.41-beta4, Apache-2.0, Copyright 2026 androidfanman): per channel 5 points at 0 / 25 / 50 / 75 / 100 % of
 * the 12-bit output, offsets -7..+7 steps of 48, a monotone cubic (Hermite, Fritsch-Butland tangents) in Q12
 * integer maths with truncating division as the CPU's div. Here it is evaluated at t = 16 k (k = 0..255) and added
 * to the split-tone delta tables (hsl.s tn_tables), which wb.s st_tint applies at each output level c >> 4. With
 * every segment 1024 wide the model's Q12 steps are exact shifts: s = 64 (k & 63), d_i = 4 (Y[i+1] - Y[i]),
 * A_i = m_i >> 2, B_i = m[i+1] >> 2. tests/rgb_curves.py holds the same arithmetic and checks it against the OM-3
 * model; tests/st_assert.mjs checks the tables the camera code builds.
 *
 * Storage (research/OM5II-RGB-CURVES-STORAGE-2026-11-28.md): nine settings E148 defines no descriptor for, the
 * fourth slots of four-wide families (a fourth Color / Monochrome Profile E148 does not have): channel c of Color
 * Profile p is rgb_ids[3p + c], read from its working cell (wc_get, 32 bits; OM's writer keeps them). All nine are
 * in OM's save, custom-mode copy and reset lists. A cell is RGB_TAG << 24 | point j's offset in bits 4j..4j+3 (two's
 * complement, -7..+7); without the tag it is a flat curve, as after OM's reset (the stock defaults -3..3). */
RGB_TAG = 0xc5
ST_BUF = 1180                   /* hsl.s: the split-tone buffer; deltas at +1552, 512 bytes a channel */
ST_P = 1541                     /* hsl.s: the profile the tables are built for (tn_pre), 3 = none */

.section .text,"ax"
.balign 2
.global rgb_ids
rgb_ids:                        /* R, G, B of Color Profile 1, 2, 3 */
 .hword 985, 986, 987, 1030, 1031, 1032, 1002, 1006, 1010

/* d3 = profile p (3.. none) -> d0 = 1 when one of its channels has a curve. From hsl.s tint_refresh, before
 * it decides whether to build the tables. call rgb_any,[d2,d3,a2,a3],24 */
.global rgb_any_b
rgb_any_b:
 clr d2
 cmp 3,d3
 bcc ra_out
 mov d3,d0
 add d0,d0
 add d3,d0
 add d0,d0
 mov rgb_ids,a3
 add d0,a3
 mov 3,d3
ra_loop:
 movhu (a3),d0
 call wc_get,[],4
 mov d0,d1
 lsr 24,d1
 cmp RGB_TAG,d1
 bne ra_next
 and 0xfffff,d0
 beq ra_next
 mov 1,d2
 bra ra_out
ra_next:
 add 2,a3
 add -1,d3
 bne ra_loop
ra_out:
 mov d2,d0
 ret [d2,d3,a2,a3],24

/* a3 = P: add each channel's curve to the delta tables tn_tables has just built (from hsl.s tn_tables, before
 * ST_A is set). Frame: (0..19,sp) Y[0..4], (20..39,sp) m[0..4], (40,sp) channel, (44,sp) its deltas, (48,sp)
 * its rgb_ids entry, (52,sp) the running sum. call rgb_add,[d2,d3,a2,a3],72 */
.global rgb_add_b
rgb_add_b:
 movbu (ST_P,a3),d0
 cmp 3,d0
 bcc rd_out
 mov d0,d1
 add d0,d0
 add d1,d0
 add d0,d0
 add rgb_ids,d0
 mov d0,(48,sp)                  /* the channel's entry in rgb_ids */
 mov (ST_BUF,a3),a2
 cmp 0,a2
 beq rd_out
 add 1552,a2
 mov a2,(44,sp)
 clr d0
 mov d0,(40,sp)
rd_chan:
 mov (48,sp),a0
 movhu (a0),d0
 call wc_get,[],4
 mov d0,d1
 lsr 24,d1
 cmp RGB_TAG,d1
 bne rd_next
 and 0xfffff,d0
 beq rd_next
 mov d0,d2                       /* Y[j] = 48 * offset j, -7..+7 */
 mov sp,a0
 mov 5,d3
rd_y:
 mov d2,d0
 and 15,d0
 cmp 8,d0
 bcs rd_pos
 add -16,d0
 cmp -7,d0
 bge rd_pos
 mov -7,d0
rd_pos:
 mov 48,d1
 mul d1,d0
 mov d0,(a0)
 add 4,a0
 lsr 4,d2
 add -1,d3
 bne rd_y
 mov (4,sp),d0                   /* m[0] = d[0], m[4] = d[3]; d[i] = 4 (Y[i+1] - Y[i]) */
 mov (0,sp),d1
 sub d1,d0
 asl2 d0
 mov d0,(20,sp)
 mov (16,sp),d0
 mov (12,sp),d1
 sub d1,d0
 asl2 d0
 mov d0,(36,sp)
 mov sp,a0                       /* m[j], j = 1..3: 0 unless d[j-1], d[j] share a sign, else 2ab / (a + b) */
 mov 1,d3
rd_m:
 mov (4,a0),d0
 mov (a0),d1
 sub d1,d0
 asl2 d0
 mov d0,d2                       /* a = d[j-1] */
 mov (8,a0),d0
 mov (4,a0),d1
 sub d1,d0
 asl2 d0                         /* b = d[j] */
 cmp 0,d2
 beq rd_m0
 cmp 0,d0
 beq rd_m0
 mov d2,d1
 xor d0,d1
 blt rd_m0
 mov d2,d1
 add d0,d1                       /* a + b */
 mul d2,d0
 add d0,d0                       /* 2ab */
 ext d0
 div d1,d0                       /* truncates toward zero, as the model's tdiv */
 bra rd_mst
rd_m0:
 clr d0
rd_mst:
 mov d0,(24,a0)                  /* m[j] at 20 + 4j */
 add 4,a0
 inc d3
 cmp 4,d3
 bcs rd_m
 mov (44,sp),a2
 clr d3
rd_k:
 mov d3,d2                       /* s = 64 (k & 63): t = 16 k in its 1024-wide segment, Q12 */
 and 63,d2
 asl 6,d2
 mov d2,d0
 mul d2,d0
 asr 12,d0
 mov d0,a0                       /* s2 */
 mul d2,d0
 asr 12,d0
 mov d0,a1                       /* s3 */
 mov d3,d0
 lsr 6,d0
 asl2 d0
 mov sp,a3
 add d0,a3                       /* (0,a3) Y[i], (4,a3) Y[i+1], (20,a3) m[i], (24,a3) m[i+1] */
 mov a1,d0                       /* h00 = 2 s3 - 3 s2 + 4096 */
 add d0,d0
 mov a0,d1
 sub d1,d0
 sub d1,d0
 sub d1,d0
 add 4096,d0
 mov (a3),d1
 mul d1,d0
 mov d0,(52,sp)
 mov a1,d0                       /* h10 = s3 - 2 s2 + s, A = m[i] >> 2 */
 mov a0,d1
 sub d1,d0
 sub d1,d0
 add d2,d0
 mov (20,a3),d1
 asr 2,d1
 mul d1,d0
 mov (52,sp),d1
 add d1,d0
 mov d0,(52,sp)
 mov a0,d0                       /* h01 = 3 s2 - 2 s3 */
 mov d0,d1
 add d0,d0
 add d1,d0
 mov a1,d1
 sub d1,d0
 sub d1,d0
 mov (4,a3),d1
 mul d1,d0
 mov (52,sp),d1
 add d1,d0
 mov d0,(52,sp)
 mov a1,d0                       /* h11 = s3 - s2, B = m[i+1] >> 2 */
 mov a0,d1
 sub d1,d0
 mov (24,a3),d1
 asr 2,d1
 mul d1,d0
 mov (52,sp),d1
 add d1,d0
 asr 12,d0                       /* D(16 k) */
 movhu (a2),d1
 exth d1
 add d1,d0
 movhu d0,(a2)
 add 2,a2
 inc d3
 cmp 256,d3
 bcs rd_k
rd_next:
 mov (44,sp),d0
 add 512,d0
 mov d0,(44,sp)
 mov (48,sp),d0
 add 2,d0
 mov d0,(48,sp)
 mov (40,sp),d0
 inc d0
 mov d0,(40,sp)
 cmp 3,d0
 bcs rd_chan
rd_out:
 ret [d2,d3,a2,a3],72
