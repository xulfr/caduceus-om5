SECTIONS {
 .wb_hook 0x602d19b6 : { *(.wb_hook) }
 .wb_extension 0x605af780 : { *(.wb_extension) }
 .wb_body 0x60829570 : { *(.wb_body) }
 .wb_profile 0x613f2f20 : { *(.wb_profile) }
 .st_tint 0x60829764 : { *(.st_tint) }
}
PM_ID = 111;
/* Completed initialization, not the asynchronous load-submission word at +4. */
loaded_bits = 0xa26e2694;
commit_resume = 0x602d19bb;
st_ptr = 0x605af4b0;   /* hsl.s .ext2 */
stock_get = 0x602d000d;
stock_ui_write = 0x60855cdc;
active_read = 0x602f50f8;
active_write = 0x602f5121;
pm_refresh = 0x602e082f;
setter_back = 0x603e6979;
st_handle_u = 0xa218c2fe;   /* hsl.s: the state handle, uncached */
ST_POOL = 0xa1e27d80;
ST_HANDLE_MAX = 43329;   /* R/G/B curve setter after its first 5 bytes (st_hook) */
ctx_get = 0x602d2fc2;
ASSERT(ADDR(.wb_extension) + SIZEOF(.wb_extension) <= 0x605af800, "WB gate leaves section 2")
ASSERT(ADDR(.wb_body) + SIZEOF(.wb_body) <= 0x60829764, "WB body runs into st_tint")
ASSERT(ADDR(.st_tint) + SIZEOF(.st_tint) <= 0x60829800, "st_tint leaves section 4")
ASSERT(ADDR(.wb_profile) + SIZEOF(.wb_profile) <= 0x613f2ffc, "WB profile helper runs into the extension vector")
