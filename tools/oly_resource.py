"""Repoint GUI image IDs to stock bitmaps or artwork derived from stock."""

import struct

from oly_compress import _sequences, _repack, _encode, length_fault
from oly_ui_bitmap import append_icons, unpack_bitmap


def _recipe(target, rows, recipe):
    """Encode `target` with the stock sequences outside one window and the given (literal length, offset, match
    length) sequences inside it. The window is given by output offsets that are stock sequence boundaries."""
    lo, hi = int(recipe['from'], 16), int(recipe['to'], 16)
    begin = lambda r: r[3] - len(r[0])
    head = [r for r in rows if r[3] + r[2] <= lo]
    tail = [r for r in rows if begin(r) >= hi]
    if (not head or head[-1][3] + head[-1][2] != lo
            or (begin(tail[0]) if tail else len(target)) != hi):
        raise ValueError('Resource recipe window is not on stock sequence boundaries')
    packed, at = bytearray(), 0
    for lits, off, n, start in head:
        packed.extend(_encode(target[at:start], off, n))
        at = start + n
    sequences = (struct.iter_unpack('<3H', bytes.fromhex(recipe['sequences_le16']))
                 if 'sequences_le16' in recipe else recipe['sequences'])
    for lit, off, n in sequences:
        packed.extend(_encode(target[at:at + lit], off, n))
        at += lit + n
    if at != hi:
        raise ValueError('Resource recipe does not fill its window')
    for lits, off, n, start in tail:
        packed.extend(_encode(target[at:start], off, n))
        at = start + n
    if _sequences(bytes(packed), len(target))[0] != target:
        raise ValueError('Resource recipe does not decode to the aliased record')
    return bytes(packed)


def alias_images(payload, aliases, recipe=None, artwork=None):
    """Return a same-size 0x101 payload with selected image IDs replaced.

    recipe (optional): the LZ4 sequences of the changed part of the record, so the stored bytes equal a stream
    that has started on a camera (the 8 November 2026 build's resource block). The packed length is checked
    against the loader's length rule either way."""
    if len(payload) < 2048 or len(payload) % 16:
        raise ValueError('Invalid resource component size')
    first, span, z1, z2 = struct.unpack_from('<4I', payload)
    if z1 or z2:
        raise ValueError('Invalid resource index')
    origin = first - 2016
    at = first - origin
    if at != 2016 or at + span > len(payload):
        raise ValueError('Resource record leaves component')
    original = payload[at:at + span]
    if original[:16] != b'olycompress' + b' ' * 5 or original[24:32] != bytes(8):
        raise ValueError('Expected compressed resource record 0')
    packed, raw = struct.unpack_from('<II', original, 16)
    if packed + 32 > span:
        raise ValueError('Compressed resource exceeds record span')
    decoded, _ = _sequences(original[32:32 + packed], raw)
    data = bytearray(decoded)
    load = struct.unpack_from('<I', data)[0] - 8
    table = struct.unpack_from('<I', data, 4)[0] - load
    if not 0 <= table < len(data):
        raise ValueError('Resource image table is outside record')
    source = bytes(data)
    placeholder = load + table - 20
    replacements = {}
    for target_id, source_id in aliases:
        src = table + 4 * source_id
        if src < table or src + 4 > len(data):
            raise ValueError('Source image ID leaves pointer table')
        replacements[target_id] = struct.unpack_from('<I', source, src)[0]
    if len(aliases) != len(replacements):
        raise ValueError('Duplicate resource alias')
    result = bytearray(payload)
    if artwork:
        icons = _append_artwork(result, origin, source, load, table, artwork)
        if replacements.keys() & icons.keys():
            raise ValueError('Resource alias and artwork share an image ID')
        replacements.update(icons)
    for target_id, replacement in replacements.items():
        dst = table + 4 * target_id
        if dst < table or dst + 4 > len(data):
            raise ValueError('Image ID leaves pointer table')
        current = struct.unpack_from('<I', source, dst)[0]
        if current != placeholder or replacement == placeholder:
            raise ValueError(f'Invalid resource replacement for {target_id:#x}')
        struct.pack_into('<I', data, dst, replacement)

    # Re-encode with the stock stream's own sequences (oly_compress): matches whose bytes are unchanged are kept,
    # the changed pointer words become short literal runs. Pure Python and deterministic, so the user-facing
    # patcher needs no LZ4 library and every machine makes the same bytes.
    _, rows = _sequences(original[32:32 + packed], raw)
    encoded = _recipe(bytes(data), rows, recipe) if recipe else _repack(decoded, bytes(data), rows, split=True)
    size = len(encoded)
    if recipe and length_fault(size):
        raise ValueError(f'Resource record: {length_fault(size)}')
    if size + 32 > span:
        raise ValueError(f'Repacked resource exceeds its {span} byte span')
    result[at:at + span] = bytes([255]) * span
    result[at:at + 16] = original[:16]
    struct.pack_into('<II', result, at + 16, size, raw)
    result[at + 24:at + 32] = bytes(8)
    result[at + 32:at + 32 + size] = encoded
    return bytes(result)


def _append_artwork(result, origin, image_table, table_load, table, artwork):
    """Extend E148's final bitmap record into the component's zero-filled tail."""
    index = 37
    address, span, z1, z2 = struct.unpack_from('<4I', result, index * 16)
    at = address - origin
    if z1 or z2 or any(result[(index + 1) * 16:2016]):
        raise ValueError('Expected the E148 bitmap record last in the resource index')
    if at < 2016 or at + span > len(result) or result[at:at + 16] != b'olycompress     ':
        raise ValueError('Invalid E148 bitmap record')
    packed, raw = struct.unpack_from('<II', result, at + 16)
    if packed + 32 > span or result[at + 24:at + 32] != bytes(8):
        raise ValueError('Invalid E148 bitmap stream header')
    decoded, sequences = _sequences(result[at + 32:at + 32 + packed], raw)
    atlas = bytearray(decoded)
    load = 0xa3791000

    def source_rows(image_id):
        ptr, = struct.unpack_from('<I', image_table, table + 4 * image_id)
        blob, offset = (decoded, ptr - load) if ptr >= load else (image_table, ptr - table_load)
        if not 0 <= offset <= len(blob) - 28 or blob[offset:offset + 2] != b'\x0e\x00':
            raise ValueError(f'Invalid stock bitmap {image_id:#x}')
        return unpack_bitmap(blob, offset + 24)

    icons = append_icons(atlas, load, artwork['sprites'], source_rows)
    if load + len(atlas) > ((load + raw + 65535) & ~65535):
        raise ValueError('Artwork crosses the final stock bitmap memory page')
    encoded = _recipe(atlas, sequences, artwork['lz4_recipe'])
    size = len(encoded)
    if length_fault(size):
        raise ValueError(f'Bitmap record: {length_fault(size)}')
    new_span = max(span, (size + 32 + 511) & ~511)
    if at + new_span > len(result) or any(result[at + span:at + new_span]):
        raise ValueError('Bitmap record exceeds zero-filled tail')
    struct.pack_into('<I', result, index * 16 + 4, new_span)
    struct.pack_into('<II', result, at + 16, size, len(atlas))
    result[at + 32:at + new_span] = encoded + b'\xff' * (new_span - 32 - size)
    return icons
