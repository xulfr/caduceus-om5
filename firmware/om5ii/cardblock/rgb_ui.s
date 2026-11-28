/* Caduceus for OM-5 Mark II (E148 1.1): the RGB curves row (roadmap phase 4) and the Split toning pages'
 * strength text, in the card block. NOT tested on a camera; exercised in OM-Emu only.
 *
 * The row is OM's tone editor (item 5375) a second time, under the tone row (hsl.s RGB_ROW), as the OM-3 v0.41's
 * RGB row reuses its H&S editor. While it has the focus, the tone page's three INFO pages edit one channel's five
 * points: Hi/Sh points 3 / 1, Mid point 2, Bl/Wh points 4 / 0 (0 / 25 / 50 / 75 / 100 %); INFO from Bl/Wh goes on
 * to the next channel, R -> G -> B -> R (P+ST_CH). The values are the curve cells of rgb.s. */
RGB_TAG = 0xc5
RGB_ROW = 4
ST_TM = 1178                    /* hsl.s: 1 = the tone page's Black / White state */
ST_CH = 1542                    /* u8: the RGB row's channel, 0 R, 1 G, 2 B */
ST_RL = 1543                    /* u8: 1 while the RGB row had the focus at the last tone-page layout */

.section .text,"ax"

/* d0 = 1 when the Picture Mode panel's focused row is the RGB row (hsl.s st_split's test at index RGB_ROW; only
 * Color Profile 1..3 have that list). call rgb_row,[],4 */
rgb_row:
 mov (scr_obj),a0
 cmp 0,a0
 beq rr_no
 mov (4,a0),a0
 cmp 0,a0
 beq rr_no
 movbu (1068+RGB_ROW,a0),d0
 add -3,d0
 cmp 2,d0
 bcc rr_no
 mov 1,d0
 ret [],4
rr_no:
 clr d0
 ret [],4

/* d0 = 0..2 Color Profile p, or 3 and above none. call rgb_prof,[],4 */
rgb_prof:
 mov 111,d0
 call stock_get,[],4
 add -54,d0
 ret [],4

/* hsl.s ui_alias's tail, by jmp in its frame ([d2,d3],12; a2 and the caller's a3 are ui_read / ui_write's): d0 =
 * d2 = a setting id -> d0 = the id the UI edits. On the RGB row the tone ids 976 + 3p (Hi), 977 + 3p (Mid), 978 + 3p
 * (Sh) become 0x8000 | (3p + channel) << 4 | point; anything else goes to tone_alias. */
.global rgb_alias_b
rgb_alias_b:
 call rgb_row,[],4
 cmp 0,d0
 beq ral_tone
 call st_ptr,[],8
 cmp 0,a0
 beq ral_tone
 mov a0,a3
 call rgb_prof,[],4
 cmp 3,d0
 bcc ral_tone
 mov d0,d3
 add d0,d0
 add d0,d3                       /* 3p */
 mov d2,d0
 sub d3,d0
 add -976,d0                     /* k: 0 Hi, 1 Mid, 2 Sh */
 cmp 3,d0
 bcc ral_tone
 movbu (ST_TM,a3),d1
 cmp 0,d1
 beq ral_k
 add 3,d0
ral_k:
 mov rgb_pt,a0
 movbu (d0,a0),d0                /* the point */
 movbu (ST_CH,a3),d1
 cmp 3,d1
 bcs ral_ch
 clr d1
ral_ch:
 add d3,d1
 asl 4,d1
 or d1,d0
 or 0x8000,d0
 ret [d2,d3],12
ral_tone:
 mov d2,d0
 jmp tone_alias
rgb_pt:                         /* Hi, Mid, Sh; then in the Black / White state */
 .byte 3, 2, 1, 4, 2, 0
.balign 2

/* a0 = 0x8000 | cell << 4 | point -> d0 = the cell's cell id; d1 = 4 * point. Keeps a0. call rgb_cell,[],4 */
rgb_cell:
 mov a0,d0
 mov d0,d1
 and 15,d1
 asl2 d1
 lsr 4,d0
 and 15,d0
 add d0,d0
 mov rgb_ids,a1
 movhu (d0,a1),d0
 ret [],4

/* hsl.s rd_get (its frame [],4; ui_read restores d2, d3, a2, a3 after): a0 = pseudo id -> d0 = the point -7..+7, 0
 * without the tag. */
.global rgb_rd_b
rgb_rd_b:
 call rgb_cell,[],4
 mov d1,d2
 call wc_get,[],4
 mov d0,d1
 lsr 24,d1
 cmp RGB_TAG,d1
 bne rrd_zero
 lsr d2,d0
 and 15,d0
 cmp 8,d0
 bcs rrd_out
 add -16,d0
 cmp -7,d0
 bge rrd_out
 mov -7,d0
 bra rrd_out
rrd_zero:
 clr d0
rrd_out:
 ret [],4

