/* Caduceus for OM-5 Mark II (E148 1.1): the Picture Mode page graphics, loaded from the card.
 * NOT tested on a camera; exercised in OM-Emu only.
 *
 * Built by tools/mkcardblock.py into OM5MOD/CADUCEUS.BIN, linked at a fixed address (cardblock/block.ld) against
 * the flashed build's symbols, and loaded by boot.s (cb_load) into memory the firmware does not use (see
 * research/OM5II-CARD-BLOCK-2026-11-27.md). hsl.s keeps a stub of each entry with its caller's frame; these
 * bodies are the former hsl.s code, moved unchanged. The entry table must stay first: the stubs index it. */
.section .text,"ax"
cb_entries:
 .long gfx_wheel                 /* +0: hsl.s gfx_wheel stub */
 .long gfx_tone                  /* +4: gfx_tone */
 .long gfx_filter                /* +8: gfx_filter */
 .long tint_vis                  /* +12: tint_vis (hsl.s view_upd) */
 .long rgb_any_b                 /* +16: rgb_any (hsl.s tint_refresh, rgb.s) */
 .long rgb_add_b                 /* +20: rgb_add (hsl.s tn_tables, rgb.s) */
 .long rgb_alias_b               /* +24: rgb_alias (hsl.s ui_alias, rgb_ui.s) */
 .long rgb_rd_b                  /* +28: rd_get's curve point */
 .long rgb_wr_b                  /* +32: wr_set's curve point */
 .long rgb_lbl_b                 /* +36: rgb_lbl (hsl.s tone_labels) */
 .long rgb_info_b                /* +40: rgb_info_w (the tone editors' INFO) */
 .long paint_strength_b          /* +44: paint_strength (hsl.s paint_axis) */

/* ---- Colour wheel and tone curve graphics (section 5, armed only) ----
 * OM-3 draws both through its GPU layer: the page controller sends
 * guiUtility::chgBackGround DRAW_PROFILE (E147 0x612981c8, background id
 * 0xffec -> VARIOUS_DRAW_PROFILE, type 11). E148 has neither that function
 * nor the type (its table 0x6125fdf0 ends at SS_MENU, and its C3D library has
 * no profile drawing), so the restored pages have no graphic to ask for.
 * They are drawn here instead, on the OSD plane, with OM's own pen. A paint
 * context's colour is an index into the screen's 128-entry palette:
 *   pen_color 0x60d51e2c, pen_size 0x60d51eed, move_to 0x60d519e7,
 *   line_to 0x60d51774 (context +36 colour, +40/+42 size, +48 style, +32 point).
 * Every mark is an axis-aligned block: the OSD driver queues one command per
 * block but one per pixel of a slanted line, and its command buffer
 * (0x60cc647f) holds about a thousand per repaint; anything past that is
 * dropped. The context's pen is saved and put back. a2 = context throughout. */
GX = 290                        /* wheel centre */
GY = 222
G_ZERO = 84                     /* radius of value 0; 8 px per step, -7..7 */
C_WHITE = 13
C_GREY = 12
TX = 194                        /* tone box: 192 x 192, 48 columns of 4 px */
TY = 104

/* a0 = context: the colour editor's 12 values on the active axis, one spoke
 * each (ui_read; child k of the editor at +128, colour-wheel order from
 * Yellow at the top, clockwise). A spoke is a dotted scale -5..+5, a bar of
 * blocks from 0 to the value and a larger block at the value. Frame:
 * (4..23,sp) the pen, (24,sp) the value, (28,sp) the step being drawn.
 * call gfx_wheel,[d2,d3,a2,a3],48 */
gfx_wheel:
 mov a0,a2
 /* the screen's container (scr_obj -> +0) focuses the colour editor on this
  * row: the same object and checks as hsl_container */
 mov (scr_obj),a0
 cmp 0,a0
 beq gw_out
 mov (a0),a0
 cmp 0,a0
 beq gw_out
 mov (76,a0),a3
 cmp 0,a3
 beq gw_out
 movhu (120,a3),d0
 cmp 13,d0
 bne gw_out
 mov sp,a1
 add 4,a1
 call gfx_save,[],4
 clr d2
