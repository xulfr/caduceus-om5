/* OM-5 Mark II 1.1 (E148, build 1100) HSL editor and builder overlay, ported
 * from the OM-3 patch. NOT tested on a camera; exercised in OM-Emu only.
 * Code and state live in the FF tails inside the loaded extents of sections 2,
 * 6, 7 and 8. E148 loads all ten sections once at boot (8 before 2) and never clears their
 * completion bits (finalizer 0x600464d0, bits 0xa26e2694). See README.md. */
/* Runtime state is NOT kept in the loaded image. Stock E148 makes no absolute
 * store into it, and the 8 November camera failure began at the first such
 * stores this patch made (research/OM5II-IMAGE-STORE-FAULT-2026-11-11.md).
 * State lives in a 1040-byte heap block "P" (stock malloc, class-1 pool,
 * uncached alias), allocated once on the first shutter half-press after boot.
 * Its handle is the padding halfword after the HLS event manager's task id
 * (.bss, zero at power-on). Until then every hook behaves as stock.
 *   P+0 axis (0 saturation, 1 hue, 2 lightness)   P+4 colour editor object
 *   P+8 reset-in-progress flag                    P+12 WB commit busy flag
 *   P+16..55 axis label text (UTF-16)             P+56 unused (was: repaint flag)
 *   P+64.. reserved (Caduceus) */
ST_AXIS = 0
ST_EDITOR = 4
ST_RESET = 8
ST_BUSY = 12
ST_LABEL = 16
ST_SIZE = 1544                  /* the heap block P; 1024 before the Shading descriptors' nodes, 1040 before CP grain's, 1136 with the Blacks/Whites/Split tone rows, 1528 before gs_hook's table */
/* v0.2.0-dev fields of P (after the 23 descriptor nodes at P+988..1171): */
BW_B = 1172                     /* s16 Blacks of the active Color Profile, curve units */
BW_W = 1174                     /* s16 Whites: positive lowers the white end */
ST_A = 1176                     /* s16: 1 while the split-tone delta tables are valid (wb.s st_tint) */
ST_TM = 1178                    /* byte: 1 = the tone page's Black / White state */
ST_HINT = 1179                  /* byte: 1 = the tone hint shows IMG_HINT, tone_text writes Bl/Wh */
ST_BUF = 1180                   /* split-tone buffer: 3 x 512 output tables, 16 bytes, 3 x 512 deltas */
TINT_T = 1184                   /* 9 s16: tint of zone z (shadows, midtones, highlights), channel c (R, G, B) */
ST_BUF_SIZE = 3088
CAD_DESC = 1204                 /* 15 x 20: the Black / White and tint descriptors (cad_build) */
GS_GEN = 1504                   /* u32: +1 at each rebuild of the Black / White and tint tables */
GS_TAB = 1508                   /* 4 x {gamma cache, GS_GEN it last saw} (gs_hook) */
ST_MAGIC = 60                   /* P+60: 'CADU' once the block is initialised */
ST_MAGIC_VALUE = 0x55444143
.section .arm_hook,"ax"
 jmp arm_hook
/* INFO keeps its native individual/all role. Delete (trash) switches axis:
 * the colour-direct screen forwards its native 0x9016 command to the focused
 * widget, and the colour page container consumes it for the colour editor. */
.section .delete_pointer,"a"
 .long hsl_delete_action
.section .label_hook,"ax"
 jmp label_get
 .fill 5,1,0xcb
.section .container_pointer,"a"
 .long hsl_container
.section .reset_hook,"ax"
 jmp reset_hook
 nop
.section .read_hook,"ax"
 jmp read_hook
 nop
 nop
.section .write_hook,"ax"
 jmp write_hook
 nop
 nop
.section .display_hook,"ax"
 jmp display_hook
 nop
 nop
.section .builder_hook,"ax"
 jmp builder_hook
.section .parent_hook,"ax"
 jmp parent_hook
.section .paint_pointer,"a"
 .long paint_axis
.section .tone_pointer,"a"
 .long paint_tone
.section .filter_pointer,"a"
 .long paint_filter
.section .cp_any_hook,"ax"
 call cp_any_nd,[],4
.section .pages_hook,"ax"
 jmp pages_hook
 nop
 nop

.section .ext7,"ax"
/* Action-table entry of the SCP direct-setting screen for the Delete press
 * (0x9016). Stock ignores it unless setting 2163 is 1. Only in screen state
 * 0x0418 (colour/picture-mode direct page) forward it to the focused widget,
 * as the same screen already does for INFO. Elsewhere: stock. */
hsl_delete_action:
 add -24,sp
 mov d0,(20,sp)
 mov d1,(4,sp)
 mov a0,(8,sp)
 mov a1,(12,sp)
 clr d1
 mov d1,(16,sp)
 movbu (a0),d0
 cmp 4,d0
 bne delete_restore
 movbu (1,a0),d0
 cmp 24,d0
 bne delete_restore
 mov 2163,d0
 call stock_get,[],4
 cmp 1,d0
 beq delete_restore
 mov 1,d0
 mov d0,(16,sp)
 /* Forward to the focused widget, as before. The colour editor consumes the
  * press by switching its axis (hsl_container). When it did not, the press
  * steps the Color Profile slot's film (Caduceus films, films.s): nothing
  * unless armed, a film file is loaded and the mode is Color Profile 1-3. */
 call st_axis,[],12
 mov d0,(16,sp)
 mov (4,sp),d1
 mov (8,sp),a0
 mov (12,sp),a1
 mov 0x9016,d0
 calls screen_forward
 mov d0,(20,sp)
 call st_axis,[],12
 mov (16,sp),d1
 cmp d1,d0
 bne delete_done
 /* Section 10 loads last. Check the published state before branching there. */
 call st_ptr,[],8
 cmp 0,a0
 beq delete_done
 call fl_delete,[d2,d3,a2,a3],44
 cmp 0,d0
 beq delete_done
 /* A film step is user activity: restart the screen's timeout (films.s) */
 call ui_film_activity,[d2,d3,a2,a3],24
delete_done:
 mov (20,sp),d0
 add 24,sp
 rets
delete_restore:
 mov (4,sp),d1
 mov (8,sp),a0
 mov (12,sp),a1
delete_stock:
 mov (20,sp),d0
 add 24,sp
 jmp stock_delete_action

/* Colour page container command method (vtable entry 0). Stock forwards INFO
 * to its focused child but drops 0x9016. Consume 0x9016 only when that child
 * is the 13-child colour editor whose cursor is a colour-selection setting. */
hsl_container:
 cmp 0x9014,d0
 beq container_info
 cmp 0x9016,d0
 bne container_stock
 add -4,sp
 mov a0,(sp)
 mov (76,a0),a0
 cmp 0,a0
 beq container_restore
 movhu (120,a0),d0
 cmp 13,d0
 bne container_restore
 mov (124,a0),a1
 cmp 0,a1
 beq container_restore
 movhu (80,a1),d0
 sub 2197,d0
 cmp 8,d0
 bcc container_restore
 mov (sp),a1                     /* the container */
 add 4,sp
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov a1,(4,sp)
 mov a0,a2
 call st_ptr,[],8
 cmp 0,a0
 beq container_unarmed
 mov a2,(ST_EDITOR,a0)
 movbu (ST_AXIS,a0),d0
 inc d0
 cmp 6,d0                        /* Saturation, Hue, Lightness, Shadow / Midtone / Highlight tint */
 bcs container_axis
 clr d0
container_axis:
 movbu d0,(ST_AXIS,a0)
 /* A tint is one colour: arriving on a tint axis with "all" selected
  * (parent +122 = 0), switch to one colour with OM's own INFO. */
 cmp 3,d0
 bcs container_refresh
 movhu (122,a2),d0
 cmp 0,d0
 bne container_refresh
 mov (4,sp),a0
 mov 0x9014,d0
 calls stock_container
container_refresh:
 call refresh_children,[d2,d3,a2,a3],24
 mov (124,a2),a0
 mov 0x900c,d0
 clr d1
 mov (a0),a1
 mov (a1),a1
 calls (a1)
 /* The axis title and wheel are painted by the colour page's view, which
  * pages_hook invalidates when the panel lays out after this press. Count
  * the press as activity, as stock does for a command its child consumed. */
 mov (4,sp),a0
 call ui_activity,[d2,d3],12
container_unarmed:
 mov 1,d0
 ret [d2,d3,a2,a3],24
container_restore:
 mov (sp),a0
 add 4,sp
 mov 0x9016,d0
container_stock:
 jmp stock_container
/* INFO: section 2 (container_info2), for space. */
container_info:
 jmp container_info2

/* The native value label (stock "Vivid +n", 0x60e4ad08..0x60e4ae5e) reads the
 * selected sector's stored profile cell (IDs 928-975) through the settings
 * object's getter into (36,sp). Re-run that call, then substitute the active
 * H/L value. Runs in the caller frame; replaces calls (a2) + the next two
 * instructions, which are replayed. */
label_get:
 calls (a2)
 call st_axis,[],12
 cmp 0,d0
 beq label_get_done
 mov d2,d0
 exthu d0
 sub 928,d0
 cmp 48,d0
 bcc label_get_done
 mov d2,d0
 exthu d0
 call ui_read,[d2,d3,a2,a3],24
 mov d0,(36,sp)
label_get_done:
 mov (12,sp),d0
 mov label_format,a1
 jmp label_resume

/* During the native reset command, the stock saturation defaults are not
 * H/L defaults: reset the active experimental axis to zero instead. */
reset_hook:
 call st_reset_on,[d2,a2],12
 mov (a0),a1
 mov (a1),a1
 calls (a1)
 call st_reset_off,[d2,a2],12
 jmp reset_resume

/* Capture only the 13-child colour editor parent; every pointer is checked
 * again before use. This replaces two stock setup instructions. */
parent_hook:
 add -12,sp
 mov d0,(8,sp)
 mov a1,(4,sp)
 movhu (120,a0),d0
 cmp 13,d0
 bne parent_restore
 mov (124,a0),a1
 cmp 0,a1
 beq parent_restore
 movhu (80,a1),d0
 sub 2197,d0
 cmp 8,d0
 bcc parent_restore
 call st_set_editor,[a2],8
parent_restore:
 mov (8,sp),d0
 mov (4,sp),a1
 add 12,sp
 mov a0,a2
 mov 0,a3
 mov 1,d3
 jmp parent_resume

/* Refresh the native enum indices so a new axis starts at its own value. */
refresh_children:
 call st_ptr,[],8
 cmp 0,a0
 beq refresh_done
 mov (ST_EDITOR,a0),a2
 cmp 0,a2
 beq refresh_done
 movhu (120,a2),d0
 cmp 13,d0
 bne refresh_done
 add 128,a2
 clr d3
refresh_loop:
 mov (a2),a3
 cmp 0,a3
 beq refresh_done
 movhu (80,a3),d0
 mov d0,d1
 sub 928,d1
 cmp 48,d1
 bcc refresh_done
 movhu (92,a3),d1
 cmp 11,d1
 bne refresh_done
 call ui_read,[d2,d3,a2,a3],24
 /* A cell may hold -7..7 (set from a look); the editor's list has -5..5.
  * Show the nearest entry rather than abandoning the refresh. */
 cmp -5,d0
 bge refresh_low_ok
 mov -5,d0
refresh_low_ok:
 cmp 5,d0
 ble refresh_high_ok
 mov 5,d0
refresh_high_ok:
 mov 5,d1
 sub d0,d1
 movhu d1,(94,a3)
 add 4,a2
 inc d3
 cmp 12,d3
 bne refresh_loop
refresh_done:
 ret [d2,d3,a2,a3],24

/* This color-wheel view's paint method wraps the stock child painter.
 * Context layout is based on the matching OM-3 draw API, not PEN-F addresses. */
