"""Compose E148 OSD artwork from the user's stock resource bitmaps."""

import struct


def unpack_bitmap(data, start):
    """Read a type-14 bitmap body (format 11, five 12-bit runs per 64-bit word)."""
    header = data[start:start + 4]
    if len(header) != 4 or header[3] != 11:
        raise ValueError('Expected a format-11 OSD bitmap')
    width = ((header[1] >> 4) | (header[2] << 4)) + 1
    height = (header[0] | ((header[1] & 15) << 8)) + 1
    if width > 128 or height > 60:
        raise ValueError('Icon source exceeds 128 x 60')
    pixels = bytearray()
    for start in range(start + 4, len(data), 8):
        word = int.from_bytes(data[start:start + 8], 'little')
        for shift in range(0, 60, 12):
            token = (word >> shift) & 4095
            run = (token & 15) + 1
            if len(pixels) % width + run > width:
                raise ValueError('Bitmap run crosses a row')
            pixels.extend(bytes([token >> 4]) * run)
            if len(pixels) == width * height:
                return [pixels[y:y + width] for y in range(0, len(pixels), width)]
    raise ValueError('Truncated OSD bitmap')


def pack_bitmap(rows):
    width, height = len(rows[0]), len(rows)
    if any(len(row) != width for row in rows):
        raise ValueError('Inconsistent bitmap width')
    encoded = bytearray([height - 1, ((width - 1) & 15) << 4, (width - 1) >> 4, 11])
    tokens = []
    for row in rows:
        x = 0
        while x < width:
            value, run = row[x], 1
            while run < 16 and x + run < width and row[x + run] == value:
                run += 1
            tokens.append((value << 4) | (run - 1))
            x += run
    for i in range(0, len(tokens), 5):
        group = tokens[i:i + 5]
        word = sum(token << (12 * j) for j, token in enumerate(group))
        encoded.extend(word.to_bytes(8 if len(group) == 5 else (12 * len(group) + 7) // 8, 'little'))
    if unpack_bitmap(encoded, 0) != rows:
        raise ValueError('Bitmap round trip failed')
    return encoded


def append_icons(atlas, load, sprites, source_rows):
    """Add type-14 records whose normal and alternate draws use the same artwork."""
    pointers = {}
    for sprite in sprites:
        strips = []
        for strip in sprite['strips']:
            rows = source_rows(int(strip['source'], 16))
            if 'crop' in strip:
                x0, y0, x1, y1 = strip['crop']
                if not (0 <= x0 < x1 <= len(rows[0]) and 0 <= y0 < y1 <= len(rows)):
                    raise ValueError('Icon crop leaves source')
                rows = [row[x0:x1] for row in rows[y0:y1]]
            if 'width' in strip:
                width = strip['width']
                old_width = len(rows[0])
                if not 1 <= width <= old_width:
                    raise ValueError('Invalid narrower glyph width')
                columns = [(2 * x + 1) * old_width // (2 * width) for x in range(width)]
                rows = [bytes(row[x] for x in columns) for row in rows]
            pad = bytes(strip.get('pad_left', 0))
            strips.append([pad + row for row in rows])
        if len({len(rows) for rows in strips}) != 1:
            raise ValueError('Bitmap strips must have equal heights')
        rows = [bytearray().join(parts) for parts in zip(*strips)]
        pixels = pack_bitmap(rows)
        atlas.extend(bytes(-len(atlas) % 4))
        pointer = load + len(atlas)
        atlas.extend(struct.pack('<6H3I', 14, len(rows[0]), len(rows), 8, 0, 0,
                                 len(pixels), pointer + 24, 0))
        atlas.extend(pixels)
        for image_id in sprite['ids']:
            image_id = int(image_id, 16)
            if image_id in pointers:
                raise ValueError(f'Duplicate custom bitmap ID {image_id:#x}')
            pointers[image_id] = pointer
    return pointers
