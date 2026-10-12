"""Classify the committed census verdict's walls, so the next target is chosen by evidence.

The table has a wall per trapping suite: where it stopped (`at`), the address it touched, the pc of the
instruction, and the entry/call context the machine recorded. The classes this prints are not a theory of the
port; they are what the addresses say:

  import-stub     the suite reached an unimplemented host import (`at` = import)
  null-base       an unmapped read at a small absolute address, which is a zero base plus a struct offset
  garbage-base    an unmapped access at an address that is not a plausible offset, so a register holds
                  something that is not a pointer at all
  other           everything else, named rather than binned
  pinned-fault    a suite that DID NOT FAIL and produced a wall anyway - see the note below

A class is a next step only if it names something to read; the point is to stop choosing by whichever suite
was looked at last.

Section 134: a wall is only a wall if the suite failed. `th12-aim-angle` passes and produces a real trap
artifact on purpose - it calls the dispatcher with a non-reference argument and asserts that the original
faults (`fstp [eax]` on a null store at 0x419629). Counting that as a null-base wall would inflate the class
the next target is chosen from, so rows whose process exited zero are reported as `pinned-fault` instead, and
the class list is built from `wallCounted` alone.
"""
import collections
import io
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'docs/porting/census-th12.json'
d = json.load(io.open(path, encoding='utf-8'))
rows = d['rows']
classes = collections.defaultdict(list)
for row in rows:
    wall = row.get('wall')
    if not wall:
        continue
    at = wall.get('at') or '?'
    try:
        address = int(str(wall.get('address')), 16)
    except (TypeError, ValueError):
        address = None
    if not row.get('wallCounted', True):
        kind = 'pinned-fault'
    elif at == 'import':
        kind = 'import-stub'
    elif at == 'unmapped' and address is not None and address < 0x10000:
        kind = 'null-base'
    elif at == 'unmapped' and address is not None and address >= 0x10000000:
        kind = 'garbage-base'
    else:
        kind = 'other:' + at
    classes[kind].append((row['suite'], wall, row))

print('  %s: %d rows, %d with a wall, %d of them counted (the rest did not fail)'
      % (path, len(rows), sum(len(v) for v in classes.values()),
         sum(len(v) for k, v in classes.items() if k != 'pinned-fault')))
for kind, items in sorted(classes.items(), key=lambda item: -len(item[1])):
    print('  %-14s %d suites' % (kind, len(items)))
    by_pc = collections.Counter(str(item[1].get('pc')) for item in items)
    for pc, count in by_pc.most_common(4):
        shared = [item[0] for item in items if str(item[1].get('pc')) == pc][:4]
        entry = next((item[2].get('entry') for item in items if str(item[1].get('pc')) == pc), None)
        calls = next((item[2].get('calls') for item in items if str(item[1].get('pc')) == pc), None)
        print('      pc=%s x%d entry=%s calls=%s  %s' % (pc, count, entry, calls,
                                                         ', '.join(name[:20] for name in shared)))