/* hsl.s wr_set (its frame [d2,d3,a2,a3],20): a0 = pseudo id, d3 = the value -> the point in its cell, written with
 * OM's writer (wb.s then refreshes the profile, so the tables follow), d0 its result. */
.global rgb_wr_b
rgb_wr_b:
 cmp -7,d3
 bge rwr_lo
 mov -7,d3
rwr_lo:
 cmp 7,d3
 ble rwr_hi
 mov 7,d3
rwr_hi:
 call rgb_cell,[],4
 mov d0,a2                       /* the cell id */
 mov d1,d2                       /* the point's shift */
 call wc_get,[],4
 mov d0,d1
 lsr 24,d1
 cmp RGB_TAG,d1
 beq rwr_have
 mov 0xc5000000,d0               /* untagged: a flat curve */
rwr_have:
 mov 15,d1
 asl d2,d1
 not d1
 and d1,d0
 mov d3,d1
 and 15,d1
 asl d2,d1
 or d1,d0
 mov d0,d1
 mov a2,d0
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 ret [d2,d3,a2,a3],20

/* The tone editors' INFO, before tone_info (hsl.s rgb_info_w; entered by calls): on the RGB row, INFO from Bl/Wh
 * steps the channel R -> G -> B -> R; tone_info then takes the page back to Hi/Sh. */
.global rgb_info_b
rgb_info_b:
 movm [d2,d3,a2,a3],(sp)
 call rgb_row,[],4
 cmp 0,d0
 beq rin_out
 call st_ptr,[],8
 cmp 0,a0
 beq rin_out
 mov a0,a3
 movbu (ST_TM,a3),d0
 cmp 0,d0
 beq rin_out
 call rgb_prof,[],4
 cmp 3,d0
 bcc rin_out
 movbu (ST_CH,a3),d0
 inc d0
 cmp 3,d0
 bcs rin_set
 clr d0
rin_set:
 movbu d0,(ST_CH,a3)
rin_out:
 movm (sp),[d2,d3,a2,a3]
 rets

/* hsl.s tone_labels' tail (a2 = the tone view, after OM's labels and ours). When the focus moves between the tone
 * and RGB rows the editor stays, holding the other row's values: re-read them (tone_refresh, which reads through
 * ui_read and so through rgb_alias_b); entering the RGB row starts on Red. On the RGB row OM's value labels (sign,
 * digit) show the points (its view copies OM's tone values from its data model). call rgb_lbl,[d2,d3,a2,a3],24 */
.global rgb_lbl_b
rgb_lbl_b:
 call st_ptr,[],8
 cmp 0,a0
 beq rlb_out
 mov a0,a3
 call rgb_row,[],4
 mov d0,d3
 movbu (ST_RL,a3),d0
 cmp d0,d3
 beq rlb_vals
 movbu d3,(ST_RL,a3)
 cmp 0,d3
 beq rlb_reread
 clr d0
 movbu d0,(ST_CH,a3)
rlb_reread:
 mov (scr_obj),a0                /* the focused row's editor, as gfx_wheel finds it */
 cmp 0,a0
 beq rlb_vals
 mov (a0),a0
 cmp 0,a0
 beq rlb_vals
 mov (76,a0),a0
 cmp 0,a0
 beq rlb_vals
 mov (128,a0),a1                 /* a tone editor: child 1 edits one of 976..984 */
 cmp 0,a1
 beq rlb_vals
 movhu (80,a1),d0
 add -976,d0
 cmp 9,d0
 bcc rlb_vals
 mov a2,d2
 mov a0,a2
 call tone_refresh,[d2,d3,a2,a3],24
 mov d2,a2
rlb_vals:
 cmp 0,d3
 beq rlb_out
 call rgb_prof,[],4
 cmp 3,d0
 bcc rlb_out
 mov d0,d2
 add d0,d0
 add d0,d2
 add 976,d2                      /* Sh 978 + 3p: labels 3 / 4, Hi 976 + 3p: labels 11 / 12 (via rgb_alias_b) */
 mov d2,d0
 add 2,d0
 mov 804,d1
 call rlb_val,[d2,d3],16
 mov d2,d0
 mov 836,d1
 call rlb_val,[d2,d3],16
 mov d2,d0                       /* Mid 977 + 3p: labels 7 / 8 */
 inc d0
 mov 820,d1
 call rlb_val,[d2,d3],16
rlb_out:
 ret [d2,d3,a2,a3],24
/* a2 = view, d0 = tone id, d1 = the sign label's offset (the digit's follows): the value ui_read gives, with OM's
 * image indices (sign 0 for 0, 1 for +, 2 for -; digit |v|), as hsl.s tl_val. call rlb_val,[d2,d3],16 */
rlb_val:
 mov d1,d3
 call ui_read,[d2,d3,a2,a3],24
 mov d0,d2
 clr d0
 cmp 0,d2
 beq rlv_s
 mov 1,d0
 cmp 0,d2
 bgt rlv_s
 mov 2,d0
