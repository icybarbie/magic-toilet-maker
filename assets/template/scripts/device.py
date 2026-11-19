#!/usr/bin/env python3
"""Read USB diagnostics or export the actual RGB565 framebuffer as a PNG."""
import argparse
import pathlib
import struct
import sys
import time
import zlib
import serial

def png_chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)

def save_png(path, width, height, data):
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            v = struct.unpack_from('<H', data, (y * width + x) * 2)[0]
            r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
            rows.extend(((r * 255 + 15)//31, (g * 255 + 31)//63, (b * 255 + 15)//31))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0)) + png_chunk(b'IDAT', zlib.compress(rows)) + png_chunk(b'IEND', b''))
