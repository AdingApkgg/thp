#!/usr/bin/env python3
"""Resolve one title's ANM opcode table from measurement, parallel stretches and shapes.

`th-anm-opcode-measure.py` aligns the shipped scripts and counts votes. That is the strongest
evidence, but the argument-less commands of a low band can drift onto a neighbour, so a vote
alone is not enough to fix an opcode. This resolves the votes with two more checks:

* parallel stretch: if a run of the title's opcodes carries the same argument signatures, in
  order and at a constant displacement, as a run of the other title's table (as
  `reference/thtk/thanm/thanm.c` records them), and at least one measured row inside the run
  agrees with that displacement, then the run fixes every opcode in it. One such run is
  `100..121`, signature for signature equal to th12's `6..27` at `-94`, with three
  independently measured rows inside it;
* shape: of the rows nothing else covers, a title opcode whose signature matches exactly one
  opcode of the other title is fixed by that, and a title opcode with no witness at all that
  loses a claimed target takes the least unused opcode of the same signature.

Usage: th-anm-opcode-resolve.py <dir_theirs> <dir_ours> [--cpp] [--unmapped]
"""
import importlib.util
import re
import sys


def apply_native_overrides(table):
    """Native bodies override statistical guesses, including confirmed defaults.

    Opcode 5 is a label consumed by interrupt lookup outside the dispatch; it
    must keep canonical marker 64 despite its dispatch body being a no-op.
    """
    native = load('anm_native', 'tools/th-anm-handlers.py')
    _, handlers, default = native.handlers(13)
    for opcode in table:
        if opcode not in (0,5) and handlers.get(opcode,default)==default:
            table[opcode]=(0,'native-default','original dispatcher advances without side effects')
    table[5]=(64,'native-label','TH13 interrupt scan compares opcode 5 at 0x4625c3')
    for opcode, canonical in {2:2,6:75,131:0x7002,302:67,304:0x7000,306:0x7003,309:62,310:72,312:0x7004,405:77,
                              422:83,423:0x700c,424:0x700d,431:0x700e,432:0x700f,507:0x7010,508:0x7018,
                              600:84,601:101,602:0x7017,603:0x7011,604:0x7015,605:0x7016,606:0x7012,607:0x7013,608:0x7014,
                              417:55,425:70,426:71,427:93,428:94,429:0x7005,430:0x7006,433:0x700b,434:0x7007,435:0x7008,436:0x7009,437:0x700a,
                              438:0x7001,500:88,501:90}.items():
        table[opcode]=(canonical,'native','TH13 handler checked against original machine code')
    return table


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
        return {int(a): b for a, b in re.findall(r'\{\s*(\d+)\s*,\s*"([^"]*)"\s*\}', body)}
    return table('v4p'), table('v8')


def minimal_stretches(v4, v8, anchors, minimum=4):
    """Runs of consecutive ids whose signatures are equal at one displacement, with a witness."""
    found = []
    ids = sorted(v8)
    offsets = {t - op for op, (t, _, _) in anchors.items()}
    for offset in sorted(offsets):
        i = 0
        while i < len(ids):
            def equal(k):
                return v4.get(ids[k] + offset) == v8[ids[k]]
            if not equal(i):
                i += 1
                continue
            j = i
            while j + 1 < len(ids) and ids[j + 1] == ids[j] + 1 and equal(j + 1):
                j += 1
            if ids[j] - ids[i] + 1 >= minimum:
                stamped = [ids[k] for k in range(i, j + 1) if ids[k] in anchors]
                # Every measured row inside the run has to agree with the run's displacement; one
                # that points elsewhere means the run's signatures are too alike to separate them.
                if stamped and all(anchors[o][0] == o + offset for o in stamped):
                    found.append((len(stamped), ids[j] - ids[i] + 1, offset, ids[i], ids[j], len(stamped)))
            i = j + 1
    found.sort(key=lambda row: (-row[0], -row[1]))
    return found


def context_rows(v4, v8, table, taken, candidates_for):
    """Rows whose longest equal-signature window leaves one displacement.

    A run of consecutive opcodes that carries the same signatures, in the same order, as a run of
    the other title's table is evidence on its own when the run is long enough to be specific; a
    measured row inside it, if any, has to agree. The longest such window decides, and only when
    one displacement is strictly longest.
    """
    plain = lambda op: (op - (op % 1))  # ids are integral already
    out = {}
    for op in sorted(v8):
        if op in table:
            continue
        best = {}
        for target in candidates_for(op):
            offset = target - op
            start, end = op, op
            while v8.get(start - 1) is not None and v8.get(start - 1) == v4.get(start - 1 + offset):
                start -= 1
            while v8.get(end + 1) is not None and v8.get(end + 1) == v4.get(end + 1 + offset):
                end += 1
            inside = [o for o in range(start, end + 1) if o in table]
            if inside and not all(table[o][0] == o + offset for o in inside):
                continue
            length = end - start + 1
            if all(v4.get(o + offset) is not None for o in range(start, end + 1)):
                best.setdefault(length, []).append((offset, start, end))
        if not best:
            continue
        top = max(best)
        if len(best[top]) != 1 or top < 3:
            continue
        offset, start, end = best[top][0]
        out[op] = (op + offset, 'context',
                   'the equal-signature window %d..%d with %d..%d at %+d is the longest one (%d opcodes) and no measured row inside disagrees' %
                   (start, end, start + offset, end + offset, offset, top))
    return out


