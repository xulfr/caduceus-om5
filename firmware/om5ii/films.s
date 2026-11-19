/* Caduceus for OM-5: films (OM-5 Mark II, E148 firmware 1.1 build 1100).
 * NOT tested on a camera; exercised in OM-Emu only.
 *
 * FILM 1-3 are the camera's three restored Color Profile slots. A film is a
 * set of values for that slot's own settings: 12 x saturation / hue /
 * lightness, contrast, sharpness, shading, the tone curve and the WB shift.
 *
 *  1. Half-press (HLS_EVENT task, through hsl.s' extension vector, only once
 *     armed): read C:\OM5MOD\LOOKS.BIN (up to 833 bytes) into the heap
 *     state block P and check it. One attempt per power-on, and only with a
 *     mounted card. Nothing is written to the settings here.
 *  2. Delete on the Picture Mode screen with the highlight on a Color
 *     Profile (GUI task, the context the camera's own editors write from):
 *     that slot takes the next film of the file. The values go through the
 *     camera's own UI writer, so they are saved, travel with custom modes and
 *     reach the photo exactly as values set by hand; the card is not needed
 *     afterwards. The film's name and number are kept in three spare part-1
 *     cells of the slot.
 *  3. The string getter gives the film's name in place of "Color Profile n"
 *     while the slot holds one.
 *
 * No state is kept in the loaded image (see hsl.s). All of this file's code
 * is in section 10's loaded tail except the string getter's gate, which is in
 * section 7 beside the getter and enters section 10 only once armed (armed
 * implies all ten sections initialised). */
FL_STATE = 64                   /* 0 not tried, 1 bank loaded, 2 tried: no file / bad file */
FL_N     = 65                   /* films in the bank */
FL_BUSY  = 66                   /* a film is being written */
FL_DIRTY = 67                   /* the title label must repaint at the next page layout */
FL_NAME  = 68                   /* 3 x 26 bytes: UTF-16 names handed to the GUI */
FL_BANK  = 152                  /* the file */
FL_HDR   = 32
FL_REC   = 80                   /* 64-byte record + 16-byte name */
FL_MAX   = 10
FL_SIZE  = FL_HDR + FL_REC * FL_MAX
FL_READ  = FL_SIZE + 1           /* read one extra byte to detect an oversized file */
PANEL_ROW = 136                 /* panel updater object: kind of the highlighted row */
PANEL_TITLE = 140               /* u16: that row's title id (the mode strip: mode name or 203) */
LABEL_ID = 130                  /* text label: the string id it last laid out */
FL_TAG   = 0x464c               /* 'FL': word 0 of a slot's name cells = FL_TAG << 16 | index << 8 */

.section .hook_str,"ax"
 jmp fl_str
 nop

/* ---- section 7: the string getter's gate (stock: mov d0,d2; call lang,[],0) */
.section .ext7,"ax"
fl_str:
 mov d0,d2
 cmp 3838,d0                     /* hsl.s Split tone row title */
 beq fl_str_st
 sub 2749,d0                     /* "Color Profile 1..3", and the same with the icon prefix */
 cmp 6,d0
 bcs fl_str_cp
 mov d2,d0
 sub 2859,d0                     /* "Color Profile 1..3" (second set) */
 cmp 3,d0
 bcs fl_str_cp
fl_str_stock:
 mov d2,d0
 call str_lang,[],0
 jmp str_back
fl_str_st:
 mov st_name,a0
 ret [d2],8
fl_str_cp:
 call st_ptr,[],8
 cmp 0,a0
 beq fl_str_stock
 call fl_name,[d2,d3,a2,a3],28
 cmp 0,a0
 beq fl_str_stock
 ret [d2],8

/* ---- section 6: before the page controller lays its children out (hsl.s
 * pages_hook; a3 = the controller, child 15 = the title label). The label
 * skips a text it already shows by string id, and a film step keeps the id,
 * so after a step forget the id once. Restore the slot's title id on the
 * mode strip, where stock substitutes "Picture Mode" after a row return.
 * Preserves d0, d1, a0, a1.
 * call pg_title,[d2,d3,a2,a3],36 */
.balign 2
st_name:                         /* UTF-16 "Split Tone" for string 3838 */
 .hword 'S','p','l','i','t',' ','T','o','n','e',0
.balign 4
.global st_title
st_title:                        /* row title descriptor: string 3838 */
 .hword 4, 3838
 .long 0x611b42ac

