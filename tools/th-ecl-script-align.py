#!/usr/bin/env python3
"""Align two titles' corresponding stage scripts by their records and read off the number mapping.

A stage is the same stage in both titles, so its script is nearly the same sequence of commands.
The opcode words differ (the numbering is per title), but the record shapes and arguments mostly do
not, so aligning the two record sequences on `(length, parameters, arguments)` and then reading the
opcodes of each aligned pair gives the mapping between the two numberings - for that stage, from
evidence, without a table.

Votes are counted per pair, so a number used in several contexts shows its alternatives, and a pair
that is a coincidence shows up with one vote instead of many. The known map (TH13 0x141 -> TH12
0x118) is the instrument's check.

Usage: th-ecl-script-align.py th13:st05.ecl th12:stage05.ecl [--min-votes N] [--opcode 0x206]
"""
import collections
import difflib
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('twins', 'tools/th-ecl-twins.py')
twins = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twins)


def records(title, name):
    return [r for r in twins.instructions('%s/%s' % (twins.DIRS[title], name)) if r[3] >= 16]


def token(record):
    return (record[3], record[6], record[5], bytes(record[7]))


def main():
    left, right = sys.argv[1], sys.argv[2]
    ltitle, lname = left.split(':')
    rtitle, rname = right.split(':')
    args = sys.argv[3:]
    minimum = int(args[args.index('--min-votes') + 1]) if '--min-votes' in args else 2
    only = [int(a, 0) for a in args if a.startswith('0x')]

    a, b = records(ltitle, lname), records(rtitle, rname)
    print('  %s:%s %d records; %s:%s %d records' % (ltitle, lname, len(a), rtitle, rname, len(b)))
    matcher = difflib.SequenceMatcher(None, [token(r) for r in a], [token(r) for r in b],
                                      autojunk=False)
    pairs = collections.Counter()
    aligned = 0
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            pairs[(a[block.a + k][2], b[block.b + k][2])] += 1
            aligned += 1
    print('  %d of %d records align (%.0f%% of the left script)'
          % (aligned, len(a), 100.0 * aligned / max(1, len(a))))
    by_left = collections.defaultdict(collections.Counter)
    for (lop, rop), votes in pairs.items():
        by_left[lop][rop] += votes
    for lop in sorted(by_left):
        if only and lop not in only:
            continue
        best = by_left[lop].most_common(4)
        if not best or best[0][1] < minimum:
            continue
        print('  0x%03x -> %s' % (lop, ' '.join('0x%03x:%d' % pair for pair in best)))


if __name__ == '__main__':
    main()
