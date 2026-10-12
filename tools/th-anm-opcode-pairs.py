#!/usr/bin/env python3
"""Derive one title's ANM opcode numbering from another's, by aligning the shipped files.

An ANM opcode number is the title's, the way the arcade archives' cipher and the `.sht` layout
are: two titles ship the same kind of content (`ascii.anm`, `title.anm`, `text.anm`, ...)
with the same script ids, and the instruction streams line up command for command - same length,
same argument slots - while the numbers differ. This walks both titles' files, matches scripts by
source id, and records the (other title's opcode) -> (this title's opcode) pairs it sees.

Usage: anm-opcode-pairs.py <dir_a> <dir_b>
"""
import collections
import glob
import os
import struct
import sys


def chunks(data):
    base = 0
    while True:
        if len(data) - base < 64:
            return
        stride, = struct.unpack_from('<I', data, base + 36)
        size = stride or (len(data) - base)
        yield data[base:base + size]
        if not stride:
            return
        base += stride


def scripts(path):
    data = open(path, 'rb').read()
    if len(data) < 64 or struct.unpack_from('<I', data, 0)[0] not in (7, 8):
        return {}
    out = {}
    for c in chunks(data):
        if len(c) < 64:
            return out
        ns, nc = struct.unpack_from('<HH', c, 4)
        for i in range(nc):
            entry = 64 + ns * 4 + i * 8
            source_id, off = struct.unpack_from('<iI', c, entry)
            cursor = off
            body = []
            while cursor + 8 <= len(c):
                opcode, length, time, references = struct.unpack_from('<hHhH', c, cursor)
                if opcode == -1 or length < 8 or cursor + length > len(c):
                    break
                body.append((opcode, (length - 8) // 4))
                cursor += length
            out.setdefault(source_id, []).append(body)
    return out


def main(dir_a, dir_b):
    pairs = collections.Counter()
    witness = {}
    aligned = 0
    scripts_seen = 0
    for path in sorted(glob.glob(os.path.join(dir_a, '**', '*.anm'), recursive=True)):
        name = os.path.basename(path)
        other = os.path.join(dir_b, name)
        if not os.path.exists(other):
            continue
        left, right = scripts(path), scripts(other)
        for source_id, bodies in left.items():
            if source_id not in right:
                continue
            for body in bodies:
                # Align as far as the argument counts agree, so a pair of scripts that differ somewhere still
                # contributes the commands before the divergence. The candidate is the body with the longest
                # agreeing prefix.
                best, best_len = None, 0
                for candidate in right[source_id]:
                    run = 0
                    for (op_a, args_a), (op_b, args_b) in zip(body, candidate):
                        if args_a != args_b:
                            break
                        run += 1
                    if run > best_len:
                        best, best_len = candidate, run
                if best is None or best_len < 2:
                    continue
                scripts_seen += 1
                aligned += 1
                for (op_left, args_left), (op_right, args_right) in zip(body[:best_len], best[:best_len]):
                    pairs[(op_right, op_left, args_left)] += 1
                    witness.setdefault((op_right, args_left), (name, source_id, op_left))
    print('  %s vs %s: %d scripts aligned, %d opcode pairs' % (os.path.basename(dir_a), os.path.basename(dir_b), aligned, sum(pairs.values())))
    mapping = {}
    for (op_other, op_this, args), count in pairs.most_common():
        current = mapping.get(op_other)
        if current is None or count > current[1]:
            mapping[op_other] = (op_this, count, args)
    for op_other in sorted(mapping, key=lambda k: (len(str(k)), k)):
        op_this, count, args = mapping[op_other]
        name, source_id, _ = witness[(op_other, args)]
        alternatives = sorted({p[1] for p in pairs if p[0] == op_other})
        flag = '' if len(alternatives) == 1 else '  (also seen: %s)' % alternatives
        print('    %-5s -> %-5d  %6d witnesses, %d args  [%s id %d]%s' % (op_other, op_this, count, args, name, source_id, flag))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