paint_axis:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov a0,a2
 mov a1,(20,sp)
 call stock_paint,[a2,a3],16
 mov (20,sp),a1
 add -40,sp
 mov a1,(20,sp)
 mov d0,(16,sp)
 cmp 0,a1
 beq paint_done
 call st_ptr,[],8
 cmp 0,a0
 beq paint_done
 add ST_LABEL,a0
 mov a0,(56,sp)
 mov (20,sp),a1
 movhu (4,a1),d0
 cmp 2,d0
 bne paint_done
 mov (8,a1),a3
 cmp 0,a3
 beq paint_done
 mov (808,a2),a1
 cmp 0,a1
 beq paint_done
 movhu (8,a1),d0
 add 24,d0
 mov d0,(24,sp)
 /* Draw with the caller's paint context in place. stock_font only sets its
  * font at +76 (0x60d51fa2) and the style below changes +52; both are put
  * back afterwards. (OM-3 copied 684 bytes of context to the stack.) */
 movhu (52,a3),d0
 mov d0,(48,sp)
 mov (76,a3),d0
 mov d0,(52,sp)
 mov a3,a0
 mov 1,d0
 call stock_font,[a2],8
 cmp 0,a0
 beq paint_restore
 mov a0,(32,sp)
 mov 2,d0
 movhu d0,(52,a3)
 mov (24,sp),d0
 add -100,d0
 movhu d0,(40,sp)
 add 199,d0
 movhu d0,(44,sp)
 mov 16,d0
 movhu d0,(42,sp)
 mov 47,d0
 movhu d0,(46,sp)
 mov (56,sp),a0
 call make_axis_label,[d2,d3,a2,a3],24
 mov (56,sp),d1
 mov a3,a0
 mov sp,a1
 add 40,a1
 mov text_style,d0
 call stock_text,[d2,d3,a2,a3],16
 mov (24,sp),d0
 add -100,d0
 movhu d0,(40,sp)
 add 199,d0
 movhu d0,(44,sp)
 mov 50,d0
 movhu d0,(42,sp)
 mov 81,d0
 movhu d0,(46,sp)
 mov text_switch,d1
 mov a3,a0
 mov sp,a1
 add 40,a1
 mov text_style,d0
 call stock_text,[d2,d3,a2,a3],16
 mov (32,sp),a0
 call stock_font_release,[],4
paint_restore:
 mov a3,a0
 call gfx_wheel,[d2,d3,a2,a3],48
 call wheel_swatch,[d2,d3,a2,a3],28   /* ext9: a2 = the view, a3 = context */
 mov (48,sp),d0
 movhu d0,(52,a3)
 mov (52,sp),d0
 mov d0,(76,a3)
paint_done:
 mov (16,sp),d0
 add 64,sp
 ret [d2,d3,a2,a3],16

/* Axis title: Saturation / Hue / Lightness. The selected value is shown by
 * the native value label, which follows the active axis. */
make_axis_label:
 mov a0,a2
 call st_axis,[],12
 mov d0,d3
 mov text_saturation,a1
label_skip:                      /* the axis' name is the d3-th of the list */
 cmp 0,d3
 beq label_copy
label_skip_ch:
 movhu (a1),d0
 add 2,a1
 cmp 0,d0
 bne label_skip_ch
 add -1,d3
 bra label_skip
label_copy:
 movhu (a1),d0
 movhu d0,(a2)
 add 2,a1
 add 2,a2
 cmp 0,d0
 bne label_copy
 ret [d2,d3,a2,a3],24
.balign 4
text_style:
 .long 10,15,15
 .byte 1,1
 .short 0,0,0,0,0
text_saturation:
 .short 'S','a','t','u','r','a','t','i','o','n',0
text_hue:
 .short 'H','u','e',0
text_lightness:
 .short 'L','i','g','h','t','n','e','s','s',0
 .short 'S','h','a','d','o','w',' ','T','i','n','t',0
 .short 'M','i','d','t','o','n','e',' ','T','i','n','t',0
 .short 'H','i','g','h','l','i','g','h','t',' ','T','i','n','t',0

.section .ext6,"ax"
read_hook:
 call ui_read,[d2,d3,a2,a3],24
 jmp read_resume
ui_read:
 mov d0,d2
 call ui_alias,[d2,d3],12        /* the tone page's Black / White state */
 cmp d0,d2
 bne ui_read_alias
 sub 928,d0
 cmp 48,d0
 bcc ui_read_stock
 call st_axis,[],12
 mov d0,d3
 cmp 3,d3
 bcc ui_read_tint
 cmp 1,d3
 beq ui_read_alt
 cmp 2,d3
 bne ui_read_stock
ui_read_alt:
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 call decode,[],4
 cmp 1,d3
 bne read_light
 asl 28,d0
 bra read_signed
read_light:
 asl 24,d0
read_signed:
 asr 28,d0
 ret [d2,d3,a2,a3],24
ui_read_alias:
 mov d0,d2
ui_read_stock:
 mov d2,d0
 call stock_get,[],4
 ret [d2,d3,a2,a3],24
ui_read_tint:
 jmp tint_read

write_hook:
 call ui_write,[d2,d3,a2,a3],24
 jmp write_resume
ui_write:
 mov d0,d2
 mov d1,d3
 mov a0,a2
 call ui_alias,[d2,d3],12
 cmp d0,d2
 bne ui_write_alias
 sub 928,d0
 cmp 48,d0
 bcc ui_write_stock
 call st_axis,[],12
 cmp 3,d0
 bcc ui_write_tint
 cmp 1,d0
 beq ui_write_alt
 cmp 2,d0
 bne ui_write_stock
ui_write_alt:
 mov ST_RESET,d0
 call st_getb,[],12
 cmp 0,d0
 beq write_not_reset
 clr d3
write_not_reset:
 cmp -5,d3
 blt ui_write_end
 cmp 5,d3
 bgt ui_write_end
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 call decode,[],4
 mov d3,d1
 and 15,d1
 mov d0,a2
 call st_axis,[],12
 mov d0,d3
 mov a2,d0
 cmp 1,d3
 beq write_hue
 and 15,d0
 asl 4,d1
 bra write_merge
write_hue:
 and 240,d0
write_merge:
 or d1,d0
 mov d0,d1
 xor 255,d1
 asl 8,d1
 or d1,d0
 or 0x48310000,d0
 mov d0,a0
 mov d2,d0
 mov 1,d1
 call active_write,[d2],8
ui_write_end:
 mov 1,d0
 ret [d2,d3,a2,a3],24
ui_write_tint:
 jmp tint_write
ui_write_alias:
 mov d0,d2
ui_write_stock:
 mov d2,d0
 mov d3,d1
 mov a2,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 ret [d2,d3,a2,a3],24

/* Wheel values: the reader 0x60a339e4, descriptor kind 6 (Color Profile),
 * leaves 12 sector bytes at a2 = sp+88 and the profile (setting 903) in d2.
 * Replaces the 7-byte call at the shared tail 0x60a33eac. */
display_hook:
 call st_axis,[],12
 cmp 0,d0
 beq display_stock
 cmp 3,d0
 bcc display_stock
 mov (a3),d0
 cmp 6,d0
 bne display_stock
 mov sp,a0
 add 88,a0
 cmp a2,a0
 bne display_stock
 call display_values,[d2,d3,a2,a3],24
display_stock:
 call stock_display_next,[],4
 jmp display_resume
display_values:
 call st_axis,[],12
 mov d0,d3
 mov d2,d0
 exthu d0
 sub 1,d0
 cmp 3,d0
 bcs display_profile
 clr d0
display_profile:
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 2,d0
 add 928,d0
 mov d0,d2
 mov 12,a3
display_loop:
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 call decode,[],4
 cmp 1,d3
 bne display_light
 asl 28,d0
 bra display_signed
display_light:
 asl 24,d0
display_signed:
 asr 28,d0
 movbu d0,(a2)
 inc a2
 inc d2
 add -1,a3
 cmp 0,a3
 bne display_loop
 ret [d2,d3,a2,a3],24


/* E148 keeps the Color Profile detail pages but no longer shows them: the
 * picture-mode direct screen creates children 2-5 and its visibility updater
 * (0x60dad4eb) never touches them. E147 shows them from its data-275 flags
 * (0x611358eb..0x61135a23). E148's data-277 struct still carries the focus
 * flags: +245 colour item, +247 tone item (E147 offsets - 32). This replaces
 * the updater's last call (0x60dad5f5) and then shows child 4 (colour wheel)
 * or child 2 (tone curve) for Color Profile 1-3 only. Registers: d2 = data
 * struct, a3 = direct-screen controller; the stock ret restores them. */
pages_hook:
 call pg_title,[d2,d3,a2,a3],36      /* films.s: repaint the title after a film step */
 call direct_layout,[d2,d3,a2,a3],160
 /* Not armed (no half-press since power-on): the stock updater only. The
  * detail pages are created hidden and nothing else shows them. */
 call st_ptr,[],8
 cmp 0,a0
 bne pages_armed
 jmp direct_ret
pages_armed:
 mov 111,d0
 call stock_get,[],4
 sub 54,d0
 cmp 6,d0
 bcc pages_off
 /* E147 shows child 5/4/3/2 from +276..+279 (E148 +244..+247); the
  * Monochrome Profile items use 5 and 3, Color Profile 4 and 2. */
 mov d2,a0
 movbu (244,a0),d0
 mov 5,d1
 call show_page,[d2,d3,a2,a3],24
 mov d2,a0
 movbu (245,a0),d0
 mov 4,d1
 call show_page,[d2,d3,a2,a3],24
 mov d2,a0
 movbu (246,a0),d0
 mov 3,d1
 call show_page,[d2,d3,a2,a3],24
 mov d2,a0
 movbu (247,a0),d0
 mov 2,d1
 call show_page,[d2,d3,a2,a3],24
 call pg_axis,[d2,d3,a2,a3],24
 jmp direct_ret
pages_off:
 clr d0
 mov 5,d1
 call show_page,[d2,d3,a2,a3],24
 clr d0
 mov 4,d1
 call show_page,[d2,d3,a2,a3],24
 clr d0
 mov 3,d1
 call show_page,[d2,d3,a2,a3],24
 clr d0
 mov 2,d1
 call show_page,[d2,d3,a2,a3],24
 jmp direct_ret

/* The colour page's view paints the axis title and the wheel, the tone page's
 * the curve, and OM invalidates neither when a value, the selected colour or
 * the axis changes (only the label that changed). Each panel layout that
 * shows one of them (flag +245 colour, +247 tone, +246 Monochrome colour
 * filter) invalidates that page (child 4 / 2 / 3) with OM's widget invalidate (d0 = 1, a1 = 0: the
 * widget's whole area, as a label does in 0x60d8df09..0x60d8df13). The layout
 * runs once per consumed command. d2 = data struct, a3 = controller.
 * call pg_axis,[d2,d3,a2,a3],24 */
pg_axis:
 mov d2,a0
 movbu (245,a0),d0
 mov 4,d1
 cmp 1,d0
 beq pg_inval
 movbu (247,a0),d0
 mov 2,d1
 cmp 1,d0
 beq pg_tone
 movbu (246,a0),d0               /* Monochrome colour filter page */
 mov 3,d1
 cmp 1,d0
 bne pg_axis_out
pg_inval:
 mov a3,a0
 mov d1,d0
 call child_get,[],0
 cmp 0,a0
 beq pg_axis_out
 mov 0,a1
 mov 1,d0
 call ui_invalidate,[],4
pg_axis_out:
 ret [d2,d3,a2,a3],24
pg_tone:                         /* the tone page: its labels follow the Black / White state */
 mov a3,a0
 mov 2,d0
 call child_get,[],0
 cmp 0,a0
 beq pg_axis_out
 call tone_labels,[d2,d3,a2,a3],24
 mov 2,d1
 bra pg_inval

/* d0 = flag byte, d1 = child index, a3 = controller */
show_page:
 mov d0,d2
 cmp 1,d2
 beq show_on
 clr d2
show_on:
 mov a3,a0
 mov d1,d0
 call child_get,[],0
 cmp 0,a0
 beq show_done
 mov a0,a2
 cmp 0,d2
 beq show_set
 call page_layout,[d2,d3,a2,a3],24
show_set:
 mov a2,a0
 mov d2,d0
 call set_visible,[d2,d3,a2],16
show_done:
 ret [d2,d3,a2,a3],24

/* The pages carry the OM-1/OM-3 layout (900x600 content on an 800x600 page).
 * E148's panels are 720x480, exactly 4/5 of it: scale the page and its view,
 * and move each label so its centre scales (its size and font stay). Runs once
 * per page: a scaled page is at most 720 wide. a0 = page. */
page_layout:
 mov a0,a2
 mov (36,a2),a3
 cmp 0,a3
 beq layout_done
 mov 12,d2
 mov (a3),d0
 cmp 0x610c14a0,d0
 beq layout_view
 mov 18,d2
 cmp 0x610d6560,d0
 beq layout_view
 /* Monochrome Profile pages: child 3 (colour filter, labels 1..9) and
  * child 5 (labels 1..2); same 900x600 OM-1/OM-3 layout */
 mov 10,d2
 cmp 0x610d9b20,d0
 beq layout_view
 mov 3,d2
 cmp 0x610dd9f8,d0
 bne layout_done