gw_loop:
 mov d2,d0
 asl2 d0
 mov a3,a0
 add d0,a0
 mov (128,a0),a0
 cmp 0,a0
 beq gw_done
 movhu (80,a0),d0
 mov d0,d1
 sub 928,d1
 cmp 48,d1
 bcc gw_done
 call ui_read,[d2,d3,a2,a3],24
 cmp -7,d0
 bge gw_lo
 mov -7,d0
gw_lo:
 cmp 7,d0
 ble gw_hi
 mov 7,d0
gw_hi:
 mov d0,(24,sp)
 /* scale: a dot per step, a larger one at 0 */
 mov C_GREY,d0
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 mov -5,d3
gw_scale:
 mov 2,d1
 cmp 0,d3
 bne gw_tick
 mov 4,d1
gw_tick:
 mov d3,d0
 call gfx_dot,[d2,d3,a2,a3],28
 inc d3
 cmp 6,d3
 blt gw_scale
 /* the selected colour (editor +122: 1..12, 0 = all) gets a white edge */
 movhu (122,a3),d0
 cmp 0,d0
 beq gw_edge
 add -1,d0
 cmp d2,d0
 bne gw_fill
gw_edge:
 mov C_WHITE,d0
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 mov (24,sp),d0
 mov 15,d1
 call gfx_dot,[d2,d3,a2,a3],28
gw_fill:
 mov gtab_col,a0
 add d2,a0
 movbu (a0),d0
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 clr d3
gw_bar:
 mov (24,sp),d0
 cmp d0,d3
 beq gw_head
 mov d3,d0
 mov 5,d1
 call gfx_dot,[d2,d3,a2,a3],28
 mov (24,sp),d0
 cmp 0,d0
 blt gw_down
 inc d3
 bra gw_bar
gw_down:
 add -1,d3
 bra gw_bar
gw_head:
 mov 11,d1
 call gfx_dot,[d2,d3,a2,a3],28
 inc d2
 cmp 12,d2
 bcs gw_loop
gw_done:
 mov sp,a1
 add 4,a1
 call gfx_restore,[],4
gw_out:
 ret [d2,d3,a2,a3],48

/* d0 = step (-7..7), d1 = size, d2 = sector 0..11 (clockwise from the top):
 * a square centred on the spoke. sin(30 i) * 64; cos i = sin(i + 3).
 * call gfx_dot,[d2,d3,a2,a3],28 */
gfx_dot:
 mov d1,d3
 asl 3,d0
 add G_ZERO,d0
 mov d0,a3                       /* radius */
 mov gtab_sin,a0
 add d2,a0
 movbu (a0),d0
 extb d0
 mov a3,d1
 mul d1,d0
 asr 6,d0
 add GX,d0
 movbu (3,a0),d1
 extb d1
 mov a3,d2
 mul d2,d1
 asr 6,d1
 not d1
 inc d1
 add GY,d1
 mov d3,d2
 lsr 1,d2
 sub d2,d0
 sub d2,d1
 mov d3,d2
 call gfx_bar,[d2,d3,a2,a3],28
 ret [d2,d3,a2,a3],28

/* Keep the context's pen in the caller's frame: a1 = 20 bytes.
 * call gfx_save,[],4 */
gfx_save:
 mov (32,a2),d0
 mov d0,(a1)
 mov (36,a2),d0
 mov d0,(4,a1)
 mov (40,a2),d0
 mov d0,(8,a1)
 mov (48,a2),d0
 mov d0,(12,a1)
 mov (640,a2),d0
 mov d0,(16,a1)
 clr d0
 movhu d0,(48,a2)                /* solid lines */
 ret [],4
/* a1 = the copy. call gfx_restore,[],4 */
gfx_restore:
 mov (a1),d0
 mov d0,(32,a2)
 mov (4,a1),d0
 mov d0,(36,a2)
 mov (8,a1),d0
 mov d0,(40,a2)
 mov (12,a1),d0
 mov d0,(48,a2)
 mov (16,a1),d0
 mov d0,(640,a2)
 ret [],4

/* sin(30 i) * 64, i = 0..14 */
gtab_sin:
 .byte 0,32,55,64,55,32,0,-32,-55,-64,-55,-32,0,32,55

