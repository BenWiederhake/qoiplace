#!/bin/false
# This is a library.

from enum import Enum
from PIL import Image
from typing import Tuple
import sys


class ChunkType(Enum):
    QOI_OP_RGB = 1
    QOI_OP_RGBA = 2
    QOI_OP_INDEX = 3
    QOI_OP_DIFF = 4
    QOI_OP_LUMA = 5
    QOI_OP_RUN = 6
    NONE = 7


VERBOSE = False
COL_QOI_OP_RGB = (255, 0, 0)
COL_QOI_OP_RGBA = (255, 0, 128)
COL_QOI_OP_INDEX = (0, 255, 0)
COL_QOI_OP_DIFF = (0, 255, 255)
COL_QOI_OP_LUMA = (255, 128, 0)


class QoiEater:
    def __init__(self, w, h, qoidata):
        self.qoidata = qoidata
        self.w = w
        self.h = h
        self.data_offset = 0
        self.px_offset = 0
        self.table = [(0, 0, 0)] * 64
        self.last = (0, 0, 0)

    def see(self, rgb):
        self.last = rgb
        r, g, b = rgb
        index_position = (r * 3 + g * 5 + b * 7 + 255 * 11) % 64
        self.table[index_position] = rgb

    def consumebyte(self):
        if self.data_offset >= len(self.qoidata):
            return 0
        byte_value = self.qoidata[self.data_offset]
        self.data_offset += 1
        return byte_value

    def consume(self) -> (ChunkType, Tuple[int, int, int]):
        if self.data_offset >= len(self.qoidata):
            return (ChunkType.NONE, (0, 0, 0))
        nextbyte = self.consumebyte()
        self.px_offset += 1
        if nextbyte == 0xFE:
            rgb = (self.consumebyte(), self.consumebyte(), self.consumebyte())
            self.see(rgb)
            return (ChunkType.QOI_OP_RGB, rgb)
        if nextbyte == 0xFF:
            rgb = (self.consumebyte(), self.consumebyte(), self.consumebyte())
            self.consumebyte() # Ignore alpha
            self.see(rgb)
            return (ChunkType.QOI_OP_RGBA, rgb)
        if (nextbyte & 0xC0) == 0x00:
            index_position = nextbyte & 0x3F
            rgb = self.table[index_position]
            self.see(rgb)
            return (ChunkType.QOI_OP_INDEX, rgb)
        if (nextbyte & 0xC0) == 0x40:
            dr = ((nextbyte >> 4) & 0b11) - 2
            dg = ((nextbyte >> 2) & 0b11) - 2
            db = ((nextbyte >> 0) & 0b11) - 2
            r, g, b = self.last
            rgb = (r + dr) % 256, (g + dg) % 256, (b + db) % 256
            self.see(rgb)
            return (ChunkType.QOI_OP_DIFF, rgb)
        if (nextbyte & 0xC0) == 0x80:
            dg = (nextbyte & 0x3F) - 32
            xy = self.consumebyte()
            dr = ((xy >> 4) & 0x0F) - 8 + dg
            db = ((xy >> 0) & 0x0F) - 8 + dg
            r, g, b = self.last
            rgb = (r + dr) % 256, (g + dg) % 256, (b + db) % 256
            self.see(rgb)
            return (ChunkType.QOI_OP_LUMA, rgb)
        if (nextbyte & 0xC0) == 0xC0:
            # Bias of one is already included!
            self.px_offset += nextbyte & 0x3F
            return (ChunkType.QOI_OP_RUN, self.last)
        raise AssertionError("unreachable?")


def decode(qoidata, w, h):
    qoi_eater = QoiEater(w, h, qoidata)
    img = Image.new("RGB", (qoi_eater.w, qoi_eater.h))
    data = []
    while True:
        old_px_offset = qoi_eater.px_offset
        chunk_type, rgb = qoi_eater.consume()
        if chunk_type == ChunkType.NONE:
            break
        for _ in range(old_px_offset, qoi_eater.px_offset):
            data.append(rgb)
    missing = qoi_eater.w * qoi_eater.h - len(data)
    if missing != 0:
        if VERBOSE:
            print(f"Expect {qoi_eater.w * qoi_eater.h} pixels, got {len(data)} instead")
            print(f"Padding with {missing} purple pixels?!?!")
        if missing > 0:
            data.extend([(128, 0, 128)] * missing)
        else:
            data = data[: qoi_eater.w * qoi_eater.h]
    assert len(data) == qoi_eater.w * qoi_eater.h, (len(data), qoi_eater.w, qoi_eater.h)
    img.putdata(data)
    return img


def run(qoifile, pngfile):
    with open(qoifile, "rb") as fp:
        all_qoidata = fp.read()
    qoidata = all_qoidata[14 : -8]  # Skip header, skip footer
    img = decode(qoidata, 512, 512)
    img.save(pngfile, "png")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"USAGE: {sys.argv[0]} infile.qoi outfile.png", file=sys.stderr)
        exit(1)
    run(sys.argv[1], sys.argv[2])
