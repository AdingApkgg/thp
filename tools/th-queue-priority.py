"""Prioritise the displacement queue: which flagged suites are currently FAILING?

Reads the output of tools/th-derived-args.py on stdin and the committed census verdict, then prints the flagged
sites whose suites do not pass. Schema-tolerant on purpose: the verdict is a committed artifact whose shape has
changed between rounds, so it looks for anything that names a suite and carries a status.

  py -3 tools/th-derived-args.py | py -3 tools/th-queue-priority.py
"""
import io
import json
import re
import sys

VERDICT = 'docs/porting/census-th12.json'

lines = sys.stdin.read().split('\n')
flagged = {}          # suite -> list of "0xADDR disp base<-origin"
for line in lines:
    match = re.match(r'\s*(0x[0-9a-f]{8})\s+(\S+)\s+base=(\S+?)\s+disp=(\S+)', line)
    if match:
        continue
    match = re.match(r'\s*(0x[0-9a-f]{8})\s+(.*?)\s+base=(\S+?)<-(\S+?)\s+disp=(\S+)', line)
    if match:
        target, suites, base, origin, disp = match.groups()
        for name in suites.split(','):
            name = name.strip()
            if name and name not in ('targets',):
                flagged.setdefault(name, []).append('%s %s<-%s %s' % (target, base, origin, disp))
        continue
    match = re.match(r'\s*sites:\s*(.*)', line)
    if match:
        for item in match.group(1).split(','):
            item = item.strip().replace(' ...', '')
            if ':' in item:
                name = item.split(':')[0].strip()
                if name:
                    flagged.setdefault(name, []).append('site ' + item)
print('  flagged suite names: %d -> %s' % (len(flagged), ', '.join(sorted(flagged))))

document = json.load(io.open(VERDICT, encoding='utf-8'))


def walk(node, path=''):
    """Yield (path, dict) for every dict that carries a string that matches a flagged suite name."""
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            for item in walk(value, path + '/' + str(key)):
                yield item
    elif isinstance(node, list):
        for index, value in enumerate(node):
            for item in walk(value, path + '[%d]' % index):
                yield item


status = {}
for path, node in walk(document):
    for key, value in node.items():
        if not isinstance(value, str):
            continue
        base = value[:-3] if value.endswith('.mjs') else value
        base = base[:-9] if base.endswith('.test') else base
        if base in flagged or value.replace('.test.mjs', '') in flagged:
            name = value.replace('.test.mjs', '')
            # The verdict rows carry `pass` and `fail`; the first version of this script looked for
            # passed/status/result and therefore classified EVERY flagged suite as unknown, which printed the
            # reassuring and false line "flagged AND failing: 0".
            passes = node.get('pass', node.get('passed', node.get('status')))
            fails = node.get('fail')
            state = 'pass=%s fail=%s' % (passes, fails)
            failing_here = (fails not in (None, 0, False)) or (passes in (0, False))
            status.setdefault(name, []).append((state, failing_here, path))
print('  flagged suites found in the verdict: %d' % len(status))
failing = []
for name in sorted(status):
    entries = status[name]
    if any(flag for _, flag, _ in entries):
        failing.append((name, entries[0][0], flagged.get(name, [])[:3]))
print('  --- flagged AND failing (the queue in priority order): %d' % len(failing))
for name, state, sites in failing:
    print('    %-32s %-28s %s' % (name, state, ' ; '.join(sites)))
passing = [name for name in sorted(status) if name not in {f[0] for f in failing}]
print('  flagged but passing: %d -> %s' % (len(passing), ', '.join(passing[:8])))
if not status:
    print('  VERDICT KEYS: %s' % sorted(document)[:12])
