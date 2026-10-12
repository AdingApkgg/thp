#!/usr/bin/env python3
"""Count the ECL opcode words each title's shipped scripts and stages actually use.

Walking the resources with the record layout `th-ecl-walk.py` validates gives a per-title histogram of
the opcode word. The two histograms answer a question a single failing script cannot: whether a number
that stops this title is used by the other title at all, and which numbers the port's interpreter has
to cover for the title in hand. TH12's census is the control - every number in it must already run,
because TH12 plays through.

Usage: th-ecl-opcode-census.py [title ...] [--dir PATH] [--missing PATH]
"""
import collections
import glob
import json
import os
import struct
import sys

args = sys.argv[1:]
titles = [a for a in args if not a.startswith('--') and '.' not in a and a in
          ('th12', 'th13', 'th14', 'th16', 'th17', 'th18')]
if not titles:
    titles = ['th12', 'th13']
only = None
if '--dir' in args:
    only = args[args.index('--dir') + 1]
known = None
if '--missing' in args:
    known = json.load(open(args[args.index('--missing') + 1]))

DIRS = {'th12': 'runtimes/th12/th12_web/artifacts/cpp/th12-data',
        'th13': 'runtimes/th13/th13_web/artifacts/cpp/th13-data'}

for title in titles:
    root = only or DIRS.get(title)
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
                op, = struct.unpack_from('<h', data, at + 4)
                length, = struct.unpack_from('<h', data, at + 6)
                if length < 16 or at + length > len(data):
                    break
                totals[op] += 1
                at += length
    print('  %s: %d .ecl files, %d opcode words, %d distinct numbers'
          % (title, files, sum(totals.values()), len(totals)))
    low = sorted(op for op in totals if op < 300)
    print('    below 300: %s' % ' '.join('%d:%d' % (op, totals[op]) for op in low))
    if known is not None:
        covered = set(int(k, 0) for k in known.get(title, {}).get('opcodes', {}))
        gaps = [(op, totals[op]) for op in low if op >= 256 and op not in covered]
        print('    used but not in the dispatch family: %s'
              % (' '.join('%d:%d' % pair for pair in gaps) or 'none'))
