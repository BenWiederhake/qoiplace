#!/usr/bin/env python3

import inspect
import os
import sys

import multi

# Hacky way to use existing "myqoi" implementation:
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import myqoi

VERBOSE = True
XSTART = 30
YSTART = 250
COLOR = (124, 74, 136)  # Randomly chosen


def cmds_to_make(qoidata, index, value):
    if qoidata[index] != value:
        qoidata[index] = value
        return [f"{index} {value}"]
    return []


def determine_commands(qoifile_path):
    with open(qoifile_path, "rb") as fp:
        qoidata_with_header = bytearray(fp.read())
    qoidata = qoidata_with_header[14 : -8]
    assert len(qoidata) == 512 * 512 * 4, len(qoidata)
    write_commands = []
    for i in range(10):
        current_indices = myqoi.decode_to_indices(qoidata, 512, 512)
        offset = (XSTART - i) + 512 * (YSTART + i)
        assert 0 <= offset < 512 * 512
        index_start = current_indices[offset]
        print(f"before: {qoidata[index_start : index_start + 5]}")
        write_commands.extend(cmds_to_make(qoidata, index_start, 0xFE))
        write_commands.extend(cmds_to_make(qoidata, index_start + 1, COLOR[0]))
        write_commands.extend(cmds_to_make(qoidata, index_start + 2, COLOR[1]))
        write_commands.extend(cmds_to_make(qoidata, index_start + 3, COLOR[2]))
        write_commands.extend(cmds_to_make(qoidata, index_start + 4, 0x40))
        print(f"after: {qoidata[index_start : index_start + 5]}")
        # Need to re-evaluate indices, because everything afterwards might have just shifted.
    return write_commands


def run(qoifile_path):
    cmds = determine_commands(qoifile_path)
    multi.run_commands(cmds)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"USAGE: {sys.argv[0]} path/to/CURRENT.qoi", file=sys.stderr)
        exit(1)
    run(sys.argv[1])
