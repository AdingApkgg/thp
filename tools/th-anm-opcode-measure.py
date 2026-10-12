#!/usr/bin/env python3
"""Measure the ANM opcode correspondence between two titles by aligning whole scripts.

The two titles ship the same kind of ANM content under the same file names and script ids, and a
corresponding command pair usually carries the same argument values: the same sprite index, the
same duration, the same coordinates. So the alignment score is built from the argument slots
themselves (`+3` when they are equal, `+1` when only the count agrees, `-1` otherwise, `-1`
for a gap), and every aligned pair is a vote. A vote whose arguments match exactly is the
strongest kind, because the two commands are the same command.

Usage: th-anm-opcode-measure.py <dir_a> <dir_b> [--cpp]
  (dir_a is the title whose numbering is being measured, dir_b the title the port's
   interpreter was transcribed from)
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


def commands(path):
    """{source_id: [ [ (opcode, arg_bytes), ... ], ... ]} for one ANM file."""
    try:
        data = open(path, 'rb').read()
    except OSError:
        return {}
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
            cursor, body = off, []
            while cursor + 8 <= len(c):
                opcode, length, time, references = struct.unpack_from('<hHhH', c, cursor)
                if opcode == -1 or length < 8 or cursor + length > len(c):
                    break
                body.append((opcode, c[cursor + 8:cursor + length]))
                cursor += length
            out.setdefault(source_id, []).append(body)
    return out


def align(a, b):
    """Needleman-Wunsch over two command lists; returns the aligned index pairs."""
    n, m = len(a), len(b)
    if not n or not m or abs(n - m) > 12:
        return []
    score = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = score[i - 1][0] - 1
    for j in range(1, m + 1):
        score[0][j] = score[0][j - 1] - 1
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            left, right = a[i - 1][1], b[j - 1][1]
            if len(left) != len(right):
                step = -1
            elif left == right:
                step = 3
            else:
                step = 1
            score[i][j] = max(score[i - 1][j] - 1, score[i][j - 1] - 1, score[i - 1][j - 1] + step)
    pairs, i, j = [], n, m
    while i and j:
        left, right = a[i - 1][1], b[j - 1][1]
        if len(left) != len(right):
            step = -1
        elif left == right:
            step = 3
        else:
            step = 1
        if score[i][j] == score[i - 1][j - 1] + step:
            pairs.append((i - 1, j - 1, left == right))
            i, j = i - 1, j - 1
        elif score[i][j] == score[i - 1][j] - 1:
            i -= 1
        else:
            j -= 1
    return pairs[::-1]


def measure(dir_a, dir_b):
    votes = collections.defaultdict(collections.Counter)
    exact = collections.defaultdict(collections.Counter)
    between = collections.defaultdict(collections.Counter)
    between_exact = collections.defaultdict(collections.Counter)
    scripts = 0
    for path in sorted(glob.glob(os.path.join(dir_a, '**', '*.anm'), recursive=True)):
        series = commands(path)
        other = commands(os.path.join(dir_b, os.path.basename(path)))
        if not series or not other:
            continue
        pool = [(sid, body) for sid, bodies in other.items() for body in bodies]
        for source_id, bodies in series.items():
            for body in bodies:
                same_id = [(sid, b) for sid, b in pool if sid == source_id]
                candidates = same_id or pool
                best, best_pairs = None, []
                for source, candidate in candidates:
                    pairs = align(body, candidate)
                    score = sum(3 if same else 1 for _, _, same in pairs)
                    if score > sum(3 if s else 1 for _, _, s in best_pairs):
                        best, best_pairs = candidate, pairs
                # A script whose id drifted in the other title still contains the same commands; if
                # nothing under the id scored, look for the closest script of the whole file.
                if len(best_pairs) < 4:
                    for source, candidate in pool:
                        pairs = align(body, candidate)
                        score = sum(3 if same else 1 for _, _, same in pairs)
                        if score > sum(3 if s else 1 for _, _, s in best_pairs):
                            best, best_pairs = candidate, pairs
                if not best_pairs:
                    continue
                scripts += 1
                for i, j, same in best_pairs:
                    op_a, op_b = body[i][0], best[j][0]
                    votes[op_a][op_b] += 1
                    if same:
                        exact[op_a][op_b] += 1
                # Between two aligned neighbours with one command each left over, the leftovers must
                # correspond: their argument bytes decide. That reaches the commands a script only
                # uses once, which the alignment itself leaves unmatched.
                for (i1, j1, _), (i2, j2, _) in zip(best_pairs, best_pairs[1:]):
                    if i2 == i1 + 2 and j2 == j1 + 2:
                        left, right = body[i1 + 1], best[j1 + 1]
                        between[left[0]][right[0]] += 1
                        if left[1] == right[1]:
                            between_exact[left[0]][right[0]] += 1
    return votes, exact, scripts, between, between_exact


def main(dir_a, dir_b, emit_cpp):
    votes, exact, scripts, between, between_exact = measure(dir_a, dir_b)
    table = {}
    for op, counts in votes.items():
        target, count = counts.most_common(1)[0]
        table[op] = (target, count, exact[op][target])
    print('  %d scripts aligned; %d th13 opcodes voted for; %d reached between neighbours' % (scripts, len(table), len(between)))
    if emit_cpp:
        for op in sorted(table, key=lambda k: (len(str(k)), k)):
            target, count, same = table[op]
            print('    { %d, %d },  // %d votes, %d with identical arguments' % (op, target, count, same))
    else:
        for op in sorted(table, key=lambda k: (len(str(k)), k)):
            target, count, same = table[op]
            rivals = {t: c for t, c in votes[op].most_common() if t != target}
            print('    %-4d -> %-4d  %5d votes (%d identical args)%s' %
                  (op, target, count, same, '  rivals %s' % dict(list(rivals.items())[:4]) if rivals else ''))
    return table


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], '--cpp' in sys.argv)
