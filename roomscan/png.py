"""Small, dependency-free reader for the grayscale PNGs in the supplied data."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GrayImage:
    width: int
    height: int
    bit_depth: int
    pixels: bytes

    def at(self, x: int, y: int) -> int:
        offset = y * self.width * (self.bit_depth // 8) + x * (self.bit_depth // 8)
        if self.bit_depth == 8:
            return self.pixels[offset]
        return int.from_bytes(self.pixels[offset : offset + 2], "big")


def read_gray_png(path: Path) -> GrayImage:
    """Decode non-interlaced grayscale PNGs (8-bit confidence or 16-bit depth)."""
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Not a PNG file: {path}")

    offset = 8
    compressed = bytearray()
    width = height = bit_depth = color_type = interlace = None
    while offset + 12 <= len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4 : offset + 8]
        start = offset + 8
        chunk = data[start : start + length]
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break
        offset = start + length + 4

    if not width or not height or color_type != 0 or bit_depth not in (8, 16):
        raise ValueError(f"Unsupported PNG layout in {path}")
    if interlace != 0:
        raise ValueError(f"Interlaced PNG is not supported: {path}")

    bytes_per_pixel = bit_depth // 8
    row_bytes = width * bytes_per_pixel
    raw = zlib.decompress(compressed)
    expected = height * (row_bytes + 1)
    if len(raw) != expected:
        raise ValueError(f"Unexpected decompressed PNG size in {path}: {len(raw)} != {expected}")

    pixels = bytearray(height * row_bytes)
    previous = bytearray(row_bytes)
    cursor = 0
    for y in range(height):
        filter_type = raw[cursor]
        cursor += 1
        source = raw[cursor : cursor + row_bytes]
        cursor += row_bytes
        row = bytearray(row_bytes)
        if filter_type == 0:
            row[:] = source
        else:
            for x, value in enumerate(source):
                left = row[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
                above = previous[x]
                upper_left = previous[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
                if filter_type == 1:
                    predictor = left
                elif filter_type == 2:
                    predictor = above
                elif filter_type == 3:
                    predictor = (left + above) // 2
                elif filter_type == 4:
                    p = left + above - upper_left
                    pa, pb, pc = abs(p - left), abs(p - above), abs(p - upper_left)
                    predictor = left if pa <= pb and pa <= pc else above if pb <= pc else upper_left
                else:
                    raise ValueError(f"Unknown PNG filter {filter_type} in {path}")
                row[x] = (value + predictor) & 0xFF
        begin = y * row_bytes
        pixels[begin : begin + row_bytes] = row
        previous = row

    return GrayImage(width, height, bit_depth, bytes(pixels))