/* a0 = context. Shadows / Midtones / Highlights of the selected profile
 * (976+3p.. Color, 1021+3p.. Monochrome; stored Highlights, Midtones,
 * Shadows) bend the diagonal with one bump each, centred on columns 12, 24
 * and 36 of 48; a Color Profile's Black and White lift or lower the two
 * halves (v0.2.0-dev). Frame: (4,sp) loop, (8..19,sp) the three values,
 * (20..39,sp) the pen, (40,sp) the curve at this column, (44,sp) Black,
 * (48,sp) White. call gfx_tone,[d2,d3,a2,a3],72 */
gfx_tone:
 mov a0,a2
 mov sp,a1
 add 20,a1
 call gfx_save,[],4
 mov 111,d0
 call stock_get,[],4
 sub 54,d0
 cmp 6,d0
 bcc gt_done
 clr d1
 mov d1,(44,sp)
 mov d1,(48,sp)
 cmp 3,d0
 bcc gt_mono
 mov d0,(4,sp)
 mov bw_ids,a0
 add d0,a0
 add d0,a0
 movhu (a0),d0
 call stock_get,[],4
 mov d0,(44,sp)
 mov (4,sp),d0
 mov bw_ids+6,a0
 add d0,a0
 add d0,a0
 movhu (a0),d0
 call stock_get,[],4
 mov d0,(48,sp)
 mov (4,sp),d0
gt_mono:
 mov d0,d2
 add d0,d0
 add d0,d2
 add 976,d2
 cmp 976+9,d2
 bcs gt_ids
 add 36,d2
gt_ids:
 mov 2,d3
gt_read:
 mov d2,d0
 call stock_get,[],4
 cmp -7,d0
 bge gt_lo
 mov -7,d0
gt_lo:
 cmp 7,d0
 ble gt_hi
 mov 7,d0
gt_hi:
 mov d3,d1
 asl2 d1
 mov sp,a0
 add d1,a0
 mov d0,(8,a0)
 inc d2
 add -1,d3
 bge gt_read
 mov sp,a0                       /* the RGB row: the channel's points (rgb_ui.s) */
 call rgb_gvals,[d2,d3,a2,a3],40
 /* the box with a grid at the quarters */
 mov C_GREY,d0
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 clr d0
gt_grid:
 mov d0,(4,sp)
 add TX,d0
 mov TY,d1
 mov 1,d2
 mov 193,d3
 call gfx_bar,[d2,d3,a2,a3],28
 mov (4,sp),d1
 add TY,d1
 mov TX,d0
 mov 193,d2
 mov 1,d3
 call gfx_bar,[d2,d3,a2,a3],28
 mov (4,sp),d0
 add 48,d0
 cmp 193,d0
 bcs gt_grid
 /* the unbent diagonal, dotted */
 clr d0
gt_diag:
 mov d0,(4,sp)
 mov TY+191,d1
 sub d0,d1
 add TX,d0
 mov 2,d2
 mov d2,d3
 call gfx_bar,[d2,d3,a2,a3],28
 mov (4,sp),d0
 add 12,d0
 cmp 192,d0
 bcs gt_diag
 /* the curve: each column spans its two ends */
 mov C_WHITE,d0
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 mov sp,a3
 add 8,a3
 clr d0
 mov d0,(4,sp)
 call gfx_curve,[d2,d3],16
 mov d0,(40,sp)
gt_col:
 mov (4,sp),d0
 inc d0
 call gfx_curve,[d2,d3],16
 mov (40,sp),d1                  /* d1 = this end, d0 = the next */
 mov d0,(40,sp)
 mov d0,d3
 sub d1,d3
 bge gt_up
 not d3
 inc d3
 mov d1,d0
gt_up:
 add 3,d3                        /* height; d0 = the higher end */
 mov TY+190,d1
 sub d0,d1
 mov (4,sp),d0
 asl2 d0
 add TX,d0
 mov 4,d2
 call gfx_bar,[d2,d3,a2,a3],28
 mov (4,sp),d0
 inc d0
 mov d0,(4,sp)
 cmp 48,d0
 bcs gt_col
