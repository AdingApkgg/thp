#!/usr/bin/env python3
"""Pair the commands of two titles by the records each number carries, not by the number.

A title's ECL resources are a corpus: each opcode number occurs many times, and the multiset of
records it occurs with is a fingerprint. A command the two titles share has the same multiset
(TH13's 0x141 and TH12's 0x118 are the clearest case - identical length, parameter count,
difficulty and argument bytes), while a number the titles merely spell the same has a different one
(0x206 is a rank-gated count/layers pair in TH12 and a manager call in TH13). Scoring every target
number against every other-title number by shared signatures gives the pairing, and the known pair is
the instrument's own check.

Usage: th-ecl-opcode-map.py th13 th12 [--min-score N] [--top K] [--check 0x141=0x118]
"""
import collections
import glob
import hashlib
import os
import struct
import sys

DIRS = {'th12': 'runtimes/th12/th12_web/artifacts/cpp/th12-data',
        'th13': 'runtimes/th13/th13_web/artifacts/cpp/th13-data',
        'th14': 'runtimes/th14/th14_web/artifacts/cpp/th14-data',
        'th16': 'runtimes/th16/th16_web/artifacts/cpp/th16-data',
        'th17': 'runtimes/th17/th17_web/artifacts/cpp/th17-data',
        'th18': 'runtimes/th18/th18_web/artifacts/cpp/th18-data'}


def fingerprint(title):
    root = DIRS[title]
    table = collections.defaultdict(collections.Counter)
    for path in sorted(glob.glob(os.path.join(root, '*.ecl'))):
        data = open(path, 'rb').read()
        cursor = 0
        while True:
            block = data.find(b'ECLH', cursor)
            if block < 0:
                break
            cursor = block + 4
            at = block + 16
            while at + 16 <= len(data):
                _, op, length = struct.unpack_from('<ihh', data, at)
                references, difficulty, parameters = struct.unpack_from('<HBB', data, at + 8)
                if length < 16 or at + length > len(data):
                    break
                key = hashlib.blake2b(struct.pack('<hHBB', length, references, difficulty, parameters)
                                      + data[at + 16:at + length], digest_size=8).digest()
                table[op][key] += 1
                at += length
    return table


def similarity(a, b):
    """Shared signature occurrences, normalised by the smaller corpus so a rare number can win."""
    shared = sum(min(count, b.get(key, 0)) for key, count in a.items())
    total = sum(a.values())
    return shared, shared / total if total else 0.0


def main():
    target, other = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    top = int(args[args.index('--top') + 1]) if '--top' in args else 4
    check = args[args.index('--check') + 1] if '--check' in args else None
    only = [int(a, 0) for a in args if a.startswith('0x') and '=' not in a]

    mine, theirs = fingerprint(target), fingerprint(other)
    print('  %s: %d opcode numbers; %s: %d (%d records)'
          % (target, len(mine), other, len(theirs), sum(sum(c.values()) for c in theirs.values())))

    if check:
        left, right = check.split('=')
        left, right = int(left, 0), int(right, 0)
        shared, ratio = similarity(mine[left], theirs.get(right, collections.Counter()))
        print('  check: %s 0x%x against %s 0x%x -> %d shared occurrences (%.0f%% of its corpus)'
              % (target, left, other, right, shared, 100 * ratio))
        shared_other, ratio_other = similarity(theirs[right], mine.get(left, collections.Counter()))
        print('         and %s 0x%x against %s 0x%x -> %d (%.0f%%)'
              % (other, right, target, left, shared_other, 100 * ratio_other))

    for opcode in sorted(mine):
        if only and opcode not in only:
            continue
        scores = []
        for candidate, counter in theirs.items():
            shared, ratio = similarity(mine[opcode], counter)
            if shared:
                scores.append((shared, ratio, candidate))
        scores.sort(reverse=True)
        if not scores:
            continue
        label = ' '.join('0x%x:%d/%.0f%%' % (s[2], s[0], 100 * s[1]) for s in scores[:top])
        print('  0x%03x (%5d records, %3d signatures): %s'
              % (opcode, sum(mine[opcode].values()), len(mine[opcode]), label))


if __name__ == '__main__':
    main()
