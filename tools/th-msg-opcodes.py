#!/usr/bin/env python3
"""Census the opcodes a title's message resources actually use.

The message interpreter's stream is a sequence of 4-byte headers (a 16-bit time, the opcode, the
payload length) followed by the payload, one stream per entry in the resource's own offset table.
Walking every entry of every .msg of a title says which message opcodes the title needs, which is
the list a port has to cover - and it is a different list per title (TH13 uses 1 and 2 where the
port's TH12-derived switch had no case, and 28/29/30/31 where TH12 has no case at all).

Usage: th-msg-opcodes.py th12 th13 [--dir PATH]
"""
import collections
import glob
import os
import struct
import sys

DIRS = {'th12': 'runtimes/th12/th12_web/artifacts/cpp/th12-data',
        'th13': 'runtimes/th13/th13_web/artifacts/cpp/th13-data',
        'th14': 'runtimes/th14/th14_web/artifacts/cpp/th14-data',
        'th16': 'runtimes/th16/th16_web/artifacts/cpp/th16-data',
        'th17': 'runtimes/th17/th17_web/artifacts/cpp/th17-data',
        'th18': 'runtimes/th18/th18_web/artifacts/cpp/th18-data'}


def opcodes(path):
    data = open(path, 'rb').read()
    if len(data) < 4:
        return
    count = struct.unpack_from('<I', data, 0)[0]
    if count > 0x1000:
        return
    offsets = [struct.unpack_from('<I', data, 4 + 8 * i)[0] for i in range(count)]
    for index, offset in enumerate(offsets):
        stop = offsets[index + 1] if index + 1 < len(offsets) else len(data)
        at = offset
        while at + 4 <= min(stop, len(data)):
            length = data[at + 3]
            if at + 4 + length > len(data):
                break
            yield data[at + 2]
            at += 4 + length


def main():
    titles = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = sys.argv[sys.argv.index('--dir') + 1] if '--dir' in sys.argv else None
    for title in titles:
        directory = root or DIRS[title]
        counts = collections.Counter()
        entries = 0
        for path in sorted(glob.glob(os.path.join(directory, '*.msg'))):
            entries += 1
            for opcode in opcodes(path):
                counts[opcode] += 1
        print('  %s: %d file(s), %d instruction(s), %d opcode(s)'
              % (title, entries, sum(counts.values()), len(counts)))
        print('    %s' % ' '.join('%d:%d' % pair for pair in sorted(counts.items())))


if __name__ == '__main__':
    main()
