#!/usr/bin/env python3
"""Propose a title's ANM opcode table from measured anchors, family offsets and signatures.

Three sources, in order of strength:

1. measured: `th-anm-opcode-pairs.py` aligns the two titles' shipped ANM files command for
   command and counts the wins; a pair with a witness is measured, not inferred;
2. family offset: the opcodes of one instruction family run consecutively in both versions
   (an arithmetic family, a comparison family, a spawn family), so a measured row inside a
   family fixes the offset for the whole family, and the signatures and argument counts have to
   agree at every step for the offset to hold;
3. signature: `reference/thtk/thanm/thanm.c`'s `formats_v4p` and `formats_v8` give an
   argument signature per opcode; a th13 opcode whose signature matches exactly one v4p
   opcode is fixed by that alone (weaker: the signature is a shape, not a behaviour).

Usage: th-anm-opcode-table.py <th13-data-dir> <th12-data-dir> [--cpp]
"""
import importlib.util
import os
import re
import sys


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signatures(path):
    src = open(path, encoding='utf-8', errors='replace').read()

    def table(name):
        i = src.index('formats_' + name + '[]')
        body = src[i:src.index('};', i)]
        return [(int(a), b) for a, b in re.findall(r'\{\s*(\d+)\s*,\s*"([^"]*)"\s*\}', body)]
    return dict(table('v4p')), dict(table('v8'))


def measured(pairs, dir13, dir12):
    """The majority pair per th13 opcode, with its witness count."""
    import collections
    votes = collections.defaultdict(list)
    for path in sorted(__import__('glob').glob(os.path.join(dir13, '**', '*.anm'), recursive=True)):
        other = os.path.join(dir12, os.path.basename(path))
        if not os.path.exists(other):
            continue
        left, right = pairs.scripts(path), pairs.scripts(other)
        for source_id, bodies in left.items():
            if source_id not in right:
                continue
            for body in bodies:
                best, best_len = None, 0
                for candidate in right[source_id]:
                    run = 0
                    for (_, args_a), (_, args_b) in zip(body, candidate):
                        if args_a != args_b:
                            break
                        run += 1
                    if run > best_len:
                        best, best_len = candidate, run
                if best is None or best_len < 2:
                    continue
                for index in range(best_len):
                    votes[body[index][0]].append((body[index][1], best[index][0]))
    out = {}
    for op, seen in votes.items():
        counts = __import__('collections').Counter(seen)
        (args, target), count = counts.most_common(1)[0]
        out[op] = (target, args, count, len(seen))
    return out


def main(dir13, dir12, emit_cpp):
    pairs = load('pairs', 'tools/th-anm-opcode-pairs.py')
    v4, v8 = signatures('reference/thtk/thanm/thanm.c')
    seen = measured(pairs, dir13, dir12)
    table = {}
    for op, (target, args, count, total) in seen.items():
        table[op] = (target, 'measured', '%d witnesses of %d' % (count, total))

    def runs(ids):
        out, start, prev = [], None, None
        for k in sorted(ids):
            if prev is None or k != prev + 1:
                if prev is not None:
                    out.append((start, prev))
                start = k
            prev = k
        out.append((start, prev))
        return out

    print('  signatures: formats_v4p %d, formats_v8 %d; measured rows %d' % (len(v4), len(v8), len(table)))
    print('  families (contiguous v8 runs) and, for each, the offsets its measured rows imply:')
    for start, end in runs(v8):
        anchors = {op: table[op] for op in range(start, end + 1) if op in table}
        offsets = {t - op for op, (t, kind, why) in anchors.items()}
        shape_ok = None
        if len(offsets) == 1:
            offset = offsets.pop()
            shape_ok = all(v8.get(start + i) == v4.get(start + i + offset) or
                           len(v8.get(start + i, '')) == len(v4.get(start + i + offset, '') or 'x')
                           for i in range(end - start + 1) if start + i in v8 and start + i + offset in v4)
            shape_note = 'signature/argument counts agree' if shape_ok else 'signatures differ at some step'
        else:
            shape_note = 'anchors disagree: %s' % sorted(offsets) if offsets else 'no anchor in this family'
        print('    %3d..%-3d %-28s %s' % (start, end, shape_note, {a: v[0] for a, v in anchors.items()}))
        if len(offsets) == 1 and shape_ok:
            offset = {t - op for op, (t, _, _) in anchors.items()}.pop()
            anchor = sorted(anchors)[0]
            for op in range(start, end + 1):
                if op not in table and op + offset in v4:
                    table[op] = (op + offset, 'family', 'family %d..%d offset %+d at { %d, %d }' %
                                  (start, end, offset, anchor, anchors[anchor][0]))

    for op in sorted(v8):
        if op in table:
            continue
        candidates = [c for c, s in sorted(v4.items()) if s == v8[op]]
        if len(candidates) == 1:
            table[op] = (candidates[0], 'signature', 'the only v4p opcode with signature %r' % v8[op])

    by_class = {}
    for op, (target, kind, why) in table.items():
        by_class.setdefault(kind, []).append(op)
    print('  table: %s' % {k: len(v) for k, v in sorted(by_class.items())})
    unresolved = [op for op in sorted(v8) if op not in table]
    print('  unresolved in v8: %d %s' % (len(unresolved), unresolved))
    if emit_cpp:
        for op in sorted(table, key=lambda k: (str(k)[0], len(str(k)), k)):
            target, kind, why = table[op]
            print('    { %d, %d },  // %s: %s' % (op, target, v8.get(op, '?'), why))
    return table


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], '--cpp' in sys.argv)
