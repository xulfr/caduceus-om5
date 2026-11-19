/* Colour grain probe cg1 (claude/cp-grain-experiment). NOT tested on a camera.
 *
 * E148's still development request is configured by 0x6036fc58, which calls the
 * combiner selector 0x603ecda1 at 0x6036fc5c as `call SEL,[d2,a2],12` with
 * a0 = the configuration context (+4 the request, +52 the context key).
 * OM-3's camera-proven recipe (caduceus-om3 NOTES gl6/gl7, g21 `xb_dev`, same
 * selector, same call shape) gives a COLOR still the stock grain: for a still
 * (+14 0x1000) development request (kind +16 = 0) with job key +10 = 11 (COLOR),
 * write the grain level, then key 12 (MONO) at +10 and in the context, then
 * select as usual. On E148 the level is request +1828 (read by the combiner-31
 * grain handler 0x603d85b2; OM-3 +1751) and the development effect is +1838
 * (0x603ed07a; OM-3 +1756).
 *
 * Gates (any miss = stock, byte for byte): the request as above, and no own
 * development effect (+1838 = 0: Shading's 0x0c00 would get combiner 33's mono
 * set-up under key 12, a grey picture on OM-3 gl3). Job key 11 is the
 * picture-mode byte (snapshot +28735, copied into params +10 by the key
 * writer 0x604237fc): 11 for Color Profile 1-3 (apply_values), 12 for
 * Monochrome (the selector's MONO entry). The level is
 * effective setting 998, read from store 0 of context 0 (0x602f514d, as 43 stock callers): the
 * refresh sets it to the active Color Profile's grain cell 907 + 4(p-1)
 * (0 Off, 1 Low, 2 Std, 3 High), and 0 in the other colour modes. That read
 * is the same element read (0x6005faa9 with an object) as active_read, which
 * apply_values already makes on the image-builder path (camera-proven there).
 * Grain Off (the default; reset, init and custom-mode copies give 0) = stock. */
.section .cg_hook,"ax"
 call cg_sel,[d2,a2],12

.section .ext8,"ax"
/* Entered in the stock call's frame: d2 / a2 are saved by it and restored by
 * the selector's `ret [d2,a2],12`; (0,sp) is our call slot. Leaves through
 * the selector with a0 = the context. Uses d0, d1, d2, a1, a2. */
.global cg_sel
cg_sel:
 mov (4,a0),a1
 movbu (16,a1),d0
 cmp 0,d0
 bne cg_out
 movhu (14,a1),d0
 cmp 0x1000,d0
 bne cg_out
 movbu (10,a1),d0
 cmp 11,d0
 bne cg_out
 movhu (1838,a1),d0
 cmp 0,d0
 bne cg_out
 mov a0,a2
 call cg_level,[],4
 mov d0,d2
 add -1,d2
 cmp 3,d2
 bcc cg_ctx
 mov (4,a2),a1
 movbu d0,(1828,a1)
 mov 12,d0
 movbu d0,(10,a1)
 mov d0,(52,a2)
cg_ctx:
 mov a2,a0
cg_out:
 jmp cg_select
/* d0 = effective grain 998 (store 0, context 0). Keeps a2 (callee-saved).
 * Separate entry so the emulator test can call it. */
.global cg_level
cg_level:
 mov 998,d0
 call setting_store0,[],4
 ret [],4
