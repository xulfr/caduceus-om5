"""Lossless expansion and bounded LZ4 repacking of main-block olycompress spans."""
import struct

MAGIC = b'olycompress' + b' ' * 5


def _length(data, pos, value):
    if value != 15:
        return value, pos
    while True:
        if pos >= len(data):
            raise ValueError('Truncated LZ4 length')
        n = data[pos]
        pos += 1
        value += n
        if n != 255:
            return value, pos


def _sequences(data, raw_size):
    """Yield (decoded literals, offset, match length, output match start)."""
    pos = 0
    out = bytearray()
    rows = []
    while pos < len(data):
        token = data[pos]
        pos += 1
        lit_len, pos = _length(data, pos, token >> 4)
        if pos + lit_len > len(data):
            raise ValueError('Truncated LZ4 literals')
        literals = bytes(data[pos:pos + lit_len])
        pos += lit_len
        out.extend(literals)
        start = len(out)
        if pos == len(data):
            rows.append((literals, 0, 0, start))
            break
        if pos + 2 > len(data):
            raise ValueError('Truncated LZ4 offset')
        offset = int.from_bytes(data[pos:pos + 2], 'little')
        pos += 2
        if not 0 < offset <= len(out):
            raise ValueError('Invalid LZ4 offset')
        match_len, pos = _length(data, pos, token & 15)
        match_len += 4
        for _ in range(match_len):
            out.append(out[-offset])
        rows.append((literals, offset, match_len, start))
    if len(out) != raw_size:
        raise ValueError(f'LZ4 raw length {len(out)} != {raw_size}')
    return bytes(out), rows


