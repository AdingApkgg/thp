"""The validated class search: every candidate that clears the method's run criterion.

This is the instrument of section 98.7 promoted out of tools/tmp, because it is now the one that answers
the question the method asks: the table's own rows record `span`, `literals` and `run`, where `run` is the
longest stretch of the window containing no wildcard, and acceptance is **every literal byte agreeing** at
a candidate. Tools/th-shape-classes.py demanded full-window byte equality, which no row in the table meets,
and reported zero members for every input including rows known to be right for many rounds.

The wildcards come from the source window: an in-image dword is an absolute reference the port moves.
`tools/th-twin-batch.py` builds the same pattern with `pattern_and_wild`, so the two agree by construction,
and the calibration is `--at 0x401fd0` (th11) whose anchored row is 0x402520:

  py -3 tools/th-class-search.py --at 0x401fd0 --span 48        # one hit, 0x402520, 48/48
  py -3 tools/th-class-search.py --at 0x4540f0 --span 48        # the candidate row, unvalidated
"""
import argparse
import io
import importlib.util
import json
import re
import sys

import capstone

_ARGS = argparse.ArgumentParser()
_ARGS.add_argument('--source', default='H:/Games/th/11/th11.exe')
_ARGS.add_argument('--target', default='H:/Games/th/12/th12.exe')
_ARGS.add_argument('--at', required=True)
_ARGS.add_argument('--span', type=lambda text: int(text, 0), default=48)
_ARGS.add_argument('--limit', type=lambda text: int(text, 0), default=8)
_ARGS.add_argument('--quiet', action='store_true')
_OPTS = _ARGS.parse_args()

sys.path.insert(0, 'tools')
_spec = importlib.util.spec_from_file_location('tb', 'tools/th-twin-batch.py')
batch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(batch)

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

source_start, source_blob, _, _ = batch.FIND.image_text(_OPTS.source)
target_start, target_blob, _, _ = batch.FIND.image_text(_OPTS.target)

# Section 91's alignment rule: a window may only start where the sweep makes the address a boundary.
boundaries = set()
address = target_start
while address < target_start + len(target_blob):
    boundaries.add(address)
    one = next(MD.disasm(target_blob[address - target_start:address - target_start + 16], address,
                         count=1), None)
    address += one.size if one else 1


def agreement(window, wild, hit):
    """Longest run of agreeing positions, a wildcard agreeing with anything, and whether all literals do."""
    longest = run = 0
    literals_agree = True
    for index, flag in enumerate(wild):
        if flag:
            run += 1
        elif window[index] == target_blob[hit - target_start + index]:
            run += 1
        else:
            literals_agree = False
            run = 0
        longest = max(longest, run)
    return longest, literals_agree


at = int(_OPTS.at, 16)
window, wild = batch.pattern_and_wild(source_blob, at - source_start, _OPTS.span)
run = batch.literal_runs(wild)
pattern = b''.join(b'.' if flag else re.escape(bytes([byte])) for byte, flag in zip(window, wild))
hits = [match.start() + target_start for match in re.finditer(pattern, target_blob, re.DOTALL)]
scored = sorted(((agreement(window, wild, hit), hit) for hit in hits if hit in boundaries),
                key=lambda pair: (pair[0][1], pair[0][0]), reverse=True)
print('  0x%x: window %d bytes, %d wildcarded, longest literal run %d, %d boundary candidate(s)'
      % (at, _OPTS.span, sum(wild), run, len(scored)))
if not _OPTS.quiet:
    table = json.load(io.open('docs/porting/oracle-th11-th12.json', encoding='utf-8'))['rows']
    row = next((row for row in table if int(row['sourceAddress'], 16) == at), None)
    if row:
        print('    table: %s -> %s (%s)' % (row['sourceAddress'], row.get('targetAddress'),
                                            row.get('confidence')))
for (longest, literals_agree), hit in scored[:_OPTS.limit]:
    one = next(MD.disasm(target_blob[hit - target_start:hit - target_start + 16], hit, count=1), None)
    print('    0x%x  all literals %s  longest run %d/%d  %s'
          % (hit, 'agree' if literals_agree else 'DIFFER', longest, _OPTS.span,
             ('%s %s' % (one.mnemonic, one.op_str)) if one else '?'))
if not scored:
    print('    no candidate whose literal bytes all agree')