gt_done:
 mov sp,a1
 add 20,a1
 call gfx_restore,[],4
 call tone_text,[d2,d3,a2,a3],48
 ret [d2,d3,a2,a3],72

/* d0 = column 0..48, a3 = the three values, Black at (36,a3), White at
 * (40,a3) -> d0 = height of the curve there (0..192): 4 per column plus
 * value * bump / 8, plus Black * (24 - column) or White * (column - 24)
 * times 21/128 (4 px per step at the ends). Frame: (4,sp) index.
 * call gfx_curve,[d2,d3],16 */
gfx_curve:
 mov d0,d2
 clr d3
 mov d0,d1
 mov a3,a1
gc_loop:
 cmp 25,d1
 bcc gc_skip
 mov gtab_bump,a0
 add d1,a0
 movbu (a0),d0
 mov d1,(4,sp)
 mov (a1),d1
 mul d1,d0
 add d0,d3
 mov (4,sp),d1
gc_skip:
 add 4,a1
 add -12,d1
 mov a3,a0
 add 12,a0
 cmp a0,a1
 bne gc_loop
 mov 24,d0
 sub d2,d0
 mov (36,a3),d1                  /* Black on the left half */
 cmp 0,d0
 bgt gc_bw
 not d0
 inc d0
 mov (40,a3),d1                  /* White on the right half */
gc_bw:
 mul d1,d0
 mov 21,d1
 mul d1,d0
 asr 4,d0
 add d0,d3
 asr 3,d3
 mov d2,d0
 asl2 d0
 add d3,d0
 cmp 0,d0                        /* the curve stays in the box */
 bge gc_lo
 clr d0
gc_lo:
 cmp 192,d0
 ble gc_hi
 mov 192,d0
gc_hi:
 ret [d2,d3],16

/* 16 (1 - cos(15 i)), i = 0..24 */
gtab_bump:
 .byte 0,1,2,5,8,12,16,20,24,27,30,31,32,31,30,27,24,20,16,12,8,5,2,1,0


/* a0 = context. Monochrome Profile p (111 = 57..59) only: filter 1007+p
 * (values: 0 None, 1 Yellow, 2 Orange, 3 Red, 4 Green, 5 Yellow-green,
 * 6 Magenta, 7 Blue, 8 Cyan; names 0x611b46c8). Eight 26 px swatches in the
 * dial's order round a centre block, Yellow at the top, clockwise: Yellow,
 * Orange, Red, Magenta, Blue, Cyan, Green, Yellow-green. The selected swatch
 * has a white edge and the centre block takes its colour (grey for None).
 * Frame: pen at sp+4..23, selected slot at sp+24 (8 = None).
 * call gfx_filter,[d2,d3,a2,a3],44 */
FX = 556                        /* ring centre and radius */
FY = 236
gfx_filter:
 mov a0,a2
 mov 111,d0
 call stock_get,[],4
 sub 57,d0
 cmp 3,d0
 bcc gf_out
 add 1007,d0
 call stock_get,[],4
 cmp 9,d0
 bcc gf_out
 mov ftab_slot,a0
 add d0,a0
 movbu (a0),d0
 mov d0,(24,sp)
 mov sp,a1
 add 4,a1
 call gfx_save,[],4
 clr d2
gf_loop:
 mov (24,sp),d0
 cmp d2,d0
 bne gf_swatch
 mov C_WHITE,d0
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 mov 34,d1
 call gf_block,[d2,d3,a2,a3],28
gf_swatch:
 mov ftab_col,a0
 add d2,a0
 movbu (a0),d0
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 mov 26,d1
 call gf_block,[d2,d3,a2,a3],28
 inc d2
 cmp 8,d2
 bcs gf_loop
 mov (24,sp),d2
 mov C_GREY,d0
 cmp 8,d2
 bcc gf_centre
 mov ftab_col,a0
 add d2,a0
 movbu (a0),d0
gf_centre:
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 mov 8,d2
 mov 46,d1
 call gf_block,[d2,d3,a2,a3],28
 mov sp,a1
 add 4,a1
 call gfx_restore,[],4
gf_out:
 ret [d2,d3,a2,a3],44



/* d2 = slot 0..7 round the ring, 8 = centre; d1 = size: a square block.
 * call gf_block,[d2,d3,a2,a3],28 */