layout_view:
 movhu (12,a2),d0
 cmp 720,d0
 bls layout_done
 movhu (12,a3),d1
 cmp d1,d0
 bcc layout_w
 mov d1,d0
layout_w:
 call scale,[],4
 movhu d0,(12,a2)
 movhu (14,a2),d0
 movhu (14,a3),d1
 cmp d1,d0
 bcc layout_h
 mov d1,d0
layout_h:
 call scale,[],4
 movhu d0,(14,a2)
 mov a2,a1
 call scale_pos,[],4
 mov a3,a1
 call scale_pos,[],4
 movhu (12,a3),d0
 call scale,[],4
 movhu d0,(12,a3)
 movhu (14,a3),d0
 call scale,[],4
 movhu d0,(14,a3)
 clr d3
layout_child:
 mov a3,a0
 add 792,a0
 mov d3,d0
 asl2 d0
 mov (d0,a0),a1
 cmp 0,a1
 beq layout_next
 call centre1,[],4
 add 2,a1
 call centre1,[],4
layout_next:
 inc d3
 cmp d2,d3
 bcs layout_child
layout_done:
 ret [d2,d3,a2,a3],24

/* a1 = view: scale x, y */
scale_pos:
 movhu (8,a1),d0
 call scale,[],4
 movhu d0,(8,a1)
 movhu (10,a1),d0
 call scale,[],4
 movhu d0,(10,a1)
 ret [],4

/* a1 -> position at (8,a1), size at (12,a1): keep size, scale the centre */
centre1:
 movhu (8,a1),d0
 exth d0
 add d0,d0
 movhu (12,a1),d1
 add d1,d0
 call scale,[],4
 movhu (12,a1),d1
 sub d1,d0
 asr 1,d0
 movhu d0,(8,a1)
 ret [],4

/* d0 = d0 * 4/5 (signed halfword in, 0xccd/4096) */
scale:
 exth d0
 mov 0xccd,d1
 mul d1,d0
 asr 12,d0
 ret [],4

/* Section 2 loads before all callers of these gates. wb.ld binds st_ptr. */
.section .ext2,"ax"
/* a0 = P, or 0 when not armed / handle out of range. call st_ptr,[],8.
 * Preserves d0-d3, a1-a3. */
.global st_ptr
st_ptr:
 mov d0,(4,sp)
 /* The handle is read from RAM (uncached alias): hooks may run on another
  * CPU, whose cache need not hold what the arming CPU wrote. A handle counts
  * only if it is in the pool, the block is 4-aligned and carries the magic
  * arm_gate wrote, so a stale or foreign value reads as "not armed". */
 movhu (st_handle_u),d0
 cmp 0,d0
 beq st_ptr_none
 cmp ST_HANDLE_MAX,d0
 bhi st_ptr_none
 add ST_POOL-1,d0
 mov d0,a0
 and 3,d0
 bne st_ptr_none
 mov (ST_MAGIC,a0),d0
 cmp ST_MAGIC_VALUE,d0
 beq st_ptr_out
st_ptr_none:
 mov 0,a0
st_ptr_out:
 mov (4,sp),d0
 ret [],8
/* d0 = byte P+0 (axis) / P+d0, or 0 when not armed. call ...,[],12.
 * Preserves everything else. */
st_axis:
 clr d0
st_getb:
 mov a0,(4,sp)
 mov d0,(8,sp)
 call st_ptr,[],8
 clr d0
 cmp 0,a0
 beq st_getb_out
 mov (8,sp),d0
 add d0,a0
 movbu (a0),d0
st_getb_out:
 mov (4,sp),a0
 ret [],12
/* Half-press trigger (HLS_EVENT task, 0x602f0b95): the displaced stock call
 * runs first on the same frame; d0 and PSW are dead at the resume point
 * (0x602f0b9a reloads d0 and tests it). */
arm_hook:
 call trig,[d2,d3,a2,a3],36
 mov (16,sp),d0
 cmp 0x02000100,d0
 bne arm_back
 mov (loaded_bits),d0
 and 1023,d0
 cmp 1023,d0
 bne arm_back
 call st_ptr,[],8
 cmp 0,a0
 bne arm_ext
 call arm_gate,[d2,d3,a2,a3],36
 call st_ptr,[],8
 cmp 0,a0
 beq arm_back
 call arm_refresh,[d2,d3],16     /* section 10: armed implies all ten sections initialised */
/* Extension vector: a further layer (Caduceus) may put one entry here. It is
 * called only once armed, hence with every section initialised, on each
 * half-press, in the HLS_EVENT task. It is entered by calls and may use
 * d0, d1, a0, a1. Zero in this patch: nothing is called. */
arm_ext:
 mov (ext_halfpress),a0
 cmp 0,a0
 beq arm_back
 call arm_ext_call,[d2,d3,a2,a3],36
arm_back:
 jmp trig_resume
arm_ext_call:
 calls (a0)
 ret [d2,d3,a2,a3],36

/* Keep stock saturation input. Load current active profile's cells after
 * the builder. Per-image ownership remains unqualified. */
builder_hook:
 call color_builder,[d2,d3,a2,a3],96
 add -28,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 call st_ptr,[],8
 cmp 0,a0
 bne builder_armed
 mov (12,sp),a0
 bra builder_stock
builder_armed:
 mov (12,sp),a0
 mov a1,(16,sp)
 mov a2,(20,sp)
 mov a3,(24,sp)
 call apply_values,[d2,d3,a2,a3],24
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 mov (20,sp),a2
 mov (24,sp),a3
builder_stock:
 add 28,sp
 jmp builder_resume

.section .ext8,"ax"
/* d0 packed cell -> validated H/L byte, or neutral. Each nibble is -7..7, the
 * span of hue_lut/light_lut; the on-camera editor writes -5..5 only. */
decode:
 mov d0,d1
 lsr 16,d1
 cmp 0x4831,d1
 bne decode_zero
 mov d0,d1
 lsr 8,d1
 xor d0,d1
 and 255,d1
 cmp 255,d1
 bne decode_zero
 mov d0,d1
 asl 28,d1
 asr 28,d1
 cmp -7,d1
 blt decode_zero
 cmp 7,d1
 bgt decode_zero
 mov d0,d1
 asl 24,d1
 asr 28,d1
 cmp -7,d1
 blt decode_zero
 cmp 7,d1
 bgt decode_zero
 and 255,d0
 ret [],4
decode_zero:
 clr d0
 ret [],4

.balign 2
hue_lut:
 .hword 7000,6000,5000,4000,3000,2000,1000,0,-1000,-2000,-3000,-4000,-5000,-6000,-7000
light_lut:
 .hword -300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300

/* E148's picture-mode refresh (0x602e00bf, jump table 0x60499718) has no case
 * for 111 = 54..56: Color Profile 1..3 fall to its default, so the profile's
 * own Sharpness, Contrast, per-sector saturation, Shading and tone curve never
 * reach the effective settings the image pipeline reads. E147 handles them in
 * its refresh 0x604032a4 (cases 54..56) and its caller 0x604040ff. This
 * replays that at the end of E148's refresh (0x602e0826), in the same frame:
 *   struct +0 contrast  = 908+p  (caller writes ID 8)
 *   struct +4 sharpness = 904+p  (ID 7)
 *   struct +8 = 0 (ID 59), +20 = 1 (ID 105), +24 = 0 (ID 1806)
 *   effective 916..927 = 928+12p .. 939+12p  (store 1 -> store 2)
 *   effective 1016 = shading 912+p, 1011 = 0, 998 = 0 (Color Profile grain removed 2026-11-19)
 *   effective 383 / 691 / 382 = 976+3p / 977+3p / 978+3p (store 2):
 *   Highlights / Midtones / Shadows (checked against the tone page, alpha5)
 * Other picture modes get E147's zeros for the extra IDs, written only after a
 * Color Profile may have set them (flag starts set: effective settings survive
 * power-off). The section-5 body runs only after arming. */
.section .refresh_hook,"ax"
 jmp refresh_guard
 nop
/* Jump-table cases 54..56 (stock: the default 0x602e06ca). Note the profile
 * for the tail, then take the stock default path unchanged. */
.section .refresh_cases,"a"
 .long refresh_case,refresh_case,refresh_case,refresh_case,refresh_case,refresh_case
.section .ext2,"ax"
/* The profile travels to rt_tail in d2 (callee-saved; this path of the stock
 * function neither reads nor writes it again, and its ret restores the
 * caller's value). No store. */
REFRESH_TAG = 0x52460000
refresh_case:
 lsr 2,d2
 sub 54,d2
 or REFRESH_TAG,d2
 jmp refresh_default
refresh_guard:
 call st_ptr,[],8
 cmp 0,a0
 beq refresh_stock
 jmp rt_tail
refresh_stock:
 mov (12,sp),a0
 clr d0
 mov d3,(76,a0)
 ret [d2,d3,a2,a3],96
.section .creset_hook,"ax"
 jmp creset
.section .pm_s1,"ax"
 call pm_set_a3,[d2,d3],12
.section .pm_s2,"ax"
 call pm_set_a2,[d2,d3],12
.section .pm_s4,"ax"
 call pm_put,[d2,d3],12
.section .pm_s5,"ax"
 call pm_put,[d2,d3],12
.section .ext8,"ax"

/* Builder output: H/L of the profile recorded in this image job. */
apply_values:
 /* Profile 1..3 from the properties the capture snapshot itself reads
  * (0x602c8821/0x602c8855): picture-mode property 0x948 is 11 for Color
  * Profile 1-3 and property 0xf6b is then the profile number (stored at
  * snapshot +28735 / +28765). Job record +10 is the dispatcher's block
  * key (always 11 here), not a profile. These are read when the block is
  * built, like the H/L cells, so a profile change between the snapshot
  * and the build is not covered. The section-2 wrapper checks arming. */
 mov 38017,d0
 clr d1
 mov 0,a0
 call prop_byte,[d2,d3,a2],32
 cmp 11,d0
 bne apply_done
 mov 63153,d0
 clr d1
 mov 0,a0
 call prop_byte,[d2,d3,a2],32
 sub 1,d0
 cmp 3,d0
 bcc apply_done
 mov (12,a2),a2
 add 706,a2
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 2,d0
 add 928,d0
 mov d0,d2
 mov 12,d3
apply_loop:
 /* Builder record r = 12 - d3 holds sector 2*(r%6) + r/6 (E148 builder
  * 0x603e7ca6: outer 0/1, inner 0..5, sector byte 2*inner + outer). */
 mov 12,d0
 sub d3,d0
 mov sector_of_record,a0
 movbu (d0,a0),d0
 add d2,d0
 mov 1,d1
 call active_read,[d2],8
 call decode,[],4
 mov d0,a3
 asl 28,d0
 asr 28,d0
 add 7,d0
 add d0,d0
 mov hue_lut,a0
 movhu (d0,a0),d0
 movhu d0,(a2)
 mov a3,d0
 asl 24,d0
 asr 28,d0
 add 7,d0
 add d0,d0
 mov light_lut,a0
 movhu (d0,a0),d0
 movhu d0,(4,a2)
 add 24,a2
 add -1,d3
 bne apply_loop
apply_done:
 ret [d2,d3,a2,a3],24
sector_of_record:
 .byte 0,2,4,6,8,10,1,3,5,7,9,11

/* Custom-mode reset 0x602db531 (d0 = mode, d1 = kind; menus 0x6091c242 and
 * 0x6091c3a2) clears both parts of the live cells and reloads them only when
 * the reset mode is the current one (setting 41). Part 1 of 904..975 holds the
 * live H/L and per-profile WB, so resetting another mode would wipe them.
 * When the reset mode is not current, keep that part as it was. */
.section .ext2,"ax"
creset:
 mov d0,d2
 mov d1,d3
 /* Stock path until startup has completed. */
 movbu (loaded_bits),d0
 btst 0x20,d0
 beq creset_stock
 call st_ptr,[],8
 cmp 0,a0
 beq creset_stock
 jmp creset_armed
creset_stock:
 mov d2,d0
 mov d3,d1
creset_orig:
 mov d0,d2
 mov d1,d3
 extbu d3
 cmp 1,d3
 jmp creset_resume

