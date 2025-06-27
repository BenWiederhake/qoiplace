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
        self.table = [(0, 0, 0, 0)] * 64
        self.last = (0, 0, 0, 255)
        # Yes, the default alpha is different, which affects the table indices. Ugh.

    def see(self, rgba):
        self.last = rgba
        r, g, b, a = rgba
        index_position = (r * 3 + g * 5 + b * 7 + a * 11) % 64
        self.table[index_position] = rgba

    def consumebyte(self):
        if self.data_offset >= len(self.qoidata):
            return 0
        byte_value = self.qoidata[self.data_offset]
        self.data_offset += 1
        return byte_value

    def consume(self) -> Tuple[ChunkType, Tuple[int, int, int, int]]:
        if self.data_offset >= len(self.qoidata):
            return (ChunkType.NONE, (0, 0, 0, 0))
        nextbyte = self.consumebyte()
        self.px_offset += 1
        if nextbyte == 0xFE:
            rgba = (
                self.consumebyte(),
                self.consumebyte(),
                self.consumebyte(),
                self.last[3],
            )
            self.see(rgba)
            return (ChunkType.QOI_OP_RGB, rgba)
        if nextbyte == 0xFF:
            rgba = (
                self.consumebyte(),
                self.consumebyte(),
                self.consumebyte(),
                self.consumebyte(),
            )
            self.see(rgba)
            return (ChunkType.QOI_OP_RGBA, rgba)
        if (nextbyte & 0xC0) == 0x00:
            index_position = nextbyte & 0x3F
            rgba = self.table[index_position]
            self.see(rgba)
            return (ChunkType.QOI_OP_INDEX, rgba)
        if (nextbyte & 0xC0) == 0x40:
            dr = ((nextbyte >> 4) & 0b11) - 2
            dg = ((nextbyte >> 2) & 0b11) - 2
            db = ((nextbyte >> 0) & 0b11) - 2
            r, g, b, a = self.last
            rgba = (r + dr) % 256, (g + dg) % 256, (b + db) % 256, a
            self.see(rgba)
            return (ChunkType.QOI_OP_DIFF, rgba)
        if (nextbyte & 0xC0) == 0x80:
            dg = (nextbyte & 0x3F) - 32
            xy = self.consumebyte()
            dr = ((xy >> 4) & 0x0F) - 8 + dg
            db = ((xy >> 0) & 0x0F) - 8 + dg
            r, g, b, a = self.last
            rgba = (r + dr) % 256, (g + dg) % 256, (b + db) % 256, a
            self.see(rgba)
            return (ChunkType.QOI_OP_LUMA, rgba)
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
        chunk_type, rgba = qoi_eater.consume()
        rgb = rgba[:3]
        if chunk_type == ChunkType.NONE:
            break
        # If some jester fills the entire 1 MB with maximal QOI_OP_RUN-chunks, then we would end up writing 62 million pixels.
        # Limit the maximum impact of that:
        if qoi_eater.px_offset > 3 * qoi_eater.w * qoi_eater.h:
            # Yeah, we're *far* beyond anything reasonable. Just stop processing here.
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


def decode_to_indices(qoidata, w, h):
    qoi_eater = QoiEater(w, h, qoidata)
    indices = []
    while True:
        old_px_offset = qoi_eater.px_offset
        old_data_offset = qoi_eater.data_offset
        chunk_type, _ = qoi_eater.consume()
        if chunk_type == ChunkType.NONE:
            break
        # If some jester fills the entire 1 MB with maximal QOI_OP_RUN-chunks, then we would end up writing 62 million pixels.
        # Limit the maximum impact of that:
        if qoi_eater.px_offset > 3 * qoi_eater.w * qoi_eater.h:
            # Yeah, we're *far* beyond anything reasonable. Just stop processing here.
            break
        for _ in range(old_px_offset, qoi_eater.px_offset):
            indices.append(old_data_offset)
    missing = qoi_eater.w * qoi_eater.h - len(indices)
    if missing != 0:
        if VERBOSE:
            print(
                f"Expect {qoi_eater.w * qoi_eater.h} pixels, got {len(indices)} instead"
            )
            print(f"Padding with {missing} invalid indices?!?!")
        if missing > 0:
            indices.extend([-1] * missing)
        else:
            indices = indices[: qoi_eater.w * qoi_eater.h]
    assert len(indices) == qoi_eater.w * qoi_eater.h, (
        len(indices),
        qoi_eater.w,
        qoi_eater.h,
    )
    return indices


def run(qoifile, pngfile):
    with open(qoifile, "rb") as fp:
        all_qoidata = fp.read()
    qoidata = all_qoidata[14:-8]  # Skip header, skip footer
    img = decode(qoidata, 512, 512)
    img.save(pngfile, "png")
    indices = decode_to_indices(qoidata, 512, 512)
    print(indices[:50])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"USAGE: {sys.argv[0]} infile.qoi outfile.png", file=sys.stderr)
        exit(1)
    run(sys.argv[1], sys.argv[2])