.section .ext6,"ax"
.global pg_title
pg_title:
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 call st_ptr,[],8
 cmp 0,a0
 beq pg_t_out
 mov a0,a2
 /* Saved a0 points to the controller's RAM copy of the row descriptor:
  * u16 +0 kind, u16 +4 title id, u16 +6 the title's style index (stock
  * 0x60f05459 reads it for every kind). Only the title id may change:
  * 16-bit accesses only. Only named Color Profiles on the mode strip. */
 mov (12,sp),a0
 movhu (a0),d0
 cmp 4,d0
 bne pg_t_dirty
 /* kind 4 is any carousel row; the Film Grain row (v0.2.0) is one too.
  * The mode strip's title is the mode's name (2749+p here) or 203. */
 movhu (4,a0),d0
 call fl_strip_title,[],4
 cmp 0,d0
 bne pg_t_dirty
 mov 111,d0
 call stock_get,[],4
 sub 54,d0
 cmp 3,d0
 bcc pg_t_dirty
 mov d0,d3
 add 2749,d3
 mov a2,a0
 call fl_name,[d2,d3,a2,a3],28
 cmp 0,a0
 beq pg_t_dirty
 mov (12,sp),a0
 movhu d3,(4,a0)
pg_t_dirty:
 movbu (FL_DIRTY,a2),d0
 cmp 0,d0
 beq pg_t_out
 clr d0
 movbu d0,(FL_DIRTY,a2)
 mov a3,a0
 mov 15,d0
 call child_get,[],0
 cmp 0,a0
 beq pg_t_out
 mov -1,d0
 movhu d0,(LABEL_ID,a0)
pg_t_out:
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 ret [d2,d3,a2,a3],36

/* ---- section 10 ---- */
.section .ext10,"ax"
/* Half-press entry: `calls` from hsl.s arm_ext_call, HLS_EVENT task, armed. */
.global fl_entry
fl_entry:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp                       /* (4) file handle */
 call st_ptr,[],8
 cmp 0,a0
 beq fl_e_out
 mov a0,a2
 call cp_nd_link,[d2,d3,a2,a3],24 /* hsl.s: ND32/ND64 CP Button Settings descriptors */
 movbu (FL_STATE,a2),d0
 cmp 0,d0
 bne fl_e_out
 mov 61440,d1                    /* a medium reads MOUNT OK */
 mov (MS_A),d0
 cmp d1,d0
 beq fl_e_go
 mov (MS_B),d0
 cmp d1,d0
 beq fl_e_go
 mov (MS_C),d0
 cmp d1,d0
 bne fl_e_out
fl_e_go:
 mov 2,d0
 movbu d0,(FL_STATE,a2)          /* one attempt per power-on */
 mov fl_path,a0
 mov fl_mode,a1
 call fopen,[],4
 cmp 0,a0
 beq fl_e_out
 mov a0,(4,sp)
 mov a0,a1
 mov a2,a0
 add FL_BANK,a0
 mov 1,d0
 mov FL_READ,d1
 call fread,[d2,d3,a2,a3],24
 mov d0,d2
 mov (4,sp),a0
 call fclose,[d2,a2,a3],16
 mov d2,d0
 call fl_check,[d2,d3,a2,a3],20
 cmp 0,d0
 beq fl_e_out
 movbu d0,(FL_N,a2)
 mov 1,d0
 movbu d0,(FL_STATE,a2)
fl_e_out:
 ret [d2,d3,a2,a3],24

/* a2 = P, d0 = bytes read -> d0 = film count, 0 = not a good file. Reads only. */
fl_check:
 mov a2,a3
 add FL_BANK,a3
 mov d0,d2
 cmp FL_HDR + FL_REC,d2
 bcs fl_c_bad
 cmp FL_SIZE,d2
 bhi fl_c_bad
 mov (a3),d0
 cmp 0x46354d4f,d0               /* 'OM5F' */
 bne fl_c_bad
 mov (4,a3),d0
 cmp d2,d0
 bne fl_c_bad
 movhu (12,a3),d0
 cmp 1,d0
 bne fl_c_bad
 movhu (14,a3),d3
 cmp 0,d3
 beq fl_c_bad
 cmp FL_MAX,d3
 bhi fl_c_bad
 mov d3,d0
 mov FL_REC,d1
 mul d1,d0
 add FL_HDR,d0
 cmp d2,d0
 bne fl_c_bad
 mov a3,a0
 add 12,a0
 mov d2,d1
 add -12,d1
 call fl_crc,[d2,d3],12
 mov (8,a3),d1
 cmp d1,d0
 bne fl_c_bad
 /* every record byte the camera uses, against its range */
 mov a3,a0
 add FL_HDR,a0
 mov d3,d2
