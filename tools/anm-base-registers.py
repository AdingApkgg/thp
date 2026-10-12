"""Which registers does a title's handlers use to address its flag words?

The write reader of section 333 walks a handler and matches a displacement against the flag slots.
Section 338 restricted that match to the register measured for the title, which is right where the
displacement is small - 0x18 collides with the stack slot [esp + 0x18] - but it cost three handlers
in title 16, so the restriction has to be the measured set of registers a title uses, not the one
register an anchor happened to use.

This tool measures that set: it walks every real handler of a title with no base restriction and
tallies the register each write to a flag slot is addressed through, reading the base out of the
instruction text. The output is the table the reader should carry.

Usage: py -3 tools/anm-base-registers.py --title=16
"""
import importlib
import re
import sys
from collections import Counter, defaultdict

importlib.import_module('th-anm-handlers')
ROOT_TOOL = importlib.import_module('anm-flag-writes')
EVERY = {'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp'}
BASEOF = re.compile(r'\[(\w+) \+ (0x[0-9a-f]+)\]')


def main():
    only = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--title=')), '0'))
    for title, slots in ROOT_TOOL.TITLES.items():
        if only and title != only:
            continue
        img, table, default = importlib.import_module('th-anm-handlers').handlers(title)
        loop = ROOT_TOOL.loop_of(img, default)
        per_slot, odd = defaultdict(Counter), defaultdict(set)
        for op, entry in sorted(table.items()):
            if entry == default:
                continue
            for row in ROOT_TOOL.profile(img, entry, slots, loop, EVERY):
                hit = BASEOF.search(row['text'])
                if not hit:
                    continue
                base, slot = hit.group(1), hit.group(2)
                per_slot[slot][base] += 1
                if base not in ROOT_TOOL.VMREGS[title]:
                    odd[slot].add(op)
        print('  th%d %s' % (title, ' '.join('%s -> %s' % (slot, dict(per_slot[slot]))
                                             for slot in sorted(per_slot))))
        wish = [int(v) for a in sys.argv if a.startswith('--ops=') for v in
                a.split('=')[1].split(',')]
        for op in wish:
            entry = table.get(op)
            if entry is None or entry == default:
                continue
            bases = Counter()
            for row in ROOT_TOOL.profile(img, entry, slots, loop, EVERY):
                hit = BASEOF.search(row['text'])
                if hit:
                    bases[hit.group(1)] += 1
            print('     op %-4d %#x addresses them through %s'
                  % (op, entry, dict(bases)))
        for slot in sorted(odd):
            print('     %s reached through a register outside the carried table by ops %s'
                  % (slot, sorted(odd[slot])))


if __name__ == '__main__':
    main()
