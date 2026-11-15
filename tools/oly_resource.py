"""Repoint existing GUI image IDs inside a bounded resource record.

Only pointer-table words change in the expanded record. No image artwork is
included in the patch: every replacement points to another stock resource.
"""

import struct

from oly_compress import _sequences, _repack, _encode, length_fault


def _recipe(target, rows, recipe):
    """Encode `target` with the stock sequences outside one window and the given (literal length, offset, match
    length) sequences inside it. The window is given by output offsets that are stock sequence boundaries."""
    lo, hi = int(recipe['from'], 16), int(recipe['to'], 16)
    begin = lambda r: r[3] - len(r[0])
    head = [r for r in rows if r[3] + r[2] <= lo]
    tail = [r for r in rows if begin(r) >= hi]
    if not head or not tail or head[-1][3] + head[-1][2] != lo or begin(tail[0]) != hi:
        raise ValueError('Resource recipe window is not on stock sequence boundaries')
    packed, at = bytearray(), 0
    for lits, off, n, start in head:
        packed.extend(_encode(target[at:start], off, n))
        at = start + n
    for lit, off, n in recipe['sequences']:
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


def alias_images(payload, aliases, recipe=None):
    """Return a same-size 0x101 payload with selected IDs aliased to stock IDs.

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
    seen = set()
    for target_id, source_id in aliases:
        if target_id in seen:
            raise ValueError(f'Duplicate resource image ID {target_id:#x}')
        seen.add(target_id)
        dst = table + 4 * target_id
        src = table + 4 * source_id
        if min(dst, src) < 0 or max(dst, src) + 4 > len(data):
            raise ValueError('Image ID leaves pointer table')
        replacement = struct.unpack_from('<I', source, src)[0]
        current = struct.unpack_from('<I', source, dst)[0]
        if current != placeholder or replacement == placeholder:
            raise ValueError(f'Invalid resource alias {target_id:#x} -> {source_id:#x}')
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
    result = bytearray(payload)
    result[at:at + span] = bytes([255]) * span
    result[at:at + 16] = original[:16]
    struct.pack_into('<II', result, at + 16, size, raw)
    result[at + 24:at + 32] = bytes(8)
    result[at + 32:at + 32 + size] = encoded
    return bytes(result)