gf_block:
 mov d1,d3
 mov ftab_dx,a0
 add d2,a0
 movbu (a0),d0
 extb d0
 add FX,d0
 movbu (9,a0),d1
 extb d1
 add FY,d1
 mov d3,d2
 lsr 1,d2
 sub d2,d0
 sub d2,d1
 mov d3,d2
 call gfx_bar,[d2,d3,a2,a3],28
 ret [d2,d3,a2,a3],28

/* slot offsets (45 degree steps, radius 80; then the centre) */
ftab_dx:
 .byte 0,57,80,57,0,-57,-80,-57,0
ftab_dy:
 .byte -80,-57,0,57,80,57,0,-57,0
/* swatch colours (gfx_wheel's palette indices): Yellow, Orange, Red,
 * Magenta, Blue, Cyan, Green, Yellow-green */
ftab_col:
 .byte 123,92,122,89,105,107,22,116
/* filter value 0..8 -> slot */
ftab_slot:
 .byte 8,0,1,2,6,7,3,4,5


/* ---- The Split toning pages: OM's value group hidden (2026-11-28, emulator only) ----
 * The colour view's bottom group, label 2 (the arc), 5 ("Vivid"), 6 (the
 * value) and 7 (OM's alternative to 6; hidden on every page seen), shows the
 * editor's position there (strength - 5) while paint_strength writes the
 * strength 0..10 under the title. On the tint pages (axes 3 and 5) the group
 * is hidden; Balance (axis 6, in range) and the wheel keep OM's. Label 2,
 * which OM itself never hides, marks that this code hid the group: only then
 * are 2, 5, 6 shown and 7 hidden again (as OM leaves them off "All").
 * Label 10 (the hint's frame, about 142 px) is hidden on all three Split
 * toning pages: their hint is OM-style "Split Tone [INFO]", 180 px.
 * Run after OM's own label update (hsl.s view_upd, the view's data-model
 * handler), which shows the group again on every command. a0 = the view (its
 * class is checked). call tint_vis,[d2,d3,a2,a3],24 */
TV_VIEW = 0x610c14a0            /* the colour page's view class */
TV_LABELS = 792                 /* the view's label pointers, 4 bytes each */
tint_vis:
 mov a0,a2
 cmp 0,a2
 beq tv_out
 mov (a2),d0
 cmp TV_VIEW,d0
 bne tv_out
 call st_ptr,[],8
 cmp 0,a0
 beq tv_out
 movbu (0,a0),d0                 /* ST_AXIS */
 mov d0,d2
 clr d3                          /* label 10, the hint's frame: off on the Split toning */
 cmp 3,d2                        /* pages, whose hint (IMG_SPLIT_HINT) is wider than it */
 bcc tv_frame
 mov 1,d3
tv_frame:
 mov 40,d0
 call tv_one,[d2,d3,a2],16
 mov d2,d0
 cmp 3,d0
 beq tv_hide
 cmp 5,d0
 beq tv_hide
 mov (TV_LABELS + 8,a2),a0       /* label 2: hidden only by us */
 cmp 0,a0
 beq tv_out
 mov (a0),a1
 mov (80,a1),a1
 calls (a1)
 extbu d0
 cmp 0,d0
 bne tv_out
 mov 1,d3                        /* shown: 2, 5, 6; 7 off */
 bra tv_set
tv_hide:
 clr d3
tv_set:
 mov 8,d0
 call tv_one,[d2,d3,a2],16
 mov 20,d0
 call tv_one,[d2,d3,a2],16
 mov 24,d0
 call tv_one,[d2,d3,a2],16
 mov 28,d0
 clr d3
 call tv_one,[d2,d3,a2],16
tv_out:
 ret [d2,d3,a2,a3],24
/* a2 = view, d0 = the label's offset past TV_LABELS, d3 = 0 / 1.
 * call tv_one,[d2,d3,a2],16 */
tv_one:
 add TV_LABELS,d0
 mov (d0,a2),a0
 cmp 0,a0
 beq to_out
 mov d3,d0
 call set_visible,[d2,d3,a2],16
to_out:
 ret [d2,d3,a2],16
