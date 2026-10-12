"""Which suites hand the transcribed dispatcher a context they built from the core's heap?

Section 128.4 named the audit: a suite needs a core-to-native context mirror exactly when it passes a context
that lives in the core heap, because the native body dereferences [ctx+4] and [ctx+0x100c] and a core address
is unmapped there. This tool reports, for every suite that calls the dispatcher at 0x004154d0 through touch():

  mirror   a native block written from a core context buffer  (m.write(<native>, <ctx>))
  chain    whether the suite mentions the field + 0x174c at all
  bridge   whether it imports the relocation helper
  order    where the mention of 0x174c sits relative to the last fixture write to the object

The last column is the one that matters: section 125.1 found the field overwritten by a fixture write, so a
mention that comes BEFORE the last write cannot survive.

  py -3 tools/th-context-mirror-audit.py
"""
import io
import os
import re

TESTS = os.path.join('runtimes', 'th12', 'th12_web', 'tests', 'cpp')
DISPATCHER = '0x412e30'          # the th11 address touch() maps to 0x004154d0

print('  %-34s %-8s %-7s %-8s %s' % ('suite', 'mirror', 'chain', 'bridge', 'order of the 0x174c mention'))
needing = []
for name in sorted(os.listdir(TESTS)):
    if not name.endswith('.test.mjs'):
        continue
    path = os.path.join(TESTS, name)
    text = io.open(path, encoding='utf-8').read()
    if DISPATCHER not in text:
        continue
    # 1. A native mirror: a plain identifier (not c.*) written from a buffer whose name contains ctx.
    mirrors = [m.group(1) for m in re.finditer(r'm\.write\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)\s*\)', text)
               if 'ctx' in m.group(2).lower()]
    mirrors += [m.group(1) for m in re.finditer(r'm\.write\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)\)', text)
                if 'ctx' in m.group(2).lower()]
    # 2. The field, and where it is mentioned relative to the last write that covers the object. A call to the
    # bridge counts as a mention placed at ITS call site: the offset lives inside the helper module, so a scan
    # for the literal would report the bridge as a surviving mention that cannot survive - the false negative
    # this tool produced on the one suite that had already been fixed.
    mentions = [text.count('\n', 0, m.start()) + 1 for m in re.finditer(r'0x174c', text)]
    mentions += [text.count('\n', 0, m.start()) + 1 for m in re.finditer(r'wireContextChain\s*\(', text)]
    writes = [text.count('\n', 0, m.start()) + 1 for m in re.finditer(r'm\.write\(\s*q\b|memory\(c,p,SIZE\)', text)]
    order = 'none'
    if mentions:
        last_write = max(writes) if writes else 0
        order = ('after the last fixture write' if max(mentions) > last_write
                 else 'BEFORE the last fixture write (cannot survive)')
    bridged = 'wireContextChain' in text
    print('  %-34s %-8s %-7s %-8s %s'
          % (name.replace('.test.mjs', '')[:34], (mirrors[0] if mirrors else '-'),
             ('yes' if mentions else 'no'), ('yes' if bridged else 'no'), order))
    if DISPATCHER in text and not bridged:
        needing.append((name.replace('.test.mjs', ''), bool(mirrors), order))

print('  --- suites that call the dispatcher and do not use the bridge: %d' % len(needing))
for name, has_mirror, order in needing:
    print('    %-32s mirror=%-5s %s' % (name, 'yes' if has_mirror else 'NO', order))