/* Reset-in-progress flag. call ...,[d2,a2],12. Preserves d0,d1,a0,a1. */
st_reset_on:
 mov 1,d2
 bra st_reset_put
st_reset_off:
 clr d2
st_reset_put:
 mov a0,a2
 call st_ptr,[],8
 cmp 0,a0
 beq st_reset_out
 movbu d2,(ST_RESET,a0)
st_reset_out:
 mov a2,a0
 ret [d2,a2],12
/* Remember the colour editor object in a0. call ...,[a2],8. Preserves all.
 * (Section 5 loads before the GUI's section 7.) */
.section .ext5,"ax"
st_set_editor:
 mov a0,a2
 call st_ptr,[],8
 cmp 0,a0
 beq st_set_editor_out
 mov a2,(ST_EDITOR,a0)
st_set_editor_out:
 mov a2,a0
 ret [a2],8
/* ui_read / ui_write: tone_alias (section 9) only once armed, when every
 * section is loaded. call ui_alias,[d2,d3],12: d0 = id -> d0 */
ui_alias:
 call st_ptr,[],8
 cmp 0,a0
 beq ua_out
 jmp tone_alias
ua_out:
 ret [d2,d3],12

.section .ext8,"ax"
creset_armed:
 mov 41,d0
 call raw_get,[],4
 extbu d0
 extbu d2
 cmp d0,d2
 bne creset_save_cells
 jmp creset_stock
creset_save_cells:
 /* 72 cells (904..975) are held on this task's stack across the stock
  * reset: (8..295,sp). a2/a3 are the caller's and are put back. */
 add -304,sp
 mov a2,(296,sp)
 mov a3,(300,sp)
 mov d3,a3
 mov 904,d3
 mov sp,a2
 add 8,a2
creset_save:
 mov d3,d0
 mov 1,d1
 call active_read,[d2],8
 mov d0,(a2)
 inc4 a2
 inc d3
 cmp 976,d3
 bne creset_save
 mov d2,d0
 mov a3,d1
 call creset_orig,[d2,d3],12
 mov d0,a3
 mov 904,d3
 mov sp,a2
 add 8,a2
creset_restore:
 mov (a2),a0
 mov d3,d0
 mov 1,d1
 call active_write,[d2],8
 inc4 a2
 inc d3
 cmp 976,d3
 bne creset_restore
 mov a3,d0
 mov (296,sp),a2
 mov (300,sp),a3
 add 304,sp
 ret [d2,d3],12
/* Mode store: E148's mode-recall lists (0x604daf4c) carry 111 but not 903,
 * the Color Profile number that turns 111's stored family 11 into 54..56
 * (E147's lists carry 903 in the same row as 111), nor 989, the Monochrome
 * Profile number that turns family 12 into 57..59. Without them a custom-mode
 * recall restores the family with whatever 903/989 hold. At the four per-entry
 * copies of the list routines, copy 903 and 989 with 111 in the same row, as
 * E147 does (0 = not a profile; the DB reset writes its default to both rows).
 * rows -> working copy (0x602e0f40 entry in a3, 0x602e1071 entry in a2);
 * a row value above 3 is not copied. */
.section .ext2,"ax"
pm_set_a3:
 mov a3,d3
 bra pm_set
pm_set_a2:
 mov a2,d3
pm_set:
 mov d0,d2
 call wc_set,[],4
 cmp 111,d2
 bne pm_set_done
 call st_ptr,[],8                /* not armed: the stock copy only */
 cmp 0,a0
 beq pm_set_done
 jmp pm_set_armed
pm_set_done:
 ret [d2,d3],12
/* working copy -> rows (0x602e0fa5, 0x602e1153): d0 id, d1 row, a0 value */
pm_put:
 mov d0,d2
 mov d1,d3
 call active_write,[d2],8
 cmp 111,d2
 bne pm_put_done
 call st_ptr,[],8                /* not armed: the stock copy only */
 cmp 0,a0
 beq pm_put_done
 jmp pm_put_armed
pm_put_done:
 ret [d2,d3],12

.section .ext8,"ax"
pm_set_armed:
 mov 903,d2
pm_set_loop:
 mov d3,a0
 movbu (2,a0),d1
 mov d2,d0
 call active_read,[d2],8
 cmp 4,d0
 bcc pm_set_next
 call pm_num,[d2,d3],12
 mov d0,d1
 mov d2,d0
 call wc_set,[],4
pm_set_next:
 cmp 989,d2
 bne pm_set_mono
 ret [d2,d3],12
pm_set_mono:
 mov 989,d2
 bra pm_set_loop
pm_put_armed:
 mov 903,d2
pm_put_loop:
 mov d2,d0
 call wc_get,[],4
 call pm_num,[d2,d3],12
 mov d0,a0
 mov d2,d0
 mov d3,d1
 call active_write,[d2],8
 cmp 989,d2
 bne pm_put_mono
 ret [d2,d3],12
pm_put_mono:
 mov 989,d2
 bra pm_put_loop
/* d0 = profile number for d2 (903: Color Profile, 989: Monochrome Profile);
 * returns 0 unless the working copy's stored 111 family is that profile's
 * (11 = COLOR, 12 = MONO), and clears a stale working-copy number. E148's
 * settings reset (0x602e0ef3) resets 111 but not 903/989, so after Reset
 * (basic or full) from a profile the stored family was Natural's while 903 or
 * 989 kept the old number, and 111 read as an unknown mode (ART16). The
 * list copies run after the reset, so this keeps 111/903/989 consistent there
 * and in every custom-mode copy. */
pm_num:
 mov d0,d3
 mov 111,d0
 call wc_get,[],4
 cmp 903,d2
 bne pm_num_mono
 cmp 11,d0
 beq pm_num_keep
 bra pm_num_clear
pm_num_mono:
 cmp 12,d0
 beq pm_num_keep
pm_num_clear:
 cmp 0,d3
 beq pm_num_keep
 mov d2,d0
 clr d1
 call wc_set,[],4
 clr d3
pm_num_keep:
 mov d3,d0
 ret [d2,d3],12

/* Picture-mode refresh tail for Color Profile 1-3 and Monochrome Profile 1-3
 * (section 5 free tail, entered from refresh_guard only when armed).
 * d3 (from the tag refresh_case leaves in d2) is the case: 0..2 = CP1..3 (111 = 54..56),
 * 3..5 = MONO1..3 (111 = 57..59), 0xff = any other mode.
 *
 * E148's stock refresh never writes 916..927, 1011, 1016, 998 or the tone IDs
 * 383/691/382 (the last three are the user's own Highlight/Mid/Shadow), so a
 * profile's values must be undone on leaving it, and E147's "zero them in
 * stock modes" rule does not fit E148. On entering a profile from a stock
 * mode the user's three tone values are saved in a persistent record, part 1
 * of IDs 964..967 (context 0) or 968..971 (context 1): unused fourth-profile
 * H/L cells that are saved at power-off and travel with custom modes like the
 * rest of part 1. Word 0 is TONE_SAVED while a save is held. On leaving, the
 * tone is restored from it and the other IDs get their stock values (916..927
 * = 0, 1011 = 2, 1016 = 0, 998 = 0; no stock mode changes them).
 *
 * Profile values (E147 refresh 0x604032a4, caller 0x604040ff; E148 caller
 * 0x602e082f writes struct +0 -> 8, +4 -> 7, +8 -> 59, +12 -> 130,
 * +16 -> 131, +20 -> 105, +24 -> 1806):
 *   CP p:   +0 contrast 908+p, +4 sharpness 904+p, +8 0, +20 1, +24 0,
 *           916..927 = 928+12p.., 1016 = 912+p, 1011 = 0, 998 = 0,
 *           tone 976+3p.. (store 2) -> 383/691/382
 *   MONO p: +0 994+p, +4 990+p, +8 0, +12 filter 1007+p, +16 toning 1003+p,
 *           +20 1, +24 0, 916..927 = 0, 1011 = level 1012+p,
 *           1016 = shading 1017+p, 998 = grain 999+p, tone 1021+3p.. */
TONE_SAVED = 0x544f4e45
.section .ext5,"ax"
rt_tail:
 mov (12,sp),a0
 clr d0
 mov d3,(76,a0)
 mov 0xff,d3
 mov d2,d0
 lsr 8,d0
 cmp REFRESH_TAG >> 8,d0
 bne rt_untagged
 mov d2,d3
 and 0xff,d3
rt_untagged:
 /* d2 = tone record ID for this context, 0 = none */
 clr d2
 mov a2,d0
 cmp 2,d0
 bcc rt_have
 asl 2,d0
 add 964,d0
 mov d0,d2
rt_have:
 call bw_refresh,[d2,d3,a2,a3],20
 cmp 6,d3
 bcs rt_profile
 /* stock mode: undo a profile only if a save is held */
 cmp 0,d2
 beq rt_ret
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 cmp TONE_SAVED,d0
 bne rt_ret
 clr d0
 mov d0,a0
 mov d2,d0
 mov 1,d1
 call active_write,[d2],8
 mov rs_tone_ids,a3
rt_restore_loop:
 inc d2
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 mov d0,a1
 movhu (a3),d0
 mov d0,a0
 call rt_put2,[],4
 add 2,a3
 movhu (a3),d0
 cmp 0,d0
 bne rt_restore_loop
 mov rs_stock,a3
rt_stock_loop:
 movhu (2,a3),d0
 mov d0,a1
 movhu (a3),d0
 mov d0,a0
 call rt_put2,[],4
 add 4,a3
 movhu (a3),d0
 cmp 0,d0
 bne rt_stock_loop
rt_ret:
 ret [d2,d3,a2,a3],96

rt_profile:
 cmp 0,d2
 beq rt_write
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 cmp TONE_SAVED,d0
 beq rt_write
 /* Context 1 is filled from context 0 when the mode dial moves, so on its
  * first profile refresh it already holds the profile's tone. If context 0
  * holds a saved user tone, context 1 takes that record instead of saving
  * its own (profile) values. */
 cmp 968,d2
 bne rt_save_cur
 mov 964,d0
 mov 1,d1
 call active_read,[d2],8
 cmp TONE_SAVED,d0
 bne rt_save_cur
 mov 965,d2
rt_copy_loop:
 mov d2,d0
 mov 1,d1
 call active_read,[d2],8
 mov d0,a0
 mov d2,d0
 add 4,d0
 mov 1,d1
 call active_write,[d2],8
 inc d2
 cmp 968,d2
 bne rt_copy_loop
 mov TONE_SAVED,a0
 mov 968,d0
 mov 1,d1
 call active_write,[d2],8
 bra rt_write
rt_save_cur:
 mov rs_tone_ids,a3
rt_save_loop:
 movhu (a3),d0
 mov d0,a0
 call rt_get2,[],4
 mov d0,a0
 inc d2
 mov d2,d0
 mov 1,d1
 call active_write,[d2],8
 add 2,a3
 movhu (a3),d0
 cmp 0,d0
 bne rt_save_loop
 add -3,d2
 mov TONE_SAVED,a0
 mov d2,d0
 mov 1,d1
 call active_write,[d2],8
rt_write:
 /* d3 = kind 0..5 */
 mov rs_cp_table,a3
 cmp 3,d3
 bcs rt_tab_loop
 mov rs_mono_table,a3
rt_tab_loop:
 movhu (2,a3),d0
 cmp 2,d0
 bcs rt_tab_value
 call rt_p,[],4
 add d1,d0
 mov d0,a0
 call rt_get1,[],4
rt_tab_value:
 movhu (a3),d1
 btst 0x8000,d1
 beq rt_tab_id
 and 0xff,d1
 mov (12,sp),a0
 add d1,a0
 mov d0,(a0)
 bra rt_tab_next
rt_tab_id:
 mov d0,a1
 mov d1,a0
 call rt_put2,[],4
rt_tab_next:
 add 4,a3
 movhu (a3),d0
 cmp 0,d0
 bne rt_tab_loop
 /* 916..927: CP sectors (store 1, sector order), MONO zeros */
 movhu (2,a3),d0
 cmp 0,d0
 beq rt_sec_base
 call rt_p,[],4
 asl 2,d1
 add d1,d0
 add d1,d0
 add d1,d0
rt_sec_base:
 mov d0,a3
 mov 916,d2
