"""Read the flag-row idiom straight out of the newer titles' handlers, without Unicorn.

The handlers that write one flag bit share one instruction shape:

    movzx eax, byte ptr [edi + 8]      the argument byte of the instruction
    shl   eax, s                       s = the bit of the flag word
    xor   eax, dword ptr [reg + slot]  slot = the flag word of this title
    and   eax, mask                    mask = 1 << s, so the write is the bit and nothing else
    xor   dword ptr [reg + slot], eax  the write itself, in the tail

Reading s and slot off the code gives each title its own row, and comparing the three titles asks a
question that can fail: is the difference between two of these titles one constant pair? It holds for
the two rows the corpus already showed (title 17 = title 16, title 18 at slot + 4 and bit + 2) or
it does not, and either answer is usable. The output is written to
docs/porting/anm-flag-rows-16-18.json.
"""
import importlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[1]
MD = Cs(CS_ARCH_X86, CS_MODE_32)
TITLES = (16, 17, 18)


def idiom(img, entry):
    """The first flag-bit write in a handler: {slot, shift, mask} or None."""
    load = re.compile(r'\[edi(?: \+ \w+)? \+ 8\]')
    memory = re.compile(r'\[(\w+) \+ (0x[0-9a-f]+)\]')
    seen_load = shift = slot = None
    for i, ins in enumerate(MD.disasm(img.read(entry, 96), entry)):
        if i > 24 or ins.mnemonic in ('jmp', 'ret'):
            break
        if ins.mnemonic == 'movzx' and load.search(ins.op_str) and 'eax' in ins.op_str:
            seen_load = True
        elif seen_load and ins.mnemonic == 'shl' and shift is None:
            hit = re.search(r', (0x[0-9a-f]+|\d+)$', ins.op_str)
            shift = int(hit.group(1), 16) if hit else None
        elif seen_load and ins.mnemonic == 'xor' and 'eax' in ins.op_str and ins.op_str.count('eax') == 1:
            hit = memory.search(ins.op_str)
            if hit:
                slot = hit.group(2)
        elif seen_load and ins.mnemonic == 'and' and 'eax' in ins.op_str:
            hit = re.search(r', (0x[0-9a-f]+)$', ins.op_str)
            if hit and slot and shift is not None:
                return {'slot': slot, 'shift': shift, 'mask': hit.group(1), 'at': hex(ins.address)}
    return None


def read_title(title):
    img, table, default = importlib.import_module('th-anm-handlers').handlers(title)
    rows, missing = {}, []
    for op in sorted(op for op, entry in table.items() if entry != default):
        found = idiom(img, table[op])
        if found and found['slot'] and found['mask']:
            rows[op] = {'slot': found['slot'], 'shift': found['shift'],
                        'mask': found['mask'], 'handler': hex(table[op])}
        else:
            missing.append(op)
    return rows, missing, len(table)


def main():
    per, missing, entries = {}, {}, {}
    for title in TITLES:
        rows, miss, count = read_title(title)
        per[title], missing[title], entries[title] = rows, miss, count
        shapes = Counter(r['mask'] for r in rows.values())
        print('  th%d: %d of %d entries; %d handlers carry the flag idiom; %d do not'
              % (title, count, count, len(rows), len(miss)))
        print('       masks seen (mask = 1 << shift): %s'
              % ', '.join('%s x%d' % (m, n) for m, n in sorted(shapes.items())[:8]))
    base = per[16]
    for title in (17, 18):
        shifts, slots, both, ok = Counter(), Counter(), 0, 0
        for op, row in per[title].items():
            if op not in base:
                continue
            both += 1
            shifts[int(row['shift']) - int(base[op]['shift'])] += 1
            slots[int(row['slot'], 16) - int(base[op]['slot'], 16)] += 1
            expect_mask = 1 << int(row['shift'])
            if int(row['mask'], 16) == expect_mask:
                ok += 1
        print('  th%d against th16, on %d shared names: bit differences %s; slot differences %s; '
              'mask is 1<<shift for %d' % (title, both, dict(shifts), dict(slots), ok))
    shared = sorted(set(per[16]) & set(per[17]) & set(per[18]))
    print('  names in all three: %d' % len(shared))
    moved = [(op, per[16][op], per[17][op], per[18][op]) for op in shared
             if per[16][op] != per[17][op] or per[16][op] != per[18][op]]
    print('  names where the three titles do not agree: %d of %d' % (len(moved), len(shared)))
    for op, a, b, c in moved[:10]:
        print('    %-4d 16 slot %s bit %s | 17 slot %s bit %s | 18 slot %s bit %s'
              % (op, a['slot'], a['shift'], b['slot'], b['shift'], c['slot'], c['shift']))
    out = ROOT / 'docs/porting/anm-flag-rows-16-18.json'
    differences = {}
    for t in (17, 18):
        shared_names = [op for op in per[t] if op in base]
        differences[str(t)] = {
            'namesShared': len(shared_names),
            'bitDifferences': dict(Counter(int(per[t][op]['shift']) - int(base[op]['shift'])
                                          for op in shared_names)),
            'slotDifferences': dict(Counter(int(per[t][op]['slot'], 16) - int(base[op]['slot'], 16)
                                           for op in shared_names))}
    out.write_text(json.dumps({
        'how': 'tools/anm-newer-flag-rows.py reads the movzx/shl/xor/and idiom off each handler',
        'titles': {str(t): {'entries': entries[t], 'rows': {str(op): r for op, r in per[t].items()},
                            'without': missing[t]} for t in TITLES},
        'differenceFromTitle16': differences,
        'namesInAllThree': len(shared),
        'namesDisagreeing': len(moved)}, indent=2) + '\n', encoding='utf-8')
    print('  wrote %s' % out.relative_to(ROOT))
    if '--against-corpus' in sys.argv:
        corpora = {16: 'anm-native-all.json', 17: 'anm-native.json', 18: 'anm-native.json'}
        total = exact = covered = 0
        detail = []
        for title in TITLES:
            corpus = ROOT / ('artifacts/th%d/%s' % (title, corpora[title]))
            if not corpus.exists():
                detail.append('th%d: no corpus' % title)
                continue
            cases = json.loads(corpus.read_text(encoding='utf-8'))['cases']
            for op, row in per[title].items():
                slot = int(row['slot'], 16)
                code = int(row['mask'], 16)
                deltas = set()
                for case in cases:
                    if case.get('op') != op or case.get('fault') or 'before' not in case:
                        continue
                    a = bytes.fromhex(case['before'])
                    b = bytes.fromhex(case['context'])
                    moved = int.from_bytes(a[slot:slot + 4], 'little') ^ int.from_bytes(
                        b[slot:slot + 4], 'little')
                    if moved:
                        deltas.add(moved)
                union = 0
                for d in deltas:
                    union |= d
                total += 1
                hits = 'exact' if code in deltas else ('covered' if union & code == code and code
                                                      and all(union & (1 << bit)
                                                              for bit in range(32)
                                                              if code >> bit & 1) else 'missing')
                if hits == 'exact':
                    exact += 1
                if hits in ('exact', 'covered'):
                    covered += 1
                else:
                    detail.append('th%d op %d: code %#x not observed in the corpus (%s)'
                                 % (title, op, code, sorted(hex(d) for d in deltas)[:4]))
        print('  cross-instrument check over %d rows read from code: every bit of the mask is '
              'observed for %d, the mask exactly for %d' % (total, covered, exact))
        for line in detail[:8]:
            print('    ' + line)


if __name__ == '__main__':
    main()