fl_c_rec:
 mov fl_lo,a1
 clr d1
fl_c_byte:
 movbu (a1),d0
 extb d0
 cmp 1,d0
 beq fl_c_next                   /* 1: not used */
 mov d0,a3                       /* lo (<= 0) */
 movbu (d1,a0),d0
 extb d0
 cmp a3,d0
 blt fl_c_bad
 cmp 0,a3
 bne fl_c_hi
 cmp 1,d0                        /* lo 0: a 0 / 1 flag */
 bgt fl_c_bad
 bra fl_c_next
fl_c_hi:
 add a3,d0                       /* v + lo <= 0 */
 cmp 0,d0
 bgt fl_c_bad
fl_c_next:
 inc a1
 inc d1
 cmp 47,d1
 bne fl_c_byte
 /* Names go through OM's formatted-text renderer. '@' starts a command,
  * not a literal character (e.g. @A034@ draws an icon). Reject commands
  * and non-printable/non-ASCII bytes before any settings are written. */
 movbu (64,a0),d0
 cmp 0,d0
 beq fl_c_bad
 mov 64,d1
fl_c_name:
 movbu (d1,a0),d0
 cmp 0,d0
 beq fl_c_name_next
 cmp 32,d0
 bcs fl_c_bad
 cmp 126,d0
 bhi fl_c_bad
 cmp 64,d0
 beq fl_c_bad
fl_c_name_next:
 inc d1
 cmp 76,d1
 bne fl_c_name
 add FL_REC,a0
 add -1,d2
 bne fl_c_rec
 mov d3,d0
 ret [d2,d3,a2,a3],20
fl_c_bad:
 clr d0
 ret [d2,d3,a2,a3],20

/* a0 = bytes, d1 = length -> d0 = CRC-32 (zlib). call fl_crc,[d2,d3],12 */
fl_crc:
 mov -1,d0
fl_crc_byte:
 movbu (a0),d2
 xor d2,d0
 mov 8,d3
fl_crc_bit:
 mov d0,d2
 and 1,d2
 lsr 1,d0
 cmp 0,d2
 beq fl_crc_skip
 xor 0xedb88320,d0
fl_crc_skip:
 add -1,d3
 bne fl_crc_bit
 inc a0
 add -1,d1
 bne fl_crc_byte
 not d0
 ret [d2,d3],12

/* Delete on the Picture Mode screen (hsl.s hsl_delete_action, GUI task).
 * call fl_delete,[d2,d3,a2,a3],44. Locals: (4) p, (8) film index, (12) loop,
 * (16) name-cell base, (20) scratch. d0 = 1 when a film was written. */
.global fl_delete
fl_delete:
 call st_ptr,[],8
 cmp 0,a0
 beq fl_d_no
 mov a0,a2
 movbu (FL_STATE,a2),d0
 cmp 1,d0
 bne fl_d_no
 movbu (FL_BUSY,a2),d0
 cmp 0,d0
 bne fl_d_no
 /* only with the highlight on the Picture Mode row: the panel's own record
  * of the row's kind (4 = the mode strip; the sliders and pages read 0) */
 mov (scr_obj),a0
 cmp 0,a0
 beq fl_d_no
 mov (4,a0),a0
 cmp 0,a0
 beq fl_d_no
 movbu (PANEL_ROW,a0),d0
 cmp 4,d0
 bne fl_d_no
 movhu (PANEL_TITLE,a0),d0       /* not the Film Grain carousel (v0.2.0) */
 call fl_strip_title,[],4
 cmp 0,d0
 bne fl_d_no
 mov 111,d0
 call stock_get,[],4
 sub 54,d0
 cmp 3,d0
 bcc fl_d_no
 mov d0,d3                       /* p */
 mov d0,(4,sp)
 mov fl_cells,a0
 add d0,d0
 movhu (d0,a0),d2
 mov d2,(16,sp)
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 mov d0,d1
 lsr 16,d1
 cmp FL_TAG,d1
 bne fl_d_first
 lsr 8,d0
 and 255,d0
 inc d0
 bra fl_d_have