rt_sec_loop:
 clr d0
 mov a3,d1
 cmp 0,d1
 beq rt_sec_put
 mov d2,d0
 add -916,d0
 add d1,d0
 mov d0,a0
 call rt_get1,[],4
rt_sec_put:
 mov d0,a1
 mov d2,a0
 call rt_put2,[],4
 inc d2
 cmp 928,d2
 bne rt_sec_loop
 /* tone curve: three values per profile, store 2, as E147 */
 call rt_p,[],4
 mov d1,d2
 add d1,d2
 add d1,d2
 add 976,d2
 cmp 3,d3
 bcs rt_tone
 add 45,d2
rt_tone:
 mov rs_tone_ids,a3
rt_tone_loop:
 mov d2,a0
 call rt_get2,[],4
 mov d0,a1
 movhu (a3),d0
 mov d0,a0
 call rt_put2,[],4
 inc d2
 add 2,a3
 movhu (a3),d0
 cmp 0,d0
 bne rt_tone_loop
 bra rt_ret

/* d3 = kind -> d1 = profile p (0..2); d0 kept */
rt_p:
 mov d3,d1
 cmp 3,d1
 bcs rt_p_done
 add -3,d1
rt_p_done:
 ret [],4
/* a0 = ID -> d0 = store-1 / store-2 value of context a2 */
rt_get1:
 mov a2,d0
 mov 1,d1
 call refresh_get,[d2],8
 ret [],4
rt_get2:
 mov a2,d0
 mov 2,d1
 call refresh_get,[d2],8
 ret [],4
/* a0 = ID, a1 = value -> effective (store 2) of context a2 */
rt_put2:
 mov a2,d0
 mov 2,d1
 call refresh_set,[d2,a2],12
 ret [],4
.align 2
/* {dst, src}: dst 0x80nn = refresh struct +nn, else an ID; src 0/1 = that
 * value, else src + p (store 1). Then 0,
 * then the 916..927 source (0 = zeros).
 * Color Profile grain (v0.2.0) is stored in the value (part 0) cells of
 * Color Profile 4's Sharpness, Contrast and Shading, 907 / 911 / 915: E148
 * has no Color Profile 4 (111 = 64), the IDs have no stock descriptor, and
 * part 1 of the same IDs (the WB records) is a separate cell. */
rs_cp_table:
 .hword 0x8000,908, 0x8004,904, 0x8008,0, 0x8014,1, 0x8018,0
 .hword 1016,912, 1011,0, 998,0, 0, 928
rs_mono_table:
 .hword 0x8000,994, 0x8004,990, 0x8008,0, 0x800c,1007, 0x8010,1003
 .hword 0x8014,1, 0x8018,0, 1011,1012, 1016,1017, 998,999, 0, 0
rs_tone_ids:
 .hword 383,691,382,0
/* {ID, stock value} written when leaving a profile; then 0 */
rs_stock:
 .hword 916,0, 917,0, 918,0, 919,0, 920,0, 921,0, 922,0, 923,0
 .hword 924,0, 925,0, 926,0, 927,0, 1011,2, 1016,0, 998,0, 0

.section .ext8,"ax"
/* Arm once: every section initialised, caller is the HLS_EVENT task. */
arm_gate:
 mov sp,a0
 add 12,a0
 call get_tid,[a2],4
 cmp 0,d0
 bne arm_out
 movhu (hls_tid),d1
 cmp 0,d1
 beq arm_out
 btst 0x8000,d1
 bne arm_out
 movhu (12,sp),d0
 cmp d1,d0
 bne arm_out
 mov ST_SIZE,d0
 call malloc,[],4
 cmp 0,a0
 beq arm_out
 mov a0,d2
 sub ST_POOL-1,d2
 cmp 0,d2
 beq arm_out
 cmp ST_HANDLE_MAX,d2
 bhi arm_out
 mov d2,d0
 and 3,d0
 cmp 1,d0
 bne arm_out
 mov a0,a2
 add ST_SIZE,a2
 clr d0
arm_clear:
 mov d0,(a0)
 inc4 a0
 cmp a2,a0
 bne arm_clear
 mov ST_MAGIC_VALUE,d0
 mov d0,(ST_MAGIC-ST_SIZE,a2)
 /* Publish through the cache of this CPU and straight to RAM, so every
  * reader (st_ptr) sees it at once and a later write-back agrees. */
 movhu d2,(st_handle)
 movhu d2,(st_handle_u)
arm_out:
 ret [d2,d3,a2,a3],36
.section .ext10,"ax"
/* Once, at the half-press that arms the patch. The start-up refresh ran the
 * stock tail only (rt_tail), so run the refresh now for a context that is on a
 * profile (apply it) or still holds a tone save (undo it: the mode was changed
 * before arming). Any other context is left alone. The refresh takes the
 * context in d0 and its picture mode in d1. call arm_refresh,[d2,d3],16;
 * (4,sp) = a number was cleared. */
arm_refresh:
 /* A profile number without its family: OM's own firmware (or its Reset)
  * changes 111 and leaves 903 / 989, and 111 then reads as an unknown mode
  * (63). Clear a number whose family is not selected, then refresh. */
 clr d0
 mov d0,(4,sp)
 mov 111,d0
 call raw_get,[],4
 extbu d0
 mov d0,d3                       /* stored family: 11 Color Profile, 12 Monochrome Profile */
 mov 903,d2
 cmp 11,d3
 beq arm_fix_next
arm_fix:
 mov d2,d0
 call stock_get,[],4
 cmp 0,d0
 beq arm_fix_next
 mov d2,d0
 clr d1
 mov 1,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 mov 1,d0
 mov d0,(4,sp)
arm_fix_next:
 cmp 989,d2
 beq arm_fix_done
 mov 989,d2
 cmp 12,d3
 bne arm_fix
arm_fix_done:
 clr d2
arm_refresh_ctx:
 mov 111,d0                      /* context 0: the live setting; context 1: its store 2 (as wb.s) */
 cmp 0,d2
 bne arm_refresh_one
 call stock_get,[],4
 bra arm_refresh_mode
arm_refresh_one:
 mov d0,a0
 mov d2,d0
 mov 2,d1
 call refresh_get,[d2],8
arm_refresh_mode:
 mov d0,d3
 sub 54,d0
 cmp 6,d0
 bcs arm_refresh_run
 cmp 0,d2
 bne arm_refresh_save
 mov (4,sp),d0                   /* context 0 after a cleared number: its mode changed */
 cmp 0,d0
 bne arm_refresh_run
arm_refresh_save:
 mov d2,d0
 asl 2,d0
 add 964,d0
 mov 1,d1
 call active_read,[d2],8
 cmp 0x544f4e45,d0               /* TONE_SAVED */
 bne arm_refresh_next
arm_refresh_run:
 mov d2,d0
 mov d3,d1
 call pm_refresh,[d2],88
arm_refresh_next:
 inc d2
 cmp 2,d2
 bne arm_refresh_ctx
 ret [d2,d3],16
.section .extvec,"a"
.global ext_halfpress
ext_halfpress:
 .long fl_entry

.section .ext10,"ax"
/* ---- inactivity: custom controls are user activity (section 10, armed) ----
 * The direct-setting screen closes when its timer 500 runs out. Its container
 * restarts it (8000 ms) when a child consumes a command and the container's
 * +92 is 1 (stock 0x60e3ca89..0x60e3ca9b and 0x60e3c7ce..0x60e3c7de). The
 * axis switch, a film step and INFO on the custom pages are consumed outside
 * those paths; restart it the same way. Nothing else changes the timer.
 * a0 = container. call ui_activity,[d2,d3],12 */
.global ui_activity
ui_activity:
 cmp 0,a0
 beq ui_act_out
 mov (92,a0),d0
 cmp 1,d0
 bne ui_act_out
 mov 500,d0
 mov 30000,d1                    /* Picture Mode's idle time (pm_timeout.py), 8000 in stock */
 call ui_timer,[d2,d3],12
ui_act_out:
 ret [d2,d3],12

/* After fl_delete stepped a film: the screen's container is (scr_obj)+0.
 * call ui_film_activity,[d2,d3,a2,a3],24 */
ui_film_activity:
 mov (scr_obj),a0
 cmp 0,a0
 beq ui_film_out
 mov (a0),a0
 call ui_activity,[d2,d3],12
ui_film_out:
 ret [d2,d3,a2,a3],24

/* INFO consumed by container a0: only the direct-setting screen's own
 * container, with a Color or Monochrome Profile selected (the modes whose
 * pages pages_hook shows). call ui_info_activity,[d2,d3,a2,a3],24 */
ui_info_activity:
 mov a0,a2
 mov (scr_obj),a0
 cmp 0,a0
 beq ui_info_out
 mov (a0),a0
 cmp a2,a0
 bne ui_info_out
 mov 111,d0
 call stock_get,[],4
 sub 54,d0
 cmp 6,d0
 bcc ui_info_out
 mov a2,a0
 call ui_activity,[d2,d3],12
ui_info_out:
 ret [d2,d3,a2,a3],24

/* ---- Live ND32 / ND64 in CP Button Settings (section 10, armed) ----
 * The page (menu list 0x16f, data edit cp_button_items) lists the enable
 * settings 2217 / 2218 beside ND2..ND16. E148 keeps their cells (they read 1)
 * but has no descriptor for them, so OM's writer (0x602d0f23 -> 0x602e1a33)
 * finds none and drops a change. The descriptors are stock-format copies of
 * 2216's (data edit cp_nd_descriptors, 0/1 list 0x6050da8c). OM hashes its
 * 1589 static descriptors into 128 RAM buckets at boot (0x602e1e84); a chain
 * node is { descriptor, next }. Link ours once per power-on, after arming,
 * with nodes in P (P+988..1027, past the film bank). Only RAM changes; a
 * lookup before this finds nothing, as stock. a2 = P. Color Profile Shading
 * 912..914 has no descriptor either; it gets copies of 1017's (same list).
 * Color Profile grain 907 / 911 / 915 (v0.2.0) gets copies of 999's.
 * call cp_nd_link,[d2,d3,a2,a3],24 */
CP_NODES = 988                  /* 20 of 23 nodes: P+988..1171 (5 cp_nd_desc, 15 cad_desc) */
CP_NDESC = 5                    /* 2217, 2218, 912..914 (cp_nd.py; 907, 911, 915 with CP_GRAIN) */
.global cp_nd_link
cp_nd_link:
 mov cp_nd_desc,a3
 clr d3
cp_nd_one:
 movhu (a3),d0
 call desc_find,[],0             /* d0 id -> a0 descriptor, 0 when none */
 cmp 0,a0
 bne cp_nd_next                  /* already linked (or OM has one) */
 mov a2,a1
 add CP_NODES,a1
 mov d3,d0
 asl 3,d0
 add d0,a1                       /* a1 = node */
 mov a3,(a1)
 clr d0
 mov d0,(4,a1)
 movhu (a3),d0
 and 127,d0
 asl2 d0
 mov desc_buckets,a0
 add d0,a0                       /* a0 = the bucket's head word */
cp_nd_walk:
 mov (a0),d0
 cmp 0,d0
 beq cp_nd_put
 mov d0,a0
 add 4,a0                        /* the node's next word */
 bra cp_nd_walk
cp_nd_put:
 mov a1,(a0)
cp_nd_next:
 add 20,a3
 inc d3
 cmp CP_NDESC,d3
 bne cp_nd_more
 call cad_build,[d2,d3],12       /* then Black / White and the tints (built in P) */
cp_nd_more:
 cmp CP_NDESC+CAD_NDESC,d3
 bcs cp_nd_one
 ret [d2,d3,a2,a3],24



.section .ext5,"ax"
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

/* d0 = x, d1 = y, d2 = width, d3 = height: one filled block: a level line
 * with a pen as tall as the block, or a plumb line with a pen as wide. call gfx_bar,[d2,d3,a2,a3],28 */
gfx_bar:
 mov d0,(4,sp)
 mov d1,(8,sp)
 cmp d3,d2
 bcs gb_tall
 mov 1,d0
 mov d3,d1
 mov a2,a0
 call pen_size,[d2,d3],8
 mov d3,d1
 lsr 1,d1
 mov (8,sp),d0
 add d0,d1
 mov d1,(8,sp)                   /* the pen is centred on the line */
 mov (4,sp),d0
 mov a2,a0
 call move_to,[],4
 mov (4,sp),d0
 add d2,d0
 add -1,d0
 mov (8,sp),d1
 bra gb_line