def _extra(value):
    if value < 15:
        return b''
    value -= 15
    return b'\xff' * (value // 255) + bytes([value % 255])


def _encode(literals, offset=0, match_len=0):
    result = bytearray([min(len(literals), 15) << 4 | (min(match_len - 4, 15) if offset else 0)])
    result.extend(_extra(len(literals)))
    result.extend(literals)
    if offset:
        result.extend(offset.to_bytes(2, 'little'))
        result.extend(_extra(match_len - 4))
    return result


def _split_window(target, start, length, offset, raw):
    """Encode target[start:start + length] (a stock match whose source no longer
    matches) as [(literals, offset, match_len)] using the stock offset where the
    bytes still agree and offset-1 runs elsewhere, so the patched stream keeps
    short literal runs. Matches stay at least 12 bytes before the end of the
    span and end at least 5 bytes before it (LZ4 block rules)."""
    out, lits, i, end = [], bytearray(), start, start + length
    while i < end:
        best = None
        for off in (offset, 1):
            if not 0 < off <= i:
                continue
            n = 0
            while i + n < end and target[i + n] == target[i + n - off]:
                n += 1
            if n >= 16 and (best is None or n > best[1]):
                best = (off, n)
        if best and i <= raw - 12:
            off, n = best
            n = min(n, raw - 5 - i)
            if n >= 4:
                out.append((bytes(lits), off, n))
                lits.clear()
                i += n
                continue
        lits.append(target[i])
        i += 1
    return out, bytes(lits)


def _repack(original, target, rows, split=False):
    pending = bytearray()
    packed = bytearray()
    at = 0
    raw = len(target)
    for literals, offset, match_len, start in rows:
        pending.extend(target[at:start])
        at = start
        if offset:
            # Keep a match only if replaying it from the already patched output
            # gives precisely the requested bytes, including overlapping copies.
            if target[start:start + match_len] == target[start - offset:start - offset + match_len]:
                packed.extend(_encode(pending, offset, match_len))
                pending.clear()
            elif split:
                parts, rest = _split_window(target, start, match_len, offset, raw)
                for lits, off, n in parts:
                    pending.extend(lits)
                    packed.extend(_encode(pending, off, n))
                    pending.clear()
                pending.extend(rest)
            else:
                pending.extend(target[start:start + match_len])
            at += match_len
    packed.extend(_encode(pending))
    decoded, _ = _sequences(packed, len(target))
    if decoded != target:
        raise ValueError('Repacked LZ4 does not match expanded target')
    return bytes(packed)


# ---- Stream length rule (E148 1.1; found after the alpha5 boot loop, research/OM5II-STREAM-LENGTH-2026-11-15.md)
# The loader (0x6005b249) reads a compressed section from flash in 2 KiB blocks: (L // 2048 + 1) * 2048 bytes
# for a packed length L, although the stream is 32 + L bytes long. A stream with L % 2048 > 2016 therefore loses
# its last bytes (proven from the code). The stream is then decoded by the other processor, whose code is not in
# the main program; alpha5's section 7 was exactly 611 * 4096 bytes and that build never started. So a re-encoded
# stream must end at the same place inside a 4 KiB page as OM's own stream does: L == stock L (mod 4096).
BLOCK, PAGE, HEADER, GUARD = 2048, 4096, 32, 64


def length_fault(packed):
    """Why a packed length is refused, or None."""
    if packed % BLOCK > BLOCK - HEADER:
        return f'packed length {packed}: the loader would not read its last {packed % BLOCK - (BLOCK - HEADER)} bytes'
    if packed % PAGE < GUARD:
        return f'packed length {packed} ends {packed % PAGE} bytes into a 4 KiB page (the alpha5 boot-loop case is 0)'
    size = BLOCK
    while size <= 1 << 24:          # 32 + L must not straddle the end of any power-of-two unit a reader may use
        if packed % size > size - HEADER - GUARD:
            return f'packed length {packed} ends {size - packed % size} bytes before a {size} byte boundary'
        size *= 2
    return None


def _pad(data, raw, stock_packed, literal_limit):
    """Re-encode a valid block so its length equals stock_packed modulo 4096, without changing what it decodes
    to. Two length-neutral LZ4 rewrites, both of kinds the stock streams are full of:
      +3 bytes: one match of 8..18 bytes becomes two matches with the same offset (4 bytes, then the rest);
      +1 byte:  a 4-byte match between two short literal runs becomes literals.
    The last 64 KiB of output is left as it is (LZ4 end-of-block rules, and the patch code sits there)."""
    need = (stock_packed - len(data)) % PAGE
    while length_fault(len(data) + need):
        need += PAGE
    if not need:
        return data
    decoded, rows = _sequences(data, raw)
    ones, threes = need % 3, need // 3
    out, i, limit = [], 0, raw - 65536
    while i < len(rows):
        lits, off, n, start = rows[i]
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        if off and start + n < limit:
            if ones and n == 4 and nxt and nxt[1] and len(lits) + 4 + len(nxt[0]) <= 14 and nxt[3] + nxt[2] < limit:
                merged = lits + decoded[start:start + 4] + nxt[0]
                out.append((merged, nxt[1], nxt[2], nxt[3]))
                ones -= 1
                i += 2
                continue
            if threes and 8 <= n <= 18 and len(lits) < 15:
                out.append((lits, off, 4, start))
                out.append((b'', off, n - 4, start + 4))
                threes -= 1
                i += 1
                continue
        out.append(rows[i])
        i += 1
    if ones or threes:
        raise ValueError('No room to adjust the packed length')
    packed = bytearray()
    for lits, off, n, _ in out:
        packed.extend(_encode(lits, off, n))
    packed = bytes(packed)
    if _sequences(packed, raw)[0] != decoded or len(packed) % PAGE != stock_packed % PAGE:
        raise ValueError('Length adjustment changed the expanded data')
    return packed


def stream_lengths(stored):
    """(offset, packed length) of every olycompress stream in a stored component, whatever holds it."""
    out, p = [], 0
    while (p := stored.find(MAGIC, p)) >= 0:
        out.append((p, struct.unpack_from('<I', stored, p + 16)[0]))
        p += 32
    return out


def max_literal_run(data, raw):
    """Longest literal run of an LZ4 block (for comparison with the stock stream)."""
    _, rows = _sequences(data, raw)
    return max(len(r[0]) for r in rows)


def spans(stored):
    p = 0
    result = []
    while (p := stored.find(MAGIC, p)) >= 0:
        if p + 32 > len(stored):
            raise ValueError('Truncated olycompress header')
        packed, raw = struct.unpack_from('<II', stored, p + 16)
        if stored[p + 24:p + 32] != bytes(8) or p + 32 + packed > len(stored) or p + raw > len(stored):
            raise ValueError('Invalid olycompress span')
        result.append((p, packed, raw))
        p += raw
    return result


def expand_image(stored):
    result = bytearray(stored)
    for p, packed, raw in spans(stored):
        data, _ = _sequences(stored[p + 32:p + 32 + packed], raw)
        result[p:p + raw] = data
    return bytes(result)


def repack_image(stored, target, split=False, literal_limit=None, stream_length=None):
    """stream_length 'stock-page': every re-encoded stream keeps OM's packed length modulo 4096 and must pass
    length_fault(). None reproduces the releases up to alpha5 (blocked: alpha5 failed on a camera)."""
    if stream_length not in (None, 'stock-page'):
        raise ValueError(f'Unknown stream_length rule {stream_length!r}')
    if len(stored) != len(target):
        raise ValueError('Expanded image size changed')
    original = expand_image(stored)
    result = bytearray(stored)
    ranges = spans(stored)
    for p, packed, raw in ranges:
        if original[p:p + raw] == target[p:p + raw]:
            continue
        _, rows = _sequences(stored[p + 32:p + 32 + packed], raw)
        data = _repack(original[p:p + raw], target[p:p + raw], rows, split)
        if stream_length:
            data = _pad(data, raw, packed, literal_limit)
            if length_fault(len(data)) or length_fault(packed):
                raise ValueError(f'olycompress at {p:#x}: {length_fault(len(data)) or length_fault(packed)}')
        if literal_limit is not None:
            stock_max = max(len(r[0]) for r in rows)
            if max_literal_run(data, raw) > max(stock_max, literal_limit):
                raise ValueError(f'olycompress at {p:#x}: literal run {max_literal_run(data, raw)} exceeds '
                                 f'the stock maximum {stock_max}')
        if len(data) + 32 > raw:
            raise ValueError(f'olycompress at {p:#x} exceeds its {raw} byte span')
        result[p:p + raw] = bytes([255]) * raw
        result[p:p + 16] = MAGIC
        struct.pack_into('<II', result, p + 16, len(data), raw)
        result[p + 24:p + 32] = bytes(8)
        result[p + 32:p + 32 + len(data)] = data
    end = 0
    for p, _, raw in ranges:
        result[end:p] = target[end:p]
        end = p + raw
    result[end:] = target[end:]
    if expand_image(result) != target:
        raise ValueError('Repacked image round trip failed')
    return bytes(result)
