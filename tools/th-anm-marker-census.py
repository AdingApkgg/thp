#!/usr/bin/env python3
"""How a title spells the ANM label marker, counted in the title's own scripts.

The interpreter's interrupt scan walks a script looking for the marker `64` (AnmInterpreter.cpp:27),
and the table for each newer title has to say which of *its* numbers that is. TH13 and TH14 answer
raw `5`; the generation answered nothing, so its own `5` fell through to TH12's canonical `5`, a
decrement-and-jump, and the first update of a dialogue script landed mid-instruction on a zero word.

This counts the three candidates per file - raw 5 with a label id, raw 7, raw 64 - so the row's
claim can be read off the titles' own data and, with TH12's own files as the control:

    th16 text.anm (74 scripts): 207 raw-5 (every one with an id),  6 raw-7,   0 raw-64
    th16 ascii.anm (20):         26 raw-5,                         8 raw-7,   0 raw-64
    th17 st05enm.anm (22):       50 raw-5,                        11 raw-7,   0 raw-64
    th12 text.anm (86):           0 raw-5,                         0 raw-7, 176 raw-64
    th12 ascii.anm (21):          0 raw-5,                         0 raw-7,  22 raw-64

Controls, run before the tool was kept: TH12's own text.anm and ascii.anm come out with zero
raw-5 and a nonzero raw-64, and the generation's come out the other way round; `length` must be a
multiple of 4 and at least 8 in every script walked, which the count relies on to read the ids.

Usage: th-anm-marker-census.py <anm-file> [more...]
"""
import os
import struct
import sys


def walk(path):
    data = open(path, 'rb').read()
    base = 0
    counts = {5: 0, 7: 0, 64: 0, 'labels': 0, 'scripts': 0}
    while base + 64 <= len(data):
        stride, = struct.unpack_from('<I', data, base + 36)
        chunk = data[base:base + (stride or (len(data) - base))]
        ns, nc = struct.unpack_from('<HH', chunk, 4)
        for i in range(nc):
            entry = 64 + ns * 4 + i * 8
            if entry + 8 > len(chunk):
                continue
            off, = struct.unpack_from('<I', chunk, entry + 4)
            cursor = off
            counts['scripts'] += 1
            while cursor + 8 <= len(chunk):
                opcode, length = struct.unpack_from('<hH', chunk, cursor)
                if opcode == -1 or length < 8:
                    break
                if opcode in counts:
                    counts[opcode] += 1
                    values = struct.unpack_from('<%di' % ((length - 8) // 4), chunk, cursor + 8)
                    if opcode == 5 and values:
                        counts['labels'] += 1
                cursor += length
        if not stride:
            break
        base += stride
    return counts


def main(paths):
    for path in paths:
        if not os.path.exists(path):
            continue
        c = walk(path)
        print('  %-34s %3d scripts, %4d raw-5 (%4d with an id), %4d raw-7, %4d raw-64' %
              (os.path.basename(path), c['scripts'], c[5], c['labels'], c[7], c[64]))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