gb_tall:                         /* taller than wide: a plumb line, pen as wide */
 mov d2,d0
 mov 1,d1
 mov a2,a0
 call pen_size,[d2,d3],8
 mov d2,d0
 lsr 1,d0
 mov (4,sp),d1
 add d1,d0
 mov d0,(4,sp)
 mov (8,sp),d1
 mov a2,a0
 call move_to,[],4
 mov (4,sp),d0
 mov (8,sp),d1
 add d3,d1
 add -1,d1
gb_line:
 mov a2,a0
 call line_to,[d2,d3,a2,a3],32
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
/* palette indices: Yellow, Orange, Orange-red, Red, Magenta, Violet, Blue,
 * Blue-cyan, Cyan, Green-cyan, Green, Yellow-green */
gtab_col:
 .byte 123,92,16,122,89,88,87,105,107,86,22,116

.section .ext6,"ax"
/* The tone page's view paint (vtable 0x610d6560, entry 0x610d6600, stock
 * 0x60d47232): the stock painter, then the curve (section 10, armed only).
 * Same event checks as paint_axis; in section 6 because a view may be asked
 * to paint before arming. Entered through the vtable: a0 = view, a1 = paint event. */
paint_tone:
 movm [d2,d3,a2,a3],(sp)
 add -12,sp
 mov a1,(8,sp)
 call stock_paint,[a2,a3],16
 mov (8,sp),a1
 mov d0,(8,sp)
 cmp 0,a1
 beq pt_out
 movhu (4,a1),d0
 cmp 2,d0
 bne pt_out
 mov (8,a1),a2
 cmp 0,a2
 beq pt_out
 call st_ptr,[],8
 cmp 0,a0
 beq pt_out
 mov a2,a0
 call gfx_tone,[d2,d3,a2,a3],72
pt_out:
 mov (8,sp),d0
 add 12,sp
 ret [d2,d3,a2,a3],16

/* Monochrome Color Filter view 0x610d9b20. Preserve the stock painter and
 * draw only the filter swatches for an armed paint event. */
paint_filter:
 movm [d2,d3,a2,a3],(sp)
 add -12,sp
 mov a1,(8,sp)
 call stock_paint,[a2,a3],16
 mov (8,sp),a1
 mov d0,(8,sp)
 cmp 0,a1
 beq pf_out
 movhu (4,a1),d0
 cmp 2,d0
 bne pf_out
 mov (8,a1),a2
 cmp 0,a2
 beq pf_out
 call st_ptr,[],8
 cmp 0,a0
 beq pf_out
 mov a2,a0
 call gfx_filter,[d2,d3,a2,a3],44
pf_out:
 mov (8,sp),d0
 add 12,sp
 ret [d2,d3,a2,a3],16

.section .ext10,"ax"
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

.section .ext7,"ax"
/* CP button "any item ticked" (0x60d2230f, called by 0x60d222d3 when the
 * current item 2228 holds no item) asks 0x60d223d5(k) (is CP item k of
 * table 0x60f7f57c ticked) for k 0..5 and 13..16, each group followed by its
 * function check 0x60d044be (k 2..5: 109, Live ND). It skips k 6 and 7, Live
 * ND32 / ND64 (2217 / 2218, also mask 109), which cp_nd.py puts on the CP
 * Button page, so with only those ticked the button found nothing. This
 * replaces the k 5 test (mov 5,d0; call 0x60d223d5 at 0x60d22357, 7 bytes):
 * k 5, then, once armed (their descriptors are linked by cp_nd_link), k 6
 * and 7. d0 = 1 when one is ticked; the stock code then runs the same 109
 * check. Unarmed: k 5 only, as stock. call cp_any_nd,[],4 */
cp_any_nd:
 mov 5,d0
 call cp_ticked,[],4
 cmp 1,d0
 beq cp_any_out
 call st_ptr,[],8
 cmp 0,a0
 beq cp_any_none
 mov 6,d0
 call cp_ticked,[],4
 cmp 1,d0
 beq cp_any_out
 mov 7,d0
 call cp_ticked,[],4
cp_any_out:
 ret [],4
cp_any_none:
 clr d0
 ret [],4

.section .ext5,"ax"
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


.section .ext10,"ax"
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

.section .ext2,"ax"
/* INFO (0x9014) toggles the custom pages' native controls (all / individual,
 * the tone curve's point). Stock runs it but restarts the screen's timeout
 * only for other commands. Run stock, then count a consumed INFO as activity
 * on the custom pages (section 10, armed only). Same frame use as
 * hsl_delete_action: (0,sp) stays free for the nested calls. On a tint axis
 * of the colour wheel with one colour selected, INFO is consumed and does
 * nothing: a tint has one colour, and "all" wrote every colour in turn
 * (camera report 2026-11-19). From "all", INFO still leaves it. */
container_info2:
 add -12,sp
 mov a0,(4,sp)
 mov d0,(8,sp)
 call info_tint,[a2],8
 cmp 0,d0
 bne info_kept
 mov (8,sp),d0
 mov (4,sp),a0
 calls stock_container
 mov d0,(8,sp)
 cmp 1,d0
 bne info_done
 call st_ptr,[],8
 cmp 0,a0
 beq info_done
 mov (4,sp),a0
 call ui_info_activity,[d2,d3,a2,a3],24
 bra info_done
info_kept:
 mov d0,(8,sp)
info_done:
 mov (8,sp),d0
 add 12,sp
 rets

/* a0 = the container -> d0 = 1 when INFO must not switch to "all": armed,
 * colour wheel parent (13 children), tint axis (3..5), one colour selected.
 * Preserves d1, a1-a3. call info_tint,[a2],8 */
info_tint:
 mov (76,a0),a2
 call st_ptr,[],8
 cmp 0,a0
 beq it_no
 movbu (ST_AXIS,a0),d0
 cmp 3,d0
 bcs it_no
 cmp 0,a2
 beq it_no
 movhu (120,a2),d0
 cmp 13,d0
 bne it_no
 movhu (122,a2),d0
 cmp 0,d0
 beq it_out
 mov 1,d0
 bra it_out
it_no:
 clr d0
it_out:
 ret [a2],8

/* ---- Blacks / Whites (v0.2.0-dev): image-pipeline side ----
 * Blacks / Whites are added to the split-tone delta tables (tn_tables, ext3), so
 * they reach photos and live view through the R/G/B curve setter (wb.s st_tint),
 * the route the camera showed working for split tone (2026-11-19). The first
 * version bent E148's brightness curve (modifier 0x60385f08, hooks at
 * 0x60385f9c and 0x603e86a8): the UI worked but the camera showed no effect in
 * live view or photos, so those hooks are gone.
 * research/OM5II-BLACKS-WHITES-2026-11-18.md, OM5II-V020DEV-CAMERA-2026-11-19.md */

/* ---- Black / White and split tone (v0.2.0-dev): settings, refresh, UI ----
 * Black / White live on the tone page (no sidebar rows since 2026-11-19).
 * INFO there cycles Hi/Sh -> Black/White -> Mid -> Hi/Sh. The Black/White
 * state is the stock Hi/Sh state with P+ST_TM = 1: the page's Shadows and
 * Highlights children then read and write Blacks and Whites instead
 * (tone_alias in ui_read / ui_write), so OM's own dials, value labels and
 * Reset work on them. The "Sh" / "Hi" title images become "Bl" / "Wh" (OM's
 * glyphs, new resource images); in Hi/Sh the hint ("Mid INFO") reads
 * "Bl/Wh INFO". The state lasts until INFO leaves it or
 * power-off, like OM's own Hi/Sh / Mid choice (setting 2189).
 * Storage: Blacks 965 / 966 / 967, Whites 993 / 997 / 1020 (unused profile-4
 * cells, default 0), -7..+7 with a copy of tone 976's descriptor.
 * Split tone: three tints per Color Profile (shadows, midtones, highlights),
 * each one colour of the colour wheel's twelve and a strength 0..5, set on
 * the colour wheel's axes 3..5 (trash: Saturation, Hue, Lightness, Shadow
 * Tint, Midtone Tint, Highlight Tint). A tint axis shows the strength on its
 * colour and 0 elsewhere; setting a colour moves the tint there. Cell value
 * strength * 16 + colour (0 = none), cells tint_ids (Color Profile 4's
 * colour-sector cells; descriptor: byte list 0..95 at 0x60207318).
 * research/OM5II-SPLIT-TONE-2026-11-19.md, OM5II-BLACKS-WHITES-2026-11-18.md */
BW_STEP = 20                    /* curve units (0..1023) per Black / White step */
.section .tone_info_ptr,"a"      /* tone editor types 0x1531..0x1533 (Color Profile 1..3): INFO */
 .long tone_info
.section .tone_info_ptr2,"a"
 .long tone_info
.section .tone_info_ptr3,"a"
 .long tone_info

.section .ext5,"ax"
/* d3 = kind (0..2 Color Profile 1..3), a2 = context: P's Black / White in
 * curve units and the split-tone tables, for context 0 only (0 in other
 * modes). call bw_refresh,[d2,d3,a2,a3],20 */
bw_refresh:
 mov a2,d0
 cmp 0,d0
 bne bw_rf_out
 call st_ptr,[],8
 cmp 0,a0
 beq bw_rf_out
 mov a0,a3                       /* a3 = P */
 clr d2                          /* 0 Blacks, 1 Whites */
bw_rf_loop:
 clr d0
 cmp 3,d3
 bcc bw_rf_put
 mov d2,d0
 add d2,d0
 add d2,d0
 add d3,d0
 add d0,d0
 mov bw_ids,a0
 add d0,a0
 movhu (a0),d0
 mov d0,a0
 call rt_get1,[],4
 extb d0
 mov BW_STEP,d1
 cmp 0,d2
 beq bw_rf_mul
 mov -BW_STEP,d1                 /* + White brightens: W lowers the white end when negative */
bw_rf_mul:
 mul d1,d0
bw_rf_put:
 mov a3,a0
 add d2,a0
 add d2,a0
 movhu d0,(BW_B,a0)
 inc d2
 cmp 2,d2
 bcs bw_rf_loop
 call tint_refresh,[d2,d3,a2,a3],32
 mov (GS_GEN,a3),d0              /* tables rebuilt: each gamma cache misses once (gs_hook) */
 inc d0
 mov d0,(GS_GEN,a3)
bw_rf_out:
 ret [d2,d3,a2,a3],20

.section .ext3,"a"
/* Descriptors (stock format, linked by cp_nd_link), built in P at arming:
 * Black / White as tone 976's (-7..+7), the tints a byte list 0..95 (E148's
 * identity table 0x60207318). Ids: bw_ids then tint_ids.
 * a2 = P -> a3 = the first. call cad_build,[d2,d3],12 */
cad_build:
 mov a2,a0
 add CAD_DESC,a0
 mov bw_ids,a1
 clr d3
cb_loop:
 mov cad_tpl,a3
 cmp 6,d3
 bcs cb_copy
 add 16,a3
cb_copy:
 movhu (a1),d0
 movhu d0,(a0)
 mov 0x80,d0
 movhu d0,(2,a0)
 mov (a3),d0
 mov d0,(4,a0)
 clr d0
 mov d0,(8,a0)
 mov (4,a3),d0
 mov d0,(12,a0)
 mov (8,a3),d0
 mov d0,(16,a0)
 add 2,a1
 add 20,a0
 inc d3
 cmp 15,d3
 bcs cb_loop
 mov a2,a3
 add CAD_DESC,a3
 ret [d2,d3],12
.balign 4
cad_tpl:                         /* list, {count, kind}, flags */
 .long 0x6050ce24
 .hword 30, 2
 .long 0x401
 .long 0
 .long 0x60207318
 .hword 96, 1
 .long 0x100
 .long 0
CAD_NDESC = 15

/* The tone view's own label update 0x60df862e (a0 = the view; called at
 * 0x60df85f3 and 0x60df8626, each followed by ret [a2],8) shows OM's labels
 * again after each change; both calls jump here: OM's update, then, once
 * armed, tone_labels_v. Section 3 loads before the GUI. */
.section .tv_call1,"ax"
 jmp tv_upd
.section .tv_call2,"ax"
 jmp tv_upd
.section .ext3,"a"
tv_upd:
 call tone_view_stock,[d2,d3,a2,a3],48
 call tv_after,[d2,d3,a2,a3],24
 ret [a2],8
