#!/usr/bin/env python3
"""How each title spells the frames-counted wait, counted over all the ECL its own data holds.

`EclRoutes.hpp::ecl_vm_opcode` translates a title's bytecode numbers into the ones the port's
interpreter switches on, and every translation it carries was measured from the titles rather than
assumed. The plainest measurement is this census: the wait has one number per title, and a title
that spells it 0x17 does not spell it 0x53 at all.

  py -3 tools/th-ecl-wait-census.py [titles...] [--words 22,23,24,30,31,53,83,84,85,86]

The whole ECL set of a title is walked with the record layout `th-ecl-walk.py` validates (an ECLH
block, instructions 16 bytes in, the length at +0x06), which is the same walk the census of all
opcodes uses.
"""
import argparse
import collections
import glob
import os
import struct

DIRS = {
    'th12': 'runtimes/th12/th12_web/artifacts/cpp/th12-data',
    'th13': 'runtimes/th13/th13_web/artifacts/cpp/th13-data',
    'th14': 'runtimes/th14/th14_web/artifacts/cpp/th14-data',
    'th16': 'runtimes/th16/th16_web/artifacts/cpp/th16-data',
    'th17': 'runtimes/th17/th17_web/artifacts/cpp/th17-data',
    'th18': 'runtimes/th18/th18_web/artifacts/cpp/th18-data',
}
DEFAULT = (22, 23, 24, 30, 31, 53, 83, 84, 85, 86)


def census(root):
    totals = collections.Counter()
    files = 0
    for path in sorted(glob.glob(os.path.join(root, '*.ecl'))):
        data = open(path, 'rb').read()
        files += 1
        cursor = 0
        while True:
            block = data.find(b'ECLH', cursor)
            if block < 0:
                break
            cursor = block + 4
            at = block + 16
            while at + 16 <= len(data):
                opcode, = struct.unpack_from('<h', data, at + 4)
                length, = struct.unpack_from('<h', data, at + 6)
                if length < 16 or at + length > len(data):
                    break
                totals[opcode] += 1
                at += length
    return files, totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('titles', nargs='*')
    parser.add_argument('--words', default=None)
    args = parser.parse_args()
    words = [int(word, 0) for word in args.words.split(',')] if args.words else DEFAULT
    for title in args.titles or list(DIRS):
        root = DIRS.get(title)
        if not root or not os.path.isdir(root):
            print('  %-5s no data at %s' % (title, root))
            continue
        files, totals = census(root)
        print('  %-5s %2d file(s), %6d word(s) | %s'
              % (title, files, sum(totals.values()),
                 '  '.join('%d=%d' % (word, totals.get(word, 0)) for word in words)))


if __name__ == '__main__':
    main()