def resolve(votes, exact, v4, v8, between=None, between_exact=None):
    strong, table = {}, {}
    for op, counts in votes.items():
        target, count = counts.most_common(1)[0]
        same = exact[op].get(target, 0)
        if same >= 3 and same * 2 >= count:
            strong[op] = (target, count, same)
    for op, (target, count, same) in strong.items():
        table[op] = (target, 'measured', '%d votes, %d with identical arguments' % (count, same))
    taken = {target for target, _, _ in strong.values()}

    # A command whose two aligned neighbours leave exactly one each must be the command between them;
    # `between_exact` counts the pairs whose argument bytes also matched, which is the same standard
    # of proof the aligned votes carry.
    between = between or {}
    between_exact = between_exact or {}
    exact_of = lambda o: between_exact.get(o) or {}
    for op in sorted(between, key=lambda o: (-max(exact_of(o).values(), default=0), -max(between[o].values(), default=0))):
        if op in table:
            continue
        target, count = exact_of(op).most_common(1)[0] if exact_of(op) else (None, 0)
        if target is None or count < 2 or target in taken:
            continue
        table[op] = (target, 'between', '%d pairs left this command between two aligned neighbours with identical arguments' % count)
        taken.add(target)

    stretches = minimal_stretches(v4, v8, strong)
    print('  parallel stretches with a witness: %s' %
          [(s[3], s[4], s[2], s[0]) for s in stretches[:6]])
    for inside, length, offset, start, end, _ in stretches:
        for op in range(start, end + 1):
            if op in table or op not in v8 or op + offset not in v4:
                continue
            table[op] = (op + offset, 'family',
                         'in the stretch %d..%d, signature for signature the same as %d..%d at %+d, with %d measured rows inside' %
                         (start, end, start + offset, end + offset, offset, inside))
            taken.add(op + offset)

    def candidates_for(op):
        return [c for c, shape in sorted(v4.items()) if shape == v8.get(op) and c not in taken]
    for op, (target, kind, why) in context_rows(v4, v8, table, taken, candidates_for).items():
        if op not in table:
            table[op] = (target, kind, why)
            taken.add(target)

    for op in sorted(votes):
        if op in table:
            continue
        target, count = votes[op].most_common(1)[0]
        if target in taken:
            continue
        table[op] = (target, 'measured', '%d votes, %d with identical arguments (weak)' % (count, exact[op].get(target, 0)))
        taken.add(target)

    # Weakest tier: nothing measured and no window decides, so the argument shape is the only
    # evidence left, and among shapes that repeat (there are twenty `"ff"` opcodes in th12's table)
    # the least one is taken. The row says so.
    for op in sorted(v8):
        if op in table:
            continue
        shapes = [c for c, s in sorted(v4.items()) if s == v8[op]]
        if shapes:
            free = [c for c in shapes if c not in taken]
            table[op] = (free[0] if free else shapes[0], 'shape',
                         'shape %r admits %s; %s' % (v8[op], shapes[:6],
                                                     'the least unused is %d' % free[0] if free else 'all are claimed, so the least is %d' % shapes[0]))
            taken.add(table[op][0])
    for op in sorted(v8):
        if op in table:
            continue
        if op in votes:
            target, _ = votes[op].most_common(1)[0]
        else:
            target = None
        candidates = [c for c, s in sorted(v4.items()) if s == v8[op] and c not in taken]
        if target is not None and target in taken and candidates:
            table[op] = (candidates[0], 'duplicate',
                         'voted %d, claimed; the shape %r leaves %s' % (target, v8[op], candidates[0]))
        elif candidates and len([c for c, s in sorted(v4.items()) if s == v8[op]]) == 1:
            table[op] = (candidates[0], 'signature', 'the only th12 opcode with shape %r' % v8[op])
        if op in table:
            taken.add(table[op][0])
    return table


def main(dir_theirs, dir_ours, emit_cpp, show_unmapped):
    measure = load('measure', 'tools/th-anm-opcode-measure.py')
    v4, v8 = signatures('reference/thtk/thanm/thanm.c')
    votes, exact, scripts, between, between_exact = measure.measure(dir_theirs, dir_ours)
    table = apply_native_overrides(resolve(votes, exact, v4, v8, between, between_exact))
    kinds = {}
    for _, (_, kind, _) in table.items():
        kinds[kind] = kinds.get(kind, 0) + 1
    print('  %d scripts aligned, %d opcodes voted, %d rows: %s' % (scripts, len(votes), len(table), kinds))
    if show_unmapped:
        for file in sorted(__import__('glob').glob(dir_theirs + '/*.anm')):
            import os
            used = {op for bodies in measure.commands(file).values() for body in bodies for op, _ in body}
            missing = sorted(op for op in used if op not in table)
            if missing:
                print('    %s uses %s' % (os.path.basename(file), missing))
    if emit_cpp:
        print('// >>> th13 rows')
        for op in sorted(table, key=lambda k: (len(str(k)), k)):
            target, kind, why = table[op]
            witnesses = exact[op].get(target, 0) if kind in ('measured', 'duplicate') else 0
            evidence = kind
            if kind == 'family':
                evidence = 'family'
                witnesses = exact[op].get(target, 0)
            print('    { %d, %d, %d, "%s" },  // %s' % (op, target, witnesses, evidence, v8.get(op, '?')))
        print('// <<< th13 rows')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], '--cpp' in sys.argv, '--unmapped' in sys.argv)