tv_after:                        /* a2 = the view; d0 kept */
 mov d0,(4,sp)
 call st_ptr,[],8
 cmp 0,a0
 beq tva_out
 call tone_labels_v,[d2,d3,a2,a3],24
tva_out:
 mov (4,sp),d0
 ret [d2,d3,a2,a3],24
bw_ids:                          /* Blacks of Color Profile 1..3, then Whites */
 .hword 965, 966, 967, 993, 997, 1020
tint_ids:                        /* zone z of Color Profile p: 3z + p (shadows, midtones, highlights) */
 .hword 968, 969, 970, 971, 972, 973, 974, 975, 964
/* R, G, B of each wheel colour (Yellow at the top, clockwise; hue 60 - 30k
 * degrees): 64 cos(h - 120c), sum 0 */
tint_rgb:
 .byte 32,32,-64
 .byte 55,0,-55
 .byte 64,-32,-32
 .byte 55,-55,0
 .byte 32,-64,32
 .byte 0,-55,55
 .byte -32,-32,64
 .byte -55,0,55
 .byte -64,32,32
 .byte -55,55,0
 .byte -32,64,-32
 .byte 0,55,-55

.section .ext8,"ax"
/* z = 0..2 (shadows, midtones, highlights): T[z] = strength * tint_rgb[colour]
 * into P+TINT_T; then, when any is set, deltas for table index i (u = i - 128,
 * w = u * u): edge zone (shadows below the middle, highlights above) * w plus
 * midtones * (16384 - w), / 16384, into the buffer's delta tables, and
 * ST_A = 1. d3 = kind, a3 = P. Settings task (refresh).
 * call tint_refresh,[d2,d3,a2,a3],32 */
tint_refresh:
 clr d0
 movhu d0,(ST_A,a3)
 mov d0,(4,sp)                   /* any zone set */
 clr d2
tn_zone:
 clr d0
 cmp 3,d3
 bcc tn_have
 mov d2,d0
 add d2,d0
 add d2,d0
 add d3,d0
 add d0,d0
 mov tint_ids,a0
 add d0,a0
 movhu (a0),d0
 mov d0,a0
 clr d0
 mov 1,d1
 call refresh_get,[d2],8
 extbu d0
tn_have:
 mov d0,d1
 lsr 4,d1                        /* strength */
 and 15,d0                       /* colour */
 cmp 12,d0
 bcc tn_off
 cmp 6,d1
 bcs tn_ok
tn_off:
 clr d0
 clr d1
tn_ok:
 mov tint_rgb,a0
 add d0,a0
 add d0,a0
 add d0,a0
 mov (4,sp),d0
 or d1,d0
 mov d0,(4,sp)
 mov d2,d0
 add d0,d0
 add d2,d0
 add d0,d0
 mov a3,a1
 add d0,a1
 .rept 3
 movbu (a0),d0
 extb d0
 mul d1,d0
 movhu d0,(TINT_T,a1)
 inc a0
 add 2,a1
 .endr
 inc d2
 cmp 3,d2
 bcs tn_zone
 mov (4,sp),d0
 mov (BW_B,a3),d1                /* Blacks | Whites << 16 */
 or d1,d0
 cmp 0,d0
 beq tn_out
 mov (ST_BUF,a3),a2
 cmp 0,a2
 bne tn_build
 mov ST_BUF_SIZE,d0
 call malloc,[],4
 mov a0,(ST_BUF,a3)
 mov a0,a2
 cmp 0,a2
 beq tn_out
tn_build:
 jmp tn_tables                     /* ext3: the delta tables */
tn_out:
 ret [d2,d3,a2,a3],32


.section .ext3,"a"
/* tint_refresh (ext8) continues here, in its own frame, once a tint or Black /
 * White is set: a2 = the buffer, a3 = P. For table index i (u = i - 128, w =
 * u * u) and channel c: delta_c[i] = (w * T[edge][c] + (16384 - w) *
 * T[mid][c]) >> 14 - (X * u) >> 5, X = Blacks (P+BW_B) for u < 0, Whites
 * (P+BW_W) from the middle up; i.e. Blacks lift the black end by 4 * B (0..4095
 * units) fading linearly to 0 at the middle, Whites move the white end by -4 * W.
 * The same delta goes to R, G and B, so Black / White leave the colour alone. */
tn_tables:
 add 1552,a2
 clr d3
tn_i:
 mov d3,d0
 add -128,d0
 mov a3,a0                       /* Blacks below the middle, Whites above */
 cmp 0,d0
 blt tn_bw
 add 2,a0
tn_bw:
 movhu (BW_B,a0),d1
 exth d1
 mul d0,d1
 asr 5,d1
 mov d1,(12,sp)                  /* X * u / 32: X * 4 * (-u) / 128, subtracted below */
 mov d0,d1
 mul d0,d1
 mov d1,(8,sp)
 mov 16384,d2
 sub d1,d2
 mov a3,a0
 add TINT_T+6,a0
 mov a3,a1
 add TINT_T,a1
 cmp 0,d0
 blt tn_c
 add 12,a1
tn_c:
 mov (8,sp),d1
 movhu (a1),d0
 exth d0
 mul d1,d0
 mov d0,(4,sp)
 movhu (a0),d0
 exth d0
 mul d2,d0
 mov (4,sp),d1
 add d1,d0
 asr 14,d0
 mov (12,sp),d1
 sub d1,d0
 movhu d0,(a2)
 add 2,a0
 add 2,a1
 add 512,a2
 mov a3,d0
 add TINT_T+12,d0
 cmp d0,a0
 bne tn_c
 add -1534,a2
 inc d3
 cmp 256,d3
 bcs tn_i
 mov 1,d0
 movhu d0,(ST_A,a3)
 ret [d2,d3,a2,a3],32

.section .ext5,"ax"
/* d2 = sector cell 928+12p+k, a3 = axis 3..5 -> d0 = the tint cell, d1 = k.
 * call tint_cell,[],4 */
tint_cell:
 mov d2,d0
 add -928,d0
 clr d1
tc_div:
 cmp 12,d0
 bcs tc_done
 add -12,d0
 inc d1
 bra tc_div
tc_done:
 cmp 3,d1
 bcs tc_p
 mov 2,d1
tc_p:
 mov d0,a1
 mov a3,d0
 add -3,d0
 add d0,d1
 add d0,d1
 add d0,d1
 add d1,d1
 mov tint_ids,a0
 add d1,a0
 movhu (a0),d0
 mov a1,d1
 ret [],4

.section .ext10,"ax"
/* From ui_read (its frame): d2 = sector cell, d3 = axis -> d0 = strength
 * on the tint's colour, 0 elsewhere. */
tint_read:
 mov d3,a3
 call tint_cell,[],4
 mov d1,d3
 call stock_get,[],4
 mov d0,d1
 and 15,d1
 cmp d3,d1
 bne tint_zero
 lsr 4,d0
 ret [d2,d3,a2,a3],24
tint_zero:
 clr d0
 ret [d2,d3,a2,a3],24

.section .ext9,"ax"
/* From ui_write (its frame): d0 = axis, d2 = sector cell, d3 = value,
 * a2 = the writer's a0. Strength 1..5 puts the tint on this colour, 0 clears
 * it if it is here; then the editor's children follow. */
tint_write:
 mov d0,a3
 mov ST_RESET,d0
 call st_getb,[],12
 cmp 0,d0
 beq tw_nr
 clr d3
tw_nr:
 cmp 0,d3
 bge tw_pos
 clr d3
tw_pos:
 cmp 5,d3
 ble tw_le
 mov 5,d3
tw_le:
 call tint_cell,[],4
 mov d1,(4,sp)
 mov d0,a3
 call stock_get,[],4
 mov d3,d1
 cmp 0,d1
 bne tw_set
 and 15,d0
 mov (4,sp),d1
 cmp d1,d0
 bne tw_done
 clr d1
 bra tw_put
tw_set:
 asl 4,d1
 mov (4,sp),d0
 or d0,d1
tw_put:
 mov a3,d0
 mov a2,a0
 call stock_ui_write,[d2,d3,a2,a3],20
 call refresh_children,[d2,d3,a2,a3],24
tw_done:
 mov 1,d0
 ret [d2,d3,a2,a3],24

/* d0 = setting id -> d0 = the id the UI edits: in the Black/White state on
 * Color Profile p, Shadows 978+3p -> Blacks, Highlights 976+3p -> Whites.
 * call tone_alias,[d2,d3],12 */
tone_alias:
 mov d0,d2
 call st_ptr,[],8
 cmp 0,a0
 beq ta_out
 movbu (ST_TM,a0),d0
 cmp 0,d0
 beq ta_out
 mov 111,d0
 call stock_get,[],4
 add -54,d0
 cmp 3,d0
 bcc ta_out
 mov d0,d3
 add d0,d0
 add d3,d0
 add 976,d0
 mov bw_ids+6,a0
 cmp d0,d2
 beq ta_pick
 add 2,d0
 mov bw_ids,a0
 cmp d0,d2
 bne ta_out
ta_pick:
 add d3,a0
 add d3,a0
 movhu (a0),d0
 ret [d2,d3],12
ta_out:
 mov d2,d0
 ret [d2,d3],12

.section .ext2,"ax"          /* reached from the GUI before arming too */
/* Tone editor INFO (types 0x1531..0x1533, slots 0x61210790 / 0x612107c8 /
 * 0x61210800 of the type records at 0x6120e9dc, stock 0x60e9e8ff; entered
 * by calls from 0x60e9c10e: a0 = editor, d0 / d1 the command) -> d0. On
 * Color Profile 1-3 once armed: Hi/Sh -> Black/White (consumed, OM's state
 * stays Hi/Sh), Black/White -> Mid (OM's own step), Mid -> Hi/Sh (OM's). */
tone_info:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov a0,a2
 mov d0,d2
 mov d1,d3
 call st_ptr,[],8
 cmp 0,a0
 beq ti_stock
 mov a0,a3
 mov 111,d0
 call stock_get,[],4
 add -54,d0
 cmp 3,d0
 bcc ti_stock
 movbu (ST_TM,a3),d0
 cmp 0,d0
 bne ti_from_bw
 movhu (122,a2),d0
 cmp 0,d0
 bne ti_stock
 mov 1,d0
 movbu d0,(ST_TM,a3)
 call tone_refresh,[d2,d3,a2,a3],24
 mov 1,d0
 ret [d2,d3,a2,a3],24
ti_from_bw:
 clr d0
 movbu d0,(ST_TM,a3)
 call tone_refresh,[d2,d3,a2,a3],24
ti_stock:
 mov a2,a0
 mov d2,d0
 mov d3,d1
 calls tone_info_stock
 ret [d2,d3,a2,a3],24

.section .ext2,"ax"
/* a2 = tone editor: its value children (setting at +80, index at +94 of the
 * list +7..-7) take what the page now edits; then the editor's own update
 * (0x900c, its +72) redraws. call tone_refresh,[d2,d3,a2,a3],24 */
tone_refresh:
 mov a2,a3
 add 128,a3                      /* children 1..3; child 0 is the Hi/Sh / Mid switch */
 mov 3,d3
trf_loop:
 mov (a3),a0
 cmp 0,a0
 beq trf_next
 movhu (80,a0),d0
 mov d0,d1
 add -976,d1
 cmp 9,d1
 bcc trf_next
 call ui_read,[d2,d3,a2,a3],24
 mov 7,d1
 sub d0,d1
 mov (a3),a0
 movhu d1,(94,a0)
trf_next:
 add 4,a3
 add -1,d3
 bne trf_loop
 mov a2,a0
 mov 0x900c,d0
 clr d1
 mov (72,a2),a1
 calls (a1)
 ret [d2,d3,a2,a3],24

.section .ext9,"ax"
/* a0 = the tone page (child 2) -> its view; a2 = the view. The title and
 * hint labels follow the state: Black/White (Color Profile, P+ST_TM = 1):
 * titles "Bl" / "Wh" (IMG_BL / IMG_WH, OM's glyphs) instead of "Sh" / "Hi";
 * OM's value labels (sign, digit) get Blacks / Whites (tl_val). Hi/Sh on a Color Profile: the hint is OM's "Mid INFO" with
 * "Mid" left blank (IMG_HINT), tone_text writes "Bl/Wh" there. Otherwise
 * (Mid, other modes) OM's images. Each label's image slot 0 is set through
 * OM's label_img (no-op when unchanged); OM's own update never resets it, so
 * every state writes all three. Runs at each layout (pg_tone) and after OM's
 * view update (tv_upd). call tone_labels,[d2,d3,a2,a3],24 */
