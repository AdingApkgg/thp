"""Read every write to a flag word off the handlers of the three newer titles, not only the shift shape.

The round before read the seven handlers that write one bit by shifting the argument; that shape is a
minority. This one walks each real handler's straight path and records every instruction that writes
the title's two flag words, with the mask and where the value comes from:

    arg-bit s        the value is the argument byte's low bit, shifted to s
    arg-const m      the value is the argument byte (or a shifted copy) and the mask is m
    immediate m      the write carries the constant m
    register r       the write carries a register and this reader does not name its source

The output is docs/porting/anm-flag-writes-16-18.json, and the count that matters is how many of the
handlers the corpus already showed writing a flag word are explained here.
"""
import importlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[1]
MD = Cs(CS_ARCH_X86, CS_MODE_32)
TITLES = {13: ('0x18', '0x1c'), 14: ('0x18', '0x1c'), 16: ('0x530', '0x534'),
          17: ('0x530', '0x534'), 18: ('0x534', '0x538')}
# The registers each title's handlers are measured to address these words through, from
# tools/anm-base-registers.py, with the stack and frame pointers left out because at a small
# displacement they address a stack slot of the same shape: title 13 writes [esp + 0x18] 125 times.
# The measurement also names the three handlers in title 16 and the one each in 17 and 18 that a
# single-register restriction dropped, and the registers they use are in the sets.
VMREGS = {13: {'ebx', 'ecx', 'eax', 'edi', 'esi'},
          14: {'edi', 'ecx', 'esi', 'eax', 'ebx', 'edx'},
          16: {'ebx', 'edi', 'esi', 'ecx', 'edx'},
          17: {'esi', 'edi', 'ecx', 'ebx', 'edx'},
          18: {'ebx', 'edi', 'esi', 'ecx', 'edx'}}
# The word the whole-dispatch sweep showed beside the pair in the two older titles (section 337).
# It is read with the same walk but recorded apart, so the reconciliation over the pair keeps its
# meaning.
SECOND = {13: '0x538', 14: '0x548'}
CORPUS = {13: ['anm-native-context-all.json', 'anm-native-context.json'],
          14: ['anm-native-context-all.json', 'anm-native-context.json'],
          16: ['anm-native-all.json'],
          17: ['anm-native-all.json', 'anm-native.json'],
          18: ['anm-native-all.json', 'anm-native.json']}


def corpus_of(title):
    """The widest corpus a title has: the all-sweep where it exists, the family one otherwise."""
    for name in CORPUS[title]:
        path = ROOT / ('artifacts/th%d/%s' % (title, name))
        if path.exists():
            return path
    return None
MEM = re.compile(r'\[(\w+) \+ (0x[0-9a-f]+)\]')
IMM = re.compile(r', (0x[0-9a-f]+)$')


def loop_of(img, default):
    """The address the handler tail jumps to: the end of one dispatch, read from the default."""
    for ins in MD.disasm(img.read(default, 48), default):
        if ins.mnemonic == 'jmp' and ins.op_str.startswith('0x'):
            return int(ins.op_str, 16)
    return None


def addend(hit, slots):
    """The flag slot a [reg + disp] operand names, if any (the pair is two words wide)."""
    if hit.group(2) in slots:
        return hit.group(2)
    return None


def classify(mnemonic, slot, mask, value, pending_bit, text):
    """One flag-word write, with where its value comes from."""
    if mnemonic == 'xor' and value == 'eax' and pending_bit and 'eax' in text:
        where = pending_bit[1] if isinstance(pending_bit, tuple) else '?'
        return {'slot': slot, 'op': mnemonic, 'mask': mask.group(1) if mask else None,
                'source': 'arg-bit %s' % where, 'text': text}
    if mask:
        return {'slot': slot, 'op': mnemonic, 'mask': mask.group(1), 'source': 'immediate',
                'text': text}
    source = ('argument byte' if pending_bit == 'argument byte'
              else (pending_bit[0] + ' ' + str(pending_bit[1]) if pending_bit else 'register'))
    return {'slot': slot, 'op': mnemonic, 'mask': None,
            'source': '%s via %s' % (source, value), 'text': text}


