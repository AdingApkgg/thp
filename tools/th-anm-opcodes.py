#!/usr/bin/env python3
"""Histogram the ANM opcodes a title's shipped ANM files actually use.

An ANM opcode number is metadata the interpreter dispatches on, so the multiset a title's own
files use is the first thing to measure when a port's interpreter is written against one title.
"""
import struct
import sys
import collections
import glob
import os


def chunks(data):
    base = 0
    while True:
        if len(data) - base < 64:
            return
        stride, = struct.unpack_from('<I', data, base + 36)
        size = stride or (len(data) - base)
        yield base, data[base:base + size]
        if not stride:
            return
        base += stride


def scan(path):
    try:
        data = open(path, 'rb').read()
    except OSError:
        return None
    marker, = struct.unpack_from('<I', data, 0)
    if marker not in (7, 8):
        return None
    codes = collections.Counter()
    lengths = {}
    scripts = 0
    for base, c in chunks(data):
        if len(c) < 64:
            return None
        ns, nc = struct.unpack_from('<HH', c, 4)
        for i in range(nc):
            entry = 64 + ns * 4 + i * 8
            _, off = struct.unpack_from('<iI', c, entry)
            if off + 8 > len(c):
                continue
            cursor = off
            scripts += 1
            budget = 0
            while cursor + 8 <= len(c) and budget < 4096:
                opcode, length, time, references = struct.unpack_from('<hHhH', c, cursor)
                budget += 1
                if opcode == -1:
                    break
                if length < 8:
                    break
                codes[opcode] += 1
                lengths.setdefault(opcode, set()).add((length - 8) // 4)
                cursor += length
    return marker, codes, lengths, scripts


def main(directory):
    total = collections.Counter()
    lengths = {}
    markers = collections.Counter()
    files = 0
    scripts = 0
    for path in sorted(glob.glob(os.path.join(directory, '**', '*.anm'), recursive=True)):
        got = scan(path)
        if not got:
            continue
        marker, codes, per_file_lengths, count = got
        if int(sys.argv[2]) not in (0, marker) if len(sys.argv) > 2 else False:
            continue
        files += 1
        scripts += count
        markers[marker] += 1
        total.update(codes)
        for op, width in per_file_lengths.items():
            lengths.setdefault(op, set()).update(width)
    print('  %s: %d ANM files, %d scripts, markers %s' % (directory, files, scripts, dict(markers)))
    print('  opcodes in use (%d distinct):' % len(total))
    for op, count in sorted(total.items()):
        print('    %-5d used %-7d arg slots %s' % (op, count, sorted(lengths[op])))


if __name__ == '__main__':
    main(sys.argv[1])
