#!/usr/bin/env python3
"""Olympus / OM 'OE' update containers: split an update file into its components and put it back.

Written for this project from the format as Caduceus's decoder states it (cakelesscoder/caduceus-ep7 and
androidfanman/caduceus-om3 firmware/oe_container.py, Apache-2.0):

  component = 32-byte header | scrambled payload (length from the header, a multiple of 16) | 32-byte trailer
  header:  'OE', 2 model bytes, ..., u32 address at +8, u32 payload length at +12, u16 version at +16,
           u16 kind at +20, 4 zero bytes at +28
  trailer: the header's first 28 bytes again, then a u32 that makes the sum of every little-endian u32 word of
           header + decoded payload + trailer zero (mod 2^32)
  payload: in each 16-byte group, decoded[i] = stored[PERM[i]] ^ 0xff

Nothing here knows whether a payload is safe to run on a camera.
"""
from dataclasses import dataclass
import hashlib
import struct

PERM = (1, 3, 0, 2, 6, 4, 7, 5, 11, 10, 9, 8, 13, 14, 12, 15)
INV = tuple(PERM.index(i) for i in range(16))
_FLIP = bytes(b ^ 0xFF for b in range(256))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _permute(data, order):
    if len(data) % 16:
        raise ValueError('payload length must be a multiple of 16')
    view = memoryview(bytes(data))
    out = bytearray(len(data))
    for i, src in enumerate(order):
        out[i::16] = view[src::16]
    return out


def decode(data):
    return bytes(_permute(data, PERM).translate(_FLIP))


def encode(data):
    return bytes(_permute(bytes(data).translate(_FLIP), INV))


def sum32(data):
    if len(data) % 4:
        raise ValueError('length must be a multiple of 4')
    return sum(v[0] for v in struct.iter_unpack('<I', data)) & 0xFFFFFFFF


@dataclass(frozen=True)
class Block:
    index: int
    offset: int
    header: bytes
    payload: bytes      # decoded
    trailer: bytes

    @property
    def address(self):
        return struct.unpack_from('<I', self.header, 8)[0]

    @property
    def kind(self):
        return struct.unpack_from('<H', self.header, 20)[0]


def parse(data):
    """Every component of an update file, payloads decoded and checksums checked."""
    blocks, offset = [], 0
    if not data:
        raise ValueError('empty file')
    while offset < len(data):
        header = data[offset:offset + 32]
        if len(header) < 32 or header[:2] != b'OE':
            raise ValueError(f'no OE component at {offset:#x}')
        size = struct.unpack_from('<I', header, 12)[0]
        end = offset + 64 + size
        if not size or size % 16 or end > len(data):
            raise ValueError(f'bad component length at {offset:#x}')
        trailer = data[end - 32:end]
        if trailer[:28] != header[:28] or header[28:32] != bytes(4):
            raise ValueError(f'header and trailer disagree at {offset:#x}')
        if blocks and header[2:4] != blocks[0].header[2:4]:
            raise ValueError(f'another model at {offset:#x}')
        payload = decode(data[offset + 32:end - 32])
        if (sum32(header) + sum32(payload) + sum32(trailer)) & 0xFFFFFFFF:
            raise ValueError(f'checksum wrong at {offset:#x}')
        blocks.append(Block(len(blocks), offset, bytes(header), payload, bytes(trailer)))
        offset = end
    return blocks


def reconstruct(blocks):
    return b''.join(b.header + encode(b.payload) + b.trailer for b in blocks)


def replace_payload(block, payload):
    """The same component with another decoded payload of the same length; the checksum word is made again."""
    if len(payload) != len(block.payload):
        raise ValueError('a replacement payload keeps the component length')
    trailer = bytearray(block.trailer[:28] + bytes(4))
    check = -(sum32(block.header) + sum32(payload) + sum32(bytes(trailer))) & 0xFFFFFFFF
    struct.pack_into('<I', trailer, 28, check)
    return Block(block.index, block.offset, block.header, bytes(payload), bytes(trailer))


if __name__ == '__main__':
    import sys
    for b in parse(open(sys.argv[1], 'rb').read()):
        print(f'{b.index}: kind {b.kind:#06x} address {b.address:#010x} {len(b.payload)} bytes {sha256(b.payload)}')