fl_d_first:
 mov d3,d0                       /* an empty slot p starts on film p + 1 */
fl_d_have:
 movbu (FL_N,a2),d1
 cmp d1,d0
 bcs fl_d_idx
 clr d0
fl_d_idx:
 mov d0,(8,sp)
 mov FL_REC,d1
 mul d1,d0
 add FL_BANK + FL_HDR,d0
 mov a2,a3
 add d0,a3                       /* a3 = the film's record */
 mov 1,d0
 movbu d0,(FL_BUSY,a2)
 /* 12 sectors: saturation by the UI writer, hue / lightness as hsl.s stores them */
 clr d0
 mov d0,(12,sp)
fl_d_sec:
 mov (12,sp),d2
 mov (4,sp),d0
 mov 12,d1
 mul d1,d0
 add d2,d0
 add 928,d0
 mov d0,(20,sp)
 mov a3,a0
 add d2,a0
 movbu (24,a0),d1
 extb d1
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 mov (12,sp),d2
 mov a3,a0
 add d2,a0
 movbu (a0),d0
 and 15,d0
 movbu (12,a0),d1
 and 15,d1
 asl 4,d1
 or d1,d0
 mov d0,d1
 xor 255,d1
 asl 8,d1
 or d1,d0
 or 0x48310000,d0
 mov d0,a0
 mov (20,sp),d0
 mov 1,d1
 call active_write,[d2],8
 mov (12,sp),d0
 inc d0
 mov d0,(12,sp)
 cmp 12,d0
 bne fl_d_sec
 /* contrast, sharpness, shading, tone curve */
 clr d0
 mov d0,(12,sp)
fl_d_set:
 mov (12,sp),d2
 mov fl_ids,a0
 asl2 d2
 add d2,a0
 movbu (2,a0),d1
 mov (4,sp),d0
 mul d0,d1
 movhu (a0),d0
 add d1,d0
 movbu (3,a0),d2
 mov a3,a0
 add d2,a0
 movbu (a0),d1
 extb d1
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 mov (12,sp),d0
 inc d0
 mov d0,(12,sp)
 cmp 6,d0
 bne fl_d_set
 /* WB shift into the current WB mode's A/B and G/M: the film's own, or 0 / 0
  * for a film without one (as LookLab previews it), so a film never keeps the
  * previous film's shift. wb.s' commit hook then keeps it in this profile's
  * WB record. Byte 36 is 0 or 1 (fl_check). */
 mov 1578,d0
 call stock_get,[],4
 mov fl_wbm,a0
 clr d2
fl_d_wbm:
 movbu (d2,a0),d1
 cmp d1,d0
 beq fl_d_wb
 inc d2
 cmp 13,d2
 bne fl_d_wbm
 bra fl_d_name
fl_d_wb:
 mov d2,(12,sp)
 mov d2,d0
 add 1580,d0
 clr d1
 movbu (36,a3),d2
 cmp 0,d2
 beq fl_d_ab
 movbu (37,a3),d1
 extb d1
fl_d_ab:
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 mov (12,sp),d0
 add 1593,d0
 clr d1
 movbu (36,a3),d2
 cmp 0,d2
 beq fl_d_gm
 movbu (38,a3),d1
 extb d1
fl_d_gm:
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
fl_d_name:
 /* the name (12 characters) and the tag word, tag last */
 clr d0
 mov d0,(12,sp)
fl_d_nw:
 mov (12,sp),d2
 mov d2,d0
 asl2 d0
 mov a3,a0
 add d0,a0
 mov (64,a0),a0
 mov (16,sp),d0
 add d2,d0
 inc d0
 mov 1,d1
 call active_write,[d2],8
 mov (12,sp),d0
 inc d0
 mov d0,(12,sp)
 cmp 3,d0
 bne fl_d_nw
 mov (8,sp),d0
 asl 8,d0
 or FL_TAG << 16,d0
 mov d0,a0
 mov (16,sp),d0
 mov 1,d1
 call active_write,[d2],8
 clr d0
 movbu d0,(FL_BUSY,a2)
 /* Show it now: mark the title for repainting (pg_title, below), then run
  * the screen's own panel update, as the screen does after a press that
  * changed a value (stock 0x60ec8ea9). It re-reads the values, invalidates
  * what changed and lets the page lay itself out again. */
 mov 1,d0
 movbu d0,(FL_DIRTY,a2)
 mov (scr_obj),a0
 cmp 0,a0
 beq fl_d_done
 mov (4,a0),a0
 cmp 0,a0
 beq fl_d_done
 mov (a0),a1
 mov (a1),a1
 calls (a1)