def profile(img, entry, slots, loop, vmregs):
    """Writes to the title's flag words, following the handler's own control flow.

    The straight path of the previous round stopped at the first jump, which is often a jump into
    the shared tail (`and dword ptr [reg+0x530],0xfffffffe` and friends) or past a conditional
    branch. A work list over basic blocks walks those too, and stops where a handler stops: at the
    jump back to the dispatch loop. Without that stop the walk follows the loop itself and credits
    every later handler to this one.
    """
    writes, todo, seen, steps = [], [(entry, 0)], set(), 0
    pending_bit = None
    addr_of = {}
    while todo and len(seen) < 300 and steps < 1200:
        pc, depth = todo.pop()
        if pc in seen:
            continue
        seen.add(pc)
        block = list(MD.disasm(img.read(pc, 320), pc))
        for ins in block:
            steps += 1
            text = ins.mnemonic + ' ' + ins.op_str
            if ins.mnemonic == 'movzx' and re.search(r'\[edi(?: \+ \w+)? \+ 8\]', ins.op_str):
                pending_bit = 'argument byte'
            elif ins.mnemonic == 'shl':
                hit = IMM.search(ins.op_str)
                if hit and pending_bit:
                    pending_bit = ('arg-bit', int(hit.group(1), 16))
            hit = MEM.search(ins.op_str)
            if ins.mnemonic == 'lea' and hit:
                dest = ins.op_str.split(',')[0].strip()
                off = addend(hit, slots)
                if off and re.fullmatch(r'e[a-z]{2}', dest) and hit.group(1) in vmregs:
                    addr_of[dest] = off
            if (hit and hit.group(2) in slots and hit.group(1) in vmregs and ins.mnemonic in
                    ('mov', 'or', 'and', 'xor', 'add', 'sub')):
                mask = IMM.search(ins.op_str)
                value = ins.op_str.split(',')[0].strip()
                writes.append(classify(ins.mnemonic, hit.group(2), mask, value, pending_bit, text))
            elif (ins.mnemonic in ('mov', 'or', 'and', 'xor', 'add', 'sub')
                  and re.match(r'(?:\w+ ptr )?\[(\w+)\]', ins.op_str.split(',')[0].strip())):
                # The destination is the bare memory operand a lea set to the address of a field:
                # `mov dword ptr [eax], 0xfff0bdc1` as well as `mov dword ptr [ecx], edi`. The
                # earlier form asked for the memory at the end of the operands and so missed every
                # store whose source is an immediate, which is how the second word of titles 13 and
                # 14 is written through a shared routine (section 339).
                indirect = re.match(r'(?:\w+ ptr )?\[(\w+)\]', ins.op_str.split(',')[0].strip())
                if indirect and indirect.group(1) in addr_of:
                    mask = IMM.search(ins.op_str)
                    value = ins.op_str.split(',')[0].strip()
                    writes.append(classify(ins.mnemonic, addr_of[indirect.group(1)], mask, value,
                                          pending_bit, text + '   (pointer %s)' % indirect.group(1)))
            if ins.mnemonic == 'ret':
                break
            if ins.mnemonic == 'call' and ins.op_str.startswith('0x') and depth < 2:
                target = int(ins.op_str, 16)
                if target >= 0x401000 and target != loop:
                    todo.append((target, depth + 1))
            if ins.mnemonic.startswith('j') and ins.op_str.startswith('0x'):
                target = int(ins.op_str, 16)
                if target != loop and target >= 0x400000:
                    todo.append((target, depth))
                if ins.mnemonic == 'jmp':
                    break
    return writes


def main():
    out = {}
    only = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--title=')), '0'))
    for title, slots in TITLES.items():
        if only and title != only:
            continue
        img, table, default = importlib.import_module('th-anm-handlers').handlers(title)
        loop = loop_of(img, default)
        real = sorted(op for op, entry in table.items() if entry != default)
        rows, explained, silent = {}, [], []
        for op in real:
            found = profile(img, table[op], slots, loop, VMREGS[int(title)])
            if found:
                rows[op] = found
                explained.append(op)
            else:
                silent.append(op)
        second = {}
        if title in SECOND:
            for op in real:
                found = profile(img, table[op], (SECOND[title],), loop, VMREGS[int(title)])
                if found:
                    second[op] = found
            print('       the second word %s: %d handlers write it, forms %s'
                  % (SECOND[title], len(second),
                     dict(Counter(w['op'] for r in second.values() for w in r))))
        bySlot = Counter(w['slot'] for r in rows.values() for w in r)
        shifts = Counter(w['source'] for r in rows.values() for w in r if w['source'].startswith('arg-bit'))
        forms = Counter(w['op'] for r in rows.values() for w in r)
        print('  th%d: %d real handlers; %d write a flag word (%d do not); by slot %s'
              % (title, len(real), len(rows), len(silent), dict(bySlot)))
        print('       forms %s; argument-bit sources %s'
              % (dict(forms), dict(sorted(shifts.items(), key=lambda kv: -kv[1])[:5])))
        out[str(title)] = {'slots': list(slots), 'realHandlers': len(real), 'writers': len(rows),
                          'secondWord': SECOND.get(title), 'second': second,
                          'withoutAFlagWrite': silent, 'bySlot': dict(bySlot), 'forms': dict(forms),
                          'rows': rows}
    path = ROOT / 'docs/porting/anm-flag-writes-5-titles.json'
    path.write_text(json.dumps({'how': 'tools/anm-flag-writes.py walks each handler of a title and '
                                      'records every write to the two flag words of that title, '
                                      'whose offsets are measured - 0x18 and 0x1c in titles 13 '
                                      'and 14, 0x530 and 0x534 in 16 and 17, 0x534 and 0x538 in '
                                      '18 - with the shapes of 331 to 334: argument bit, '
                                      'immediate, register, and a write through a register a lea '
                                      'rows for the pair of a title, and for the one word a whole-dispatch sweep showed beside the '
                                      'pair in titles 13 and 14', 'titles': out},
                             indent=2) + '\n', encoding='utf-8')
    print('  wrote %s' % path.relative_to(ROOT))

    if '--against-corpus' in sys.argv:
        for title, data in out.items():
            corpus = corpus_of(int(title))
            if corpus is None:
                print('  th%s: no corpus' % title)
                continue
            cases = json.loads(corpus.read_text(encoding='utf-8'))['cases']
            moved = set()
            for case in cases:
                if case.get('fault') or 'before' not in case:
                    continue
                a, b = bytes.fromhex(case['before']), bytes.fromhex(case['context'])
                for slot in data['slots']:
                    off = int(slot, 16)
                    if int.from_bytes(a[off:off + 4], 'little') ^ int.from_bytes(
                            b[off:off + 4], 'little'):
                        moved.add(case['op'])
            code = set(int(op) for op in data['rows'])
            cases_ops = set(case['op'] for case in cases if not case.get('fault'))
            print('  th%s: the corpus moves a flag slot for %d handlers, the code read finds %d; '
                  'both %d; code only %s; corpus only %s (corpus covers %d handlers)'
                  % (title, len(moved), len(code), len(moved & code),
                     sorted(code - moved)[:6], sorted(moved - code)[:6], len(cases_ops)))


if __name__ == '__main__':
    main()
