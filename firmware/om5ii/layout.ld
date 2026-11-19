/* OM-5 Mark II 1.1 (E148 build 1100) runtime addresses. */
SECTIONS {
 .delete_pointer 0x61234464 : { *(.delete_pointer) }
 .label_hook 0x60e4ade9 : { *(.label_hook) }
 .container_pointer 0x611a0c54 : { *(.container_pointer) }
 .reset_hook 0x60e9e0f4 : { *(.reset_hook) }
 .read_hook 0x6091c66d : { *(.read_hook) }
 .write_hook 0x6091c6bd : { *(.write_hook) }
 .display_hook 0x60a33eac : { *(.display_hook) }
 .builder_hook 0x603e7eb0 : { *(.builder_hook) }
 .parent_hook 0x60ea0180 : { *(.parent_hook) }
 .paint_pointer 0x610c1540 : { *(.paint_pointer) }
 .tone_pointer 0x610d6600 : { *(.tone_pointer) }
 .filter_pointer 0x610d9bc0 : { *(.filter_pointer) }
 .cp_any_hook 0x60d22357 : { *(.cp_any_hook) }
 .pages_hook 0x60dad5f5 : { *(.pages_hook) }
 .ext2 0x605af4b0 : { *(.ext2) }
 .ext6 0x60ca7b00 : { *(.ext6) }
 .ext7 0x612a4b98 : { *(.ext7) }
 .arm_hook 0x602f0b95 : { *(.arm_hook) }
 .extvec 0x613f2ffc : { *(.extvec) }
 .refresh_hook 0x602e0826 : { *(.refresh_hook) }
 .creset_hook 0x602db531 : { *(.creset_hook) }
 .refresh_cases 0x604997f0 : { *(.refresh_cases) }
 .pm_s1 0x602e0f82 : { *(.pm_s1) }
 .pm_s2 0x602e1119 : { *(.pm_s2) }
 .pm_s4 0x602e0fe8 : { *(.pm_s4) }
 .pm_s5 0x602e11fc : { *(.pm_s5) }
 .ext8 0x613f2b80 : { *(.ext8) }
 .ext5 0x60845a00 : { *(.ext5) }
 .hook_str 0x60d52ed5 : { *(.hook_str) }
 .ext10 0x6169c820 : { *(.ext10) }
 .bw_hook 0x60385f9c : { *(.bw_hook) }
 .bw_gate_call 0x603e86a8 : { *(.bw_gate_call) }
 .rfa_hook 0x60e49d6f : { *(.rfa_hook) }
 .rfb_hook 0x60e4a1a4 : { *(.rfb_hook) }
 .bw_slot4 0x611a0ab8 : { *(.bw_slot4) }
 .bw_style_hook 0x60e4b02c : { *(.bw_style_hook) }
 .bw_knob_hook 0x60e4a9de : { *(.bw_knob_hook) }
 .bw_cell_hook 0x60e4a37a : { *(.bw_cell_hook) }
 .bw_label_hook 0x60e4b09d : { *(.bw_label_hook) }
 .bw_slot5 0x611a0ac8 : { *(.bw_slot5) }
 .bw_wslot4 0x611b7ac8 : { *(.bw_wslot4) }
 .bw_wslot6 0x611b7ad8 : { *(.bw_wslot6) }
}
screen_forward = 0x60ed5c18;
stock_delete_action = 0x60ed6476;
stock_container = 0x60e3ca0a;
label_resume = 0x60e4adf3;
tone_gate = 0x60385b9c;          /* any of five tone values non-zero -> d0 = 1; call [],0 / retf */
bw_resume = 0x60385fa1;
row_table = 0x611b50f8;         /* 17 Picture Mode row records x 40 */
row_slider_widget = 0x60e49fdf; /* row-widget handler of the slider rows (table 0x611b7aa8) */
row_slider = 0x60e3cd53;
knob_shading = 0x60e4aa19;      /* slider knob: Shading's case (effective 1016, -5..+5) */
knob_none = 0x60e4aa37;
cell_back = 0x60e4a37f;         /* panel row handler after mov 1016,d0; calls (a2) */
knob_store = 0x60e4aa35;        /* slider knob: store max d0 at (4,sp), min in a3 */
settings_obj = 0x608eedd3;      /* -> a0 = settings object (vtable +8: value getter) */
bw_style_back = 0x60e4b031;     /* slider style lookup after its first 5 bytes */
bw_label_back = 0x60e4b0a2;     /* slider value-label lookup after its first 5 bytes */        /* resolver: d0 = setting -> slider row (Sharpness / Contrast path) */
rfa_back = 0x60e49d87;          /* after the record loop at 0x60e49d6f */
rfb_back = 0x60e4a1ba;          /* after the record loop at 0x60e4a1a4 */          /* tone-curve modifier after the 5 hooked bytes (bw_hook) */
label_format = 0x611b5af0;
reset_resume = 0x60e9e0fa;
parent_resume = 0x60ea0185;
read_resume = 0x6091c674;
write_resume = 0x6091c6c4;
stock_display_next = 0x6092bbfc;
display_resume = 0x60a33eb3;
builder_resume = 0x603e7eb5;
stock_get = 0x602d000d;
stock_ui_write = 0x60855cdc;
active_read = 0x602f50f8;
active_write = 0x602f5121;
color_builder = 0x603e7c3f;
stock_paint = 0x60d47237;
stock_font = 0x60d51f07;
stock_text = 0x60d4b7bc;
stock_font_release = 0x60d529eb;
direct_layout = 0x60f05251;
direct_ret = 0x60dad5fc;
child_get = 0x60dad302;
set_visible = 0x60f04d10;
refresh_get = 0x602d2fc2;
refresh_set = 0x602d2fdb;
raw_get = 0x602f4c5b;
refresh_default = 0x602e06ca;
creset_resume = 0x602db536;
/* Completed initialization, not the asynchronous load-submission word at +4. */
loaded_bits = 0xa26e2694;
prop_byte = 0x602bbed5;
wc_set = 0x602f5173;
wc_get = 0x602f514d;
/* Heap state block (hsl.s .ext2). The handle is the padding halfword after the
 * HLS event manager's task id (object 0x6218c250, id at +0xac, next field +0xb0). */
