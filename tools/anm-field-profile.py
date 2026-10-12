"""Profile one context offset: who writes it, with what shape, and what explains the change.

Given a title and an offset, this prints what is known about that word:

  the code side, from docs/porting/anm-flag-writes-5-titles.json: the handlers the reader found
    writing there, with the masks and the sample texts, grouped by mask;
  the run side, from the widest corpus of that title: for each case with a change at the offset,
    the delta, and then the question that names a field - is the delta a function of the argument
    the case carries, of the variant flag, or of the handler alone.
A field set from the argument (a flag bit, a shifted field) answers the first; a field that
follows a preset state answers the second; and a field that moves differently on the same inputs
answers the third only.

Usage: py -3 tools/anm-field-profile.py --title=13 --offset=0x538
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 0x700
CORPUS = {12: ['anm-native.json'],
          13: ['anm-native-context-all.json', 'anm-native-context.json'],
          14: ['anm-native-context-all.json', 'anm-native-context.json'],
          16: ['anm-native-all.json'],
          17: ['anm-native-all.json', 'anm-native.json'],
          18: ['anm-native-all.json', 'anm-native.json']}


def corpus_of(title):
    for name in CORPUS[title]:
        path = ROOT / ('artifacts/th%d/%s' % (title, name))
        if path.exists():
            return path
    return None


def code_side(title, offset):
    path = ROOT / 'docs/porting/anm-flag-writes-5-titles.json'
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))['titles'].get(str(title), {})
    rows = []
    for op, writes in data.get('rows', {}).items():
        for row in writes:
            if row['slot'].lower() == offset.lower():
                rows.append((int(op), row))
    for op, writes in data.get('second', {}).items():
        for row in writes:
            if row['slot'].lower() == offset.lower():
                rows.append((int(op), row))
    return sorted(rows, key=lambda pair: (pair[0], pair[1].get('text', '')))


def main():
    title = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--title=')), '13'))
    offset = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--offset=')), '0x538'),
                 16)
    wanted = hex(offset)
    rows = code_side(title, wanted)
    by_mask = defaultdict(list)
    for op, row in rows:
        by_mask[row['mask'] or ('via ' + row['source'])].append(op)
    print('  th%d %#x, code side: %d writes from %d handlers'
          % (title, offset, len(rows), len(set(op for op, _ in rows))))
    for mask, ops in sorted(by_mask.items(), key=lambda kv: -len(kv[1]))[:8]:
        sample = next(r['text'] for op, r in rows if (r['mask'] or ('via ' + r['source'])) == mask)
        print('     mask %-14s %3d handlers %s   e.g. %s'
              % (mask, len(ops), sorted(ops)[:6], sample[:56]))

    corpus = corpus_of(title)
    cases = json.loads(corpus.read_text(encoding='utf-8'))['cases']
    moved, by_op = 0, defaultdict(set)
    values, variants, handlers = defaultdict(set), defaultdict(set), defaultdict(set)
    for case in cases:
        if case.get('fault') or 'before' not in case:
            continue
        a, b = bytes.fromhex(case['before']), bytes.fromhex(case['context'])
        delta = int.from_bytes(a[offset:offset + 4], 'little') ^ int.from_bytes(
            b[offset:offset + 4], 'little')
        if not delta:
            continue
        moved += 1
        by_op[case['op']].add(delta)
        values[(case['op'], delta)].add(case.get('value', case.get('arg')))
        variants[(case['op'], delta)].add(case.get('variant'))
        handlers[(case['op'], delta)].add(case.get('arg'))
    print('  run side (%s): %d cases change it, over %d handlers'
          % (corpus.name, moved, len(by_op)))
    for op in sorted(by_op)[:10]:
        deltas = sorted(by_op[op])
        detail = []
        for delta in deltas[:4]:
            vals = sorted(str(v) for v in values[(op, delta)])[:4]
            detail.append('%s when value in %s' % (hex(delta), vals))
        print('     op %-4d %s' % (op, '; '.join(detail)))
    if by_op:
        arg_clean = sum(1 for key, vals in values.items() if len(vals) == 1)
        var_clean = sum(1 for key, vals in variants.items() if len(vals) == 1)
        print('     delta determined by the argument in %d of %d handler-delta pairs; by the variant '
              'in %d' % (arg_clean, len(values), var_clean))
    else:
        print('     the corpus never changes this word', end='')
        if rows:
            print(', though %d handlers write it in code' % len(set(op for op, _ in rows)))
        else:
            print('')


if __name__ == '__main__':
    main()