rlv_s:
 mov a2,a0
 add d3,a0
 mov (a0),a0
 call label_index,[d2,a2],12
 mov d2,d0
 cmp 0,d0
 bge rlv_d
 not d0
 inc d0
rlv_d:
 mov a2,a0
 add d3,a0
 mov (4,a0),a0
 call label_index,[d2,a2],12
 ret [d2,d3],16

/* gfx_tone (gfx.s), after it read the profile's values into its frame (a0 = that frame: (8) Sh, (12) Mid, (16) Hi,
 * (44) Black, (48) White; a2 = the paint context): on the RGB row the channel's five points instead, and its name
 * at the top left of the box. call rgb_gvals,[d2,d3,a2,a3],40 */
.global rgb_gvals
rgb_gvals:
 mov a0,a3
 call rgb_row,[],4
 cmp 0,d0
 beq rgv_out
 call rgb_prof,[],4
 cmp 3,d0
 bcc rgv_out
 mov d0,d2
 add d0,d0
 add d0,d2                       /* 3p */
 call st_ptr,[],8
 cmp 0,a0
 beq rgv_out
 movbu (ST_CH,a0),d0
 cmp 3,d0
 bcs rgv_ch
 clr d0
rgv_ch:
 mov d0,(4,sp)
 add d0,d2
 asl 4,d2
 or 0x8000,d2                    /* pseudo id of point 0 */
 mov d2,(12,sp)                  /* pseudo id */
 clr d0
 mov d0,(16,sp)                  /* point */
rgv_pt:
 mov (12,sp),a0
 call rgb_rd_b,[],4              /* may change d2, d3 */
 mov (16,sp),d1
 mov rgv_slot,a1
 movbu (d1,a1),d1
 mov a3,a0
 add d1,a0
 mov d0,(a0)
 mov (12,sp),d0
 inc d0
 mov d0,(12,sp)
 mov (16,sp),d0
 inc d0
 mov d0,(16,sp)
 cmp 5,d0
 bcs rgv_pt
 mov (4,sp),d0                   /* "Red" / "Green" / "Blue" */
 mov d0,d1
 asl 3,d0
 add d1,d0
 add d1,d0
 add d1,d0
 add d1,d0                       /* 12 bytes a name */
 mov rgv_names,a1
 add d0,a1
 mov 200,d0
 mov 108,d1
 mov 80,d2
 call tx_draw,[d2,d3,a2,a3],44
rgv_out:
 ret [d2,d3,a2,a3],40
rgv_slot:                       /* points 0..4 -> Black, Sh, Mid, Hi, White */
 .byte 44, 8, 12, 16, 48
.balign 2
rgv_names:
 .short 'R','e','d',0,0,0
 .short 'G','r','e','e','n',0
 .short 'B','l','u','e',0,0

/* ---- The Split toning pages' strength text (moved from hsl.s .ext5, 2026-11-28, for the RGB row's room) ----
 * the strength 0..10 of the colour under the cursor, as text under the title. OM's value label has pictures for
 * -5..+5 only and shows the editor's own position there (strength - 5); it is not pushed out of its range. a2 =
 * tx_draw's context, d3 = axis. call paint_strength,[d2,d3,a2,a3],24 (hsl.s stub) */
.global paint_strength_b
paint_strength_b:
 cmp 3,d3
 bcs ps_out
 cmp 6,d3                        /* Balance: OM's label shows it (-5..+5) */
 beq ps_out
 mov 111,d0
 call stock_get,[],4
 add -54,d0
 cmp 3,d0
 bcc ps_out
 mov d0,d2                       /* p */
 mov 2201,d0                     /* the cursor: 928 + 12p + k, else colour 1 */
 add d2,d0
 call stock_get,[],4
 add -928,d0
 mov 12,d1
 mul d2,d1
 sub d1,d0
 cmp 12,d0
 bcs ps_k
 clr d0
ps_k:
 mov d0,a3                       /* k */
 mov d3,d0                       /* the tint cell: tint_ids[3 (axis - 3) + p] */
 add -3,d0
 mov d0,d1
 add d1,d0
 add d1,d0
 add d2,d0
 add d0,d0
 mov tint_ids,a0
 add d0,a0
 movhu (a0),d0
 call stock_get,[],4
 extbu d0
 mov d0,d1
 and 15,d1
 mov a3,a0
 cmp a0,d1
 bne ps_zero
 lsr 4,d0
 cmp 11,d0
 bcs ps_text
ps_zero:
 clr d0
ps_text:
 mov d0,d1                       /* 6 bytes a string */
 add d1,d0
 add d1,d0
 add d0,d0
 mov strength_text,a1
 add d0,a1
 mov 600,d0
 mov 56,d1
 mov 60,d2
 call tx_draw,[d2,d3,a2,a3],44
ps_out:
 ret [d2,d3,a2,a3],24
.balign 2
strength_text:
 .short '0',0,0, '1',0,0, '2',0,0, '3',0,0, '4',0,0, '5',0,0
 .short '6',0,0, '7',0,0, '8',0,0, '9',0,0, '1','0',0