st_handle = 0x6218c2fe;
st_handle_u = 0xa218c2fe;   /* the same halfword in RAM, past any CPU's cache */
hls_tid = 0x6218c2fc;
ST_POOL = 0xa1e27d80;      /* class-1 heap pool 0xa1e27d80..0xa1e32ac0 (free wrapper 0x6002384a; see research/OM5II-HEAP-ALLOCATOR-2026-11-18.md on codex/space-map-tooling) */
ST_HANDLE_MAX = 43329;     /* pool span 44352 - block 1024 + 1 */
trig = 0x602f0cc2;
trig_resume = 0x602f0b9a;
get_tid = 0x600317b4;
malloc = 0x60023818;
pm_refresh = 0x602e082f;   /* d0 context; call ...,[d2],88 (wb.s uses the same) */
/* films.s */
str_lang = 0x60d52eec;
str_back = 0x60d52edb;
fopen = 0x606aa3bd;        /* a0 path, a1 mode -> a0 handle or 0; call ...,[],4 */
fclose = 0x606aa3c6;       /* a0 handle; call ...,[d2,a2,a3],16 */
fread = 0x606aa54e;        /* a0 buffer, d0 item size, d1 count, a1 handle -> d0 items; call ...,[d2,d3,a2,a3],24 */
MS_A = 0x61e43b88;         /* medium status words: 0xf000 = MOUNT OK */
MS_B = 0x61e43b90;
MS_C = 0x61e43b98;
scr_obj = 0x61e588f4;      /* the direct-setting screen object; +4 = its panel updater (vtable entry 0) */
ui_timer = 0x60f10fd2;     /* restart GUI timer d0 for d1 ms (cancel 0x60d534c8, start 0x60d53421); call ...,[d2,d3],12 */
desc_find = 0x602e1edb;    /* setting id d0 -> a0 descriptor or 0 (RAM hash 0x620dc288); call ...,[],0 */
desc_buckets = 0x620dc288; /* 128 bucket heads, RAM (.bss) */
cp_nd_desc = 0x604f24f0;   /* data edit cp_nd_descriptors: 2217, 2218, 912..914, 907, 911, 915 */
pen_color = 0x60d51e2c;   /* a0 dc, d0 colour; call ...,[d2,d3,a2,a3],16 */
pen_size = 0x60d51eed;    /* a0 dc, d0 width, d1 height; call ...,[d2,d3],8 */
move_to = 0x60d519e7;     /* a0 dc, d0 x, d1 y; call ...,[],4 */
line_to = 0x60d51774;     /* a0 dc, d0 x, d1 y; call ...,[d2,d3,a2,a3],32 */
cp_ticked = 0x60d223d5;   /* d0 = CP item k (table 0x60f7f57c) -> d0 1 if ticked; call ...,[],4 */
ui_invalidate = 0x60d49294; /* a0 widget, d0 1, a1 rect or 0 (whole widget); call ...,[],4 */
ASSERT(ADDR(.ext7) + SIZEOF(.ext7) <= 0x612a5000, ".ext7 leaves section 7")
ASSERT(SIZEOF(.cp_any_hook) == 7, "cp_any_hook replaces 7 bytes")
ASSERT(ADDR(.ext5) + SIZEOF(.ext5) <= 0x60846000, ".ext5 leaves section 5")
ASSERT(ADDR(.ext10) + SIZEOF(.ext10) <= 0x6169d000, ".ext10 leaves section 10")
ASSERT(st_ptr == 0x605af4b0, "wb.ld binds st_ptr")
ASSERT(ADDR(.ext2) + SIZEOF(.ext2) <= 0x605af780, ".ext2 runs into the WB gate")
ASSERT(ADDR(.ext8) + SIZEOF(.ext8) <= 0x613f2f20, ".ext8 runs into the WB profile helper")
