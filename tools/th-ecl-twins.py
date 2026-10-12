#!/usr/bin/env python3
"""Find the instruction in another title's resources that carries the same record.

The titles renumber their command space, so "which TH12 opcode is this TH13 opcode" has to be
answered with something stronger than a nearby number. A record is a fixed-size header plus its
arguments, and a command the two titles both have carries the same length, the same parameter
count, the same difficulty mask and the same argument bytes. Searching the other title's ECL
resources for that record returns the number the other title gives it.

The instrument checks itself: TH13's 0x141 (with the MAPLEENEMY record) must find TH12's 0x118,
which `EnemyManager.cpp` already implements.

Usage: th-ecl-twins.py th13 <needle-title> --opcode 0x141 [--file NAME] [--dir PATH] [--all]
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


def instructions(path):
    data = open(path, 'rb').read()
    cursor = 0
    while True:
        block = data.find(b'ECLH', cursor)
        if block < 0:
            break
        cursor = block + 4
        at = block + 16
        while at + 16 <= len(data):
            time_value, op, length = struct.unpack_from('<ihh', data, at)
            references, difficulty, parameters = struct.unpack_from('<HBB', data, at + 8)
            if length < 16 or at + length > len(data):
                break
            yield (path, at, op, length, references, difficulty, parameters,
                   data[at + 16:at + length])
            if op == 0 and length == 16:
                break
            at += length


def signature(record):
    _, _, _, length, _, difficulty, parameters, arguments = record
    return (length, parameters, difficulty, arguments)


def main():
    target, other = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    opcode = int(args[args.index('--opcode') + 1], 0)
    name = args[args.index('--file') + 1] if '--file' in args else None
    only = args[args.index('--dir') + 1] if '--dir' in args else None
    root = only or DIRS[target]
    needles = []
    for path in sorted(glob.glob(os.path.join(root, '*.ecl'))):
        if name and os.path.basename(path) != name:
            continue
        for record in instructions(path):
            if record[2] == opcode:
                needles.append(record)
    print('  %s: %d record(s) with opcode 0x%x%s'
          % (target, len(needles), opcode, ' in %s' % name if name else ''))
    if not needles:
        return
    needle = needles[0]
    print('    sample at %s:0x%x length=%d params=%d difficulty=0x%x args=%s'
          % (os.path.basename(needle[0]), needle[1], needle[3], needle[6], needle[5],
             ' '.join('0x%x' % b for b in needle[7][:16])))
    counts = collections.Counter()
    examples = {}
    for path in sorted(glob.glob(os.path.join(DIRS[other], '*.ecl'))):
        for record in instructions(path):
            if signature(record) == signature(needle):
                counts[record[2]] += 1
                examples.setdefault(record[2], (os.path.basename(path), record[1]))
    print('    %s records with the same signature: %s'
          % (other, ' '.join('0x%x:%d' % pair for pair in counts.most_common(8)) or 'none'))
    for op, (path, at) in list(examples.items())[:6]:
        print('      0x%x example %s:0x%x' % (op, path, at))


if __name__ == '__main__':
    main()