IMG_BL = 0x3e80
IMG_WH = 0x3e81
IMG_HINT = 0x3e82
IMG_SH = 0x1078                  /* label ids: OM's tone view records (0x610d5aa8 ..) */
IMG_HI = 0x1077
IMG_MIDINFO = 0x3f7f
tone_labels:
 mov (36,a0),a2
tone_labels_v:
 cmp 0,a2
 beq tl_out
 call st_ptr,[],8
 cmp 0,a0
 beq tl_out
 movbu (ST_TM,a0),d3
 mov 111,d0
 call stock_get,[],4
 add -54,d0
 cmp 3,d0
 bcs tl_cp
 clr d3                          /* other modes: OM's images */
 bra tl_set
tl_cp:
 mov d0,(4,sp)                   /* profile 0..2 */
 cmp 0,d3
 bne tl_set                      /* 1: Black/White */
 mov 2,d3                        /* Hi/Sh: our hint. Which hint OM shows */
 mov (856,a2),a0                 /* (label 16's index: 0 "Mid INFO", 1 "Hi/Sh */
 cmp 0,a0                        /* INFO") decides, not setting 2189: on the */
 beq tl_set                      /* camera Bl/Wh was drawn over "Hi/Sh INFO" */
 movbu (132,a0),d0
 cmp 0,d0
 beq tl_set
 clr d3                          /* Mid: OM's */
tl_set:                          /* d3: 0 OM, 1 Black/White, 2 Hi/Sh */
 call st_ptr,[],8
 clr d0
 cmp 2,d3
 bne tl_h0
 mov 1,d0
tl_h0:
 movbu d0,(ST_HINT,a0)           /* for tone_text */
 mov IMG_SH,d1
 cmp 1,d3
 bne tl_t1
 mov IMG_BL,d1
tl_t1:
 mov 800,d0                      /* label 2 */
 call tl_img,[],8
 mov IMG_HI,d1
 cmp 1,d3
 bne tl_t2
 mov IMG_WH,d1
tl_t2:
 mov 832,d0                      /* label 10 */
 call tl_img,[],8
 mov IMG_MIDINFO,d1
 cmp 2,d3
 bne tl_t3
 mov IMG_HINT,d1
tl_t3:
 mov 856,d0                      /* label 16, the hint */
 call tl_img,[],8
 cmp 1,d3
 bne tl_inval
 mov (4,sp),d2                   /* Black/White: OM's view shows its data model's */
 add d2,d2                       /* (976.., not aliased) Sh / Hi values; show */
 add bw_ids,d2                   /* Blacks / Whites with the same images */
 mov d2,a0
 movhu (a0),d0
 mov 804,d1                      /* labels 3 / 4 */
 call tl_val,[d2,d3],16
 mov d2,a0
 movhu (6,a0),d0
 mov 836,d1                      /* labels 11 / 12 */
 call tl_val,[d2,d3],16
tl_inval:
 mov a2,a0                       /* repaint the view (tone_text) */
 mov 0,a1
 mov 1,d0
 call ui_invalidate,[],4
tl_out:
 ret [d2,d3,a2,a3],24
/* a2 = the view, d0 = label offset (792 + 4k), d1 = image id: slot 0.
 * Keeps d3, a2. call tl_img,[],8 */
tl_img:
 mov a2,a0
 add d0,a0
 mov (a0),a0
 cmp 0,a0
 beq tli_out
 clr d0
 call label_img,[d2,a2],12
tli_out:
 ret [],8
/* a2 = the colour view, a3 = its paint context (from paint_axis, armed, after
 * gfx_wheel). OM's selected-colour swatch (view label 4, +808) has 8 images
 * for the OM-1 / OM-3 wheel: 7 colours and "All" (slot 7). With E148's 12
 * colours it repeated every second colour (owner, 2026-11-20). Its colour
 * slots 0..6 get the blank IMG_BLANK (OM never resets them; label_img does
 * nothing when unchanged) and the selected colour's swatch is drawn here, as
 * OM's: frame in palette 7, 22 x 22 at (586, 90), fill 20 x 20 in the wheel's
 * colour (gtab_col). "All" stays OM's. call wheel_swatch,[d2,d3,a2,a3],28 */
IMG_BLANK = 0x3e83
wheel_swatch:
 mov (808,a2),a2                 /* not 0: paint_axis checked it */
 clr d3
ws_loop:
 mov a2,a0
 mov d3,d0
 mov IMG_BLANK,d1
 call label_img,[d2,a2],12
 inc d3
 cmp 7,d3
 bcs ws_loop
ws_draw:
 mov (scr_obj),a0                /* the colour editor, as gfx_wheel finds it */
 cmp 0,a0
 beq ws_out
 mov (a0),a0
 cmp 0,a0
 beq ws_out
 mov (76,a0),a0
 cmp 0,a0
 beq ws_out
 movhu (120,a0),d0
 cmp 13,d0
 bne ws_out
 movhu (122,a0),d0               /* 1..12, 0 = all */
 add -1,d0
 cmp 12,d0
 bcc ws_out
 mov gtab_col,a0
 add d0,a0
 movbu (a0),d0
 mov d0,(4,sp)
 mov a3,a2                       /* gfx_bar's context */
 mov 7,d0                        /* frame */
 clr d1
 call ws_box,[d2,d3,a2,a3],28
 mov (4,sp),d0                   /* fill, 1 px in */
 mov 1,d1
 call ws_box,[d2,d3,a2,a3],28
ws_out:
 ret [d2,d3,a2,a3],28
/* a2 = context, d0 = colour, d1 = inset k: block (586 + k, 90 + k), 22 - 2k
 * square. call ws_box,[d2,d3,a2,a3],28 */
ws_box:
 mov d1,d2
 mov a2,a0
 call pen_color,[d2,d3,a2,a3],16
 mov 22,d3
 sub d2,d3
 sub d2,d3
 mov 586,d0
 add d2,d0
 mov 90,d1
 add d2,d1
 mov d3,d2
 call gfx_bar,[d2,d3,a2,a3],28
 ret [d2,d3,a2,a3],28
/* a2 = the view, d0 = setting, d1 = its sign label's offset (the digit
 * label follows): OM's image indices (0x60df89bd): sign 0 for 0, 1 for +,
 * 2 for -; digit |v|. call tl_val,[d2,d3],16 */
tl_val:
 mov d1,d3
 call stock_get,[],4
 extb d0
 mov d0,d2
 clr d0
 cmp 0,d2
 beq tlv_s
 mov 1,d0
 cmp 0,d2
 bgt tlv_s
 mov 2,d0
tlv_s:
 mov a2,a0
 add d3,a0
 mov (a0),a0
 call label_index,[d2,a2],12
 mov d2,d0
 cmp 0,d0
 bge tlv_d
 not d0
 inc d0
tlv_d:
 mov a2,a0
 add d3,a0
 mov (4,a0),a0
 call label_index,[d2,a2],12
 ret [d2,d3],16

.section .ext6,"ax"
/* a2 = paint context, a1 = UTF-16 text, d0 = x, d1 = y, d2 = width: the text
 * in OM's font, centred in a box 32 high (as paint_axis).
 * call tx_draw,[d2,d3,a2,a3],44 */
tx_draw:
 mov a1,(4,sp)
 movhu d0,(8,sp)
 add d2,d0
 movhu d0,(12,sp)
 movhu d1,(10,sp)
 add 32,d1
 movhu d1,(14,sp)
 movhu (52,a2),d0
 mov d0,(16,sp)
 mov (76,a2),d0
 mov d0,(20,sp)
 mov a2,a0
 mov 1,d0
 call stock_font,[a2],8
 cmp 0,a0
 beq tx_restore
 mov a0,(24,sp)
 mov 2,d0
 movhu d0,(52,a2)
 mov (4,sp),d1
 mov a2,a0
 mov sp,a1
 add 8,a1
 mov text_style,d0
 call stock_text,[d2,d3,a2,a3],16
 mov (24,sp),a0
 call stock_font_release,[],4
tx_restore:
 mov (16,sp),d0
 movhu d0,(52,a2)
 mov (20,sp),d0
 mov d0,(76,a2)
 ret [d2,d3,a2,a3],44
.section .ext3,"a"
/* a2 = paint context: "Bl/Wh" in the hint's blank part while tone_labels
 * shows IMG_HINT (P+ST_HINT). call tone_text,[d2,d3,a2,a3],48 */
tone_text:
 call st_ptr,[],8
 cmp 0,a0
 beq tt_out
 movbu (ST_HINT,a0),d0           /* tone_labels put IMG_HINT in the label */
 cmp 0,d0
 beq tt_out
 mov text_bw,a1
 mov 290,d0                      /* the blank 62 px of IMG_HINT start at 296 */
 mov 426,d1
 mov 68,d2
 call tx_draw,[d2,d3,a2,a3],44
tt_out:
 ret [d2,d3,a2,a3],48
.section .ext8,"ax"
.balign 2
text_bw:                         /* the hint; titles are images (owner, 2026-11-20) */
 .short 'B','l','/','W','h',0

.section .ext6,"ax"
.balign 2
text_switch:
 .short 'S','w','i','t','c','h',' ','@','A','0','3','4','@',0

/* Live view (owner, 2026-11-20: Black / White changed live view only after a
 * half-press). E148's gamma stage 0x603e69ae keeps a cache record per
 * pipeline (d3 = (R+1484) + 5736: the selected R/G/B table pointers and a
 * descriptor) and on a hit skips the curve setter, so the hardware keeps its
 * curves. OM's own tone values change the selected tables (a miss); Black /
 * White and the tints change only P's delta tables, so live view kept hitting.
 * gs_hook replaces cmp 0,d3; beq 0x603e6aa3; mov (56,sp),a0 at 0x603e6a3b:
 * once armed, a cache that has not seen the current GS_GEN (bw_refresh adds 1
 * after each table rebuild) takes the stock miss path once (as with d3 = 0,
 * the cache is then refilled). No call: d0, d1, a0, a1 are free here (the
 * stage reloads them); d2 (= 1) and d3 are kept. In section 8, which loads
 * first after section 1 (section 2 has no room). */
.section .gs_hook,"ax"
 jmp gs_entry
 nop
.section .ext8,"ax"
gs_entry:
 cmp 0,d3
 beq gs_miss
 movhu (st_handle_u),d0
 cmp 0,d0
 beq gs_go
 add ST_POOL-1,d0
 mov d0,a0
 mov (ST_MAGIC,a0),d1
 cmp ST_MAGIC_VALUE,d1
 bne gs_go
 mov (GS_GEN,a0),d1
 mov a0,a1
 add GS_TAB+32,a1                /* end of the table */
 add GS_TAB,a0
gs_find:
 mov (a0),d0
 cmp d3,d0
 beq gs_found
 cmp 0,d0
 beq gs_new
 add 8,a0
 cmp a1,a0
 bne gs_find
 add -8,a0                       /* full: reuse the last entry */
gs_new:
 mov d3,(a0)
 bra gs_seen
gs_found:
 mov (4,a0),d0
 cmp d1,d0
 beq gs_go
gs_seen:
 mov d1,(4,a0)
gs_miss:
 jmp gs_miss_back
gs_go:
 mov (56,sp),a0
 jmp gs_back

/* Split tone entry: the R/G/B curve setter 0x603e6974 is a leaf that returns
 * with retf (MDR) and whose frame has no slot for a return address, so
 * nothing here calls: st_ptr's check is inline. d2 and a2 are free at its
 * entry (its callers save them). Unarmed: replay the 5 replaced bytes and
 * continue. Armed: wb.s st_tint (section 4, fixed address) gets a2 = P,
 * d2 = MDR and continues the setter itself. */
.section .st_hook,"ax"
 jmp st_entry
.section .ext2,"ax"
st_entry:
 movhu (st_handle_u),d2          /* st_ptr, inline: a call would write its */
 cmp 0,d2                        /* return address over the setter's saved a2 */
 beq st_unarmed
 add ST_POOL-1,d2
 mov d2,a2
 mov (ST_MAGIC,a2),d2
 cmp ST_MAGIC_VALUE,d2
 bne st_unarmed
 mov mdr,d2
 jmp st_tint
st_unarmed:
 mov a0,a2
 inc4 a2
 mov d1,d2
 mov d0,d1
 mov (a2),d0
 jmp setter_back
