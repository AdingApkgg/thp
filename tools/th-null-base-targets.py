"""Rank the null-base wall sites by the suites that share them, joined to the entry's oracle row.

This is the shortlist the plan's section 114.5 asks for. Two lessons are built in: addresses are compared as
INTEGERS, never as strings, because section 113 was a false gap caused by normalizing '0x00401670' and
'0x401670' differently; and the row facts are quoted from the map rather than remembered, so a site whose
entry supplies no slots is visible as such before the next round spends time on it.
"""
import collections
import io
import json
import sys

verdict = json.load(io.open(sys.argv[1] if len(sys.argv) > 1 else 'docs/porting/census-th12.json',
                            encoding='utf-8'))
oracle = json.load(io.open('docs/porting/oracle-interior-calls.json', encoding='utf-8'))['rows']
by_address = {int(key, 16): row for key, row in oracle.items()}

sites = collections.defaultdict(list)
for row in verdict['rows']:
    wall = row.get('wall') or {}
    try:
        address = int(str(wall.get('address')), 16)
    except (TypeError, ValueError):
        continue
    if wall.get('at') != 'unmapped' or address >= 0x10000:
        continue
    entry = row.get('entry')
    entry_value = int(entry, 16) if isinstance(entry, str) else None
    sites[(wall.get('pc'), address)].append((row['suite'], entry_value))

rows = []
for (pc, address), items in sites.items():
    entry_value = next((item[1] for item in items if item[1] is not None), None)
    facts = by_address.get(entry_value)
    rows.append({
        'pc': pc, 'address': '0x%x' % address, 'suites': sorted(item[0] for item in items),
        'entry': ('0x%08x' % entry_value) if entry_value is not None else None,
        'in_map': facts is not None,
        'slots': facts.get('slots') if facts else None,
        'reserve': facts.get('frame', {}).get('stack') if facts else None,
        'saves': ' '.join(facts.get('saves') or []) if facts else None,
    })
rows.sort(key=lambda item: (-len(item['suites']), item['pc'] or ''))

print('  null-base sites: %d over %d suites' % (len(rows), sum(len(r['suites']) for r in rows)))
print('  -- by suite count, with the entry row the machine had --')
for item in rows[:12]:
    print('    %s x%d addr=%s entry=%s inMap=%s slots=%s reserve=%s saves=%s'
          % (item['pc'], len(item['suites']), item['address'], item['entry'], item['in_map'],
             item['slots'], item['reserve'], item['saves']))
    print('        %s' % ', '.join(name[:22] for name in item['suites'][:6]))
