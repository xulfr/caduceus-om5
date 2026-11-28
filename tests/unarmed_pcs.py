#!/usr/bin/env python3
"""Check an unarmed emulator session: which project code ran before any half-press.

    PCS=out.txt PRE=tests/unarmed_pcs.mjs OM_EMU_DIR=... bash tools/dev/run.sh BUILD OUT 'keys without s1'
    python3 tests/unarmed_pcs.py BUILD out.txt        (mn10300-elf-nm on PATH)

Every executed address inside the patch's code ranges must belong to a gate or to a replay of OM's displaced
instructions. Section 3, 4 and 8 or later are forbidden even for an allowlisted symbol. Emulator only."""
import bisect, subprocess, sys
from pathlib import Path

ALLOWED = {
    'st_ptr', 'st_ptr_none', 'st_ptr_out', 'st_axis', 'st_getb', 'st_getb_out',          # the handle read
    'wb_load', 'wb_original',                                             # stock commit
    'refresh_case', 'refresh_guard', 'refresh_stock',          # stock refresh tail
    'fl_str', 'fl_str_stock', 'fl_str_cp',                                # stock string getter
    'pages_hook', 'pg_title', 'pg_t_out',                                 # stock page updater
    'read_hook', 'ui_read', 'ui_read_stock', 'write_hook', 'ui_write', 'ui_write_stock',
    'display_hook', 'display_stock', 'label_get', 'label_get_done',
    'hsl_container', 'container_stock', 'container_restore', 'container_unarmed',
    'hsl_delete_action', 'delete_done', 'delete_restore', 'delete_stock',
    'container_check', 'container_info', 'container_info2', 'info_done',                                        # INFO: stock, then an armed-only branch
    'tv_upd', 'tv_after', 'tva_out', 'ui_alias', 'ua_out',                # stock UI update and same-task state gates
    'parent_hook', 'parent_restore', 'st_set_editor', 'st_set_editor_out',
    'reset_hook', 'st_reset_on', 'st_reset_off', 'st_reset_put', 'st_reset_out',
    'builder_hook', 'builder_stock',
    'creset', 'creset_stock', 'creset_orig',
    'pm_set_a3', 'pm_set_a2', 'pm_set', 'pm_set_done', 'pm_put', 'pm_put_done',
    'arm_hook', 'arm_back', 'paint_axis', 'paint_done',
    'paint_tone', 'pt_out',                                               # stock painter, then an armed-only branch
    # boot.s: FastEndCb's hook only creates the background task; the task waits for every section to be initialised
    # (loaded_bits, as arm_hook) before it arms, so its waiting loop and exits are unarmed code like arm_hook's gate
    'bg_hook', 'bg_start', 'bg_task', 'bt_sec', 'bt_ready', 'bt_hls', 'bt_hls_wait', 'bt_end',
}


def main():
    build, pcs = Path(sys.argv[1]), Path(sys.argv[2])
    syms = []
    for unit in ('hsl', 'wb'):
        for line in subprocess.check_output(['mn10300-elf-nm', '-n', str(build / 'assembly' / unit / 'patch.elf')], text=True).splitlines():
            address, kind, name = line.split()[:3]
            # Assembler-local labels (.L*) mark relaxed branches inside a function, not code of their own.
            if kind in 'tT' and int(address, 16) > 0x60000000 and not name.startswith('.L'):
                syms.append((int(address, 16), name))
    syms.sort()
    addresses = [a for a, _ in syms]
    ran = {}
    forbidden = []
    for line in pcs.read_text().split('\n'):
        if line:
            pc = int(line.split()[0], 16)
            if 0x605ce800 <= pc < 0x60622000 or 0x60627000 <= pc < 0x60829800 or pc >= 0x61343800:
                forbidden.append(f'{pc:#010x} (outside the allowed sections)')
                continue
            index = bisect.bisect_right(addresses, pc) - 1
            name = syms[index][1] if index >= 0 else f'{pc:#010x}'
            ran[name] = ran.get(name, 0) + 1
    extra = sorted(set(ran) - ALLOWED) + forbidden
    if not ran and not forbidden:
        extra.append('empty trace')
    print('ran unarmed:', ', '.join(f'{k} ({v})' for k, v in sorted(ran.items())))
    print('UNARMED PCS failed: ' + ', '.join(extra) if extra else 'UNARMED PCS passed: only gates and stock replays ran')
    sys.exit(1 if extra else 0)


if __name__ == '__main__':
    main()
