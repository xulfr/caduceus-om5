"""Repoint existing GUI image IDs inside a bounded resource record.

Only pointer-table words change in the expanded record. No image artwork is
included in the patch: every replacement points to another stock resource.
"""

import struct

from oly_compress import _sequences, _repack


def alias_images(payload, aliases):
    """Return a same-size 0x101 payload with selected IDs aliased to stock IDs."""
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
    encoded = _repack(decoded, bytes(data), rows, split=True)
    size = len(encoded)
    if size + 32 > span:
        raise ValueError(f'Repacked resource exceeds its {span} byte span')
    result = bytearray(payload)
    result[at:at + span] = bytes([255]) * span
    result[at:at + 16] = original[:16]
    struct.pack_into('<II', result, at + 16, size, raw)
    result[at + 24:at + 32] = bytes(8)
    result[at + 32:at + 32 + size] = encoded
    return bytes(result)