fl_d_done:
 mov 1,d0
 ret [d2,d3,a2,a3],44
fl_d_no:
 clr d0
 ret [d2,d3,a2,a3],44

/* String getter, armed: d0 = 0..5 (profile, or 3 + profile), a0 = P -> a0 =
 * the slot's film name (UTF-16, in P) or 0. call fl_name,[d2,d3,a2,a3],28.
 * Locals (4) word index, (8) out pointer. */
fl_name:
 mov a0,a2
 cmp 3,d0
 bcs fl_n_p
 add -3,d0
fl_n_p:
 mov d0,d3
 mov fl_cells,a0
 add d0,d0
 movhu (d0,a0),d2
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 lsr 16,d0
 cmp FL_TAG,d0
 bne fl_n_none
 mov 26,d0
 mul d3,d0
 add FL_NAME,d0
 mov a2,a3
 add d0,a3                       /* a3 = out */
 mov a3,(8,sp)
 clr d0
 mov d0,(4,sp)
fl_n_word:
 mov (4,sp),d0
 add d2,d0
 inc d0
 mov 1,d1
 call active_read,[d2],8
 mov 4,d1
fl_n_char:
 mov d0,d3
 and 255,d3
 /* Older builds could persist renderer commands. Make existing names
  * literal too, without rewriting their stored settings. */
 cmp 0,d3
 beq fl_n_literal
 cmp 32,d3
 bcs fl_n_replace
 cmp 126,d3
 bhi fl_n_replace
 cmp 64,d3
 bne fl_n_literal
fl_n_replace:
 mov 63,d3
fl_n_literal:
 movhu d3,(a3)
 add 2,a3
 lsr 8,d0
 add -1,d1
 bne fl_n_char
 mov (4,sp),d0
 inc d0
 mov d0,(4,sp)
 cmp 3,d0
 bne fl_n_word
 clr d0
 movhu d0,(a3)
 mov (8,sp),a0
 movhu (a0),d0
 cmp 0,d0
 beq fl_n_none
 ret [d2,d3,a2,a3],28
fl_n_none:
 mov 0,a0
 ret [d2,d3,a2,a3],28

/* d0 = a carousel row's title id -> d0 = 0 for the Picture Mode strip of a
 * Color Profile (203 "Picture Mode", or 2749..2751 "Color Profile 1..3"),
 * else nonzero. Other carousels, such as Film Grain (2772..2775), are not. */
fl_strip_title:
 cmp 203,d0
 beq fl_st_yes
 add -2749,d0
 cmp 3,d0
 bcc fl_st_out                   /* d0 >= 3: nonzero */
fl_st_yes:
 clr d0
fl_st_out:
 ret [],4

.balign 2
fl_cells:                        /* a slot's four spare part-1 cells: tag, then 12 name bytes */
 .hword 916, 924, 972
fl_ids:                          /* u16 id for slot 1, u8 step per slot, u8 record offset */
 .hword 908
 .byte 1, 41                     /* Contrast */
 .hword 904
 .byte 1, 42                     /* Sharpness */
 .hword 912
 .byte 1, 43                     /* Shading */
 .hword 978
 .byte 3, 44                     /* Shadows */
 .hword 977
 .byte 3, 45                     /* Midtones */
 .hword 976
 .byte 3, 46                     /* Highlights */
fl_wbm:                          /* setting 1578's values in the order of the per-mode shift cells (wb.s) */
 .byte 0,18,3,1,6,17,7,8,13,14,15,16,9
fl_lo:                           /* record byte i: lowest value (highest = its negative); 0 = a 0 / 1 flag; 1 = not used */
 .byte -7,-7,-7,-7,-7,-7,-7,-7,-7,-7,-7,-7, -7,-7,-7,-7,-7,-7,-7,-7,-7,-7,-7,-7
 .byte -5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5
 .byte 0, -7,-7, 1,1, -2,-2,-5, -7,-7,-7
fl_path:
 .asciz "C:\\OM5MOD\\LOOKS.BIN"
fl_mode:
 .asciz "rb"
