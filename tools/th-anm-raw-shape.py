#!/usr/bin/env python3
"""The shape of an opcode's own commands in a title's shipped files.

A loader row is only worth as much as what it counts. For a row whose command has no argument
(the form a body writes past itself), the count that matters is how many the title's own files
carry and what their own headers say: a body that reads an argument its command does not have reads
the next command, and one that writes one writes over it.

Usage: th-anm-raw-shape.py [--opcode N]... <title> [<title> ...]

Titles are read from the dumps (tools/tmp/anm<N>, and the title's own exported data when that
exists) - the same directories `th-anm-trace-find.py` reads - so the count is over the title's own
untouched bytes.
"""
import glob
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OPCODES = (3, 4, 5, 6, 7, 64, 81, 101, 102)
TITLES = (12, 13, 14, 16, 17, 18)


def directories(title):
    return [os.path.join(ROOT, 'tools', 'tmp', 'anm%d' % title),
            os.path.join(ROOT, 'runtimes', 'th%d' % title, 'th%d_web' % title, 'artifacts',
                         'cpp', 'th%d-data' % title)]


def census(title, opcodes):
    counts, lengths, files, seen = {}, {}, 0, set()
    for directory in directories(title):
        if not os.path.isdir(directory):
            continue
        for path in sorted(glob.glob(os.path.join(directory, '*.anm'))):
            if os.path.basename(path) in seen:
                continue
            seen.add(os.path.basename(path))
            files += 1
            data = open(path, 'rb').read()
            base = 0
            while base + 64 <= len(data):
                stride, = struct.unpack_from('<I', data, base + 36)
                chunk = data[base:base + (stride or (len(data) - base))]
                ns, nc = struct.unpack_from('<HH', chunk, 4)
                for i in range(nc):
                    source_id, off = struct.unpack_from('<iI', chunk, 64 + ns * 4 + i * 8)
                    cursor = off
                    while cursor + 8 <= len(chunk):
                        opcode, length = struct.unpack_from('<hH', chunk, cursor)
                        if opcode == -1:
                            break
                        counts[opcode] = counts.get(opcode, 0) + 1
                        if opcode in opcodes:
                            lengths.setdefault(opcode, {})[length] = \
                                lengths.setdefault(opcode, {}).get(length, 0) + 1
                        if length < 8:
                            break
                        cursor += length
                if not stride:
                    break
                base += stride
    return files, counts, lengths


def main(argv):
    if not argv:
        sys.exit(__doc__)
    opcodes, titles = set(), []
    index = 0
    while index < len(argv):
        if argv[index] == '--opcode':
            opcodes.add(int(argv[index + 1], 0))
            index += 2
        else:
            titles.append(int(argv[index]))
            index += 1
    if not opcodes:
        opcodes = set(DEFAULT_OPCODES)
    for title in titles:
        files, counts, lengths = census(title, opcodes)
        print('  th%d: %d file(s)' % (title, files))
        for opcode in sorted(opcodes):
            shape = lengths.get(opcode)
            print('    raw %-3d %5d %s' %
                  (opcode, counts.get(opcode, 0),
                   '' if not shape else
                   'by own length: ' + ', '.join('len %d: %d' % (length, count)
                                                 for length, count in sorted(shape.items()))))


if __name__ == '__main__':
    main(sys.argv[1:])
