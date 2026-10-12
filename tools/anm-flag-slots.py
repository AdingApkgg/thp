"""Find a title's ANM flag words from its own handlers, for any of the shipped titles.

The offsets are per title: title 16 writes flags at 0x530 and 0x534, title 18 at 0x534 and 0x538,
and titles 13 and 14 were ported before this instrument existed, so their offsets have to be read
rather than inherited. This tool walks every real handler of a title the way section 333 and 334
learned to - basic blocks, a stop at the dispatch loop, called helpers to a depth of two, and a
register a lea set to the address of a field - and counts the store instructions by displacement in
the candidate region. The flag words are the two most-written words of that region, and the count
that decides is the number of distinct handlers, not the number of instructions.

Run it on title 16 first: 0x530 and 0x534 are known there, so the tool can be checked against a
case with an answer.
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
MEM = re.compile(r'\[(\w+) \+ (0x[0-9a-f]+)\]')
ONLY = re.compile(r'\[(\w+)\]')
STORES = ('mov', 'or', 'and', 'xor', 'add', 'sub', 'movzx', 'movsx')
LO, HI = 0x400, 0x600


def loop_of(img, default):
    for ins in MD.disasm(img.read(default, 48), default):
        if ins.mnemonic == 'jmp' and ins.op_str.startswith('0x'):
            return int(ins.op_str, 16)


def vm_register(img, default):
    for ins in MD.disasm(img.read(default, 48), default):
        if ins.mnemonic == 'add' and ins.op_str.rstrip().endswith('eax'):
            hit = MEM.search(ins.op_str)
            if hit:
                return hit.group(1), int(hit.group(2), 16)
    return None, None


def write_shaped(op_str):
    """The immediate of a store, and whether its shape is a bit field (at most two bits set or
    two bits clear). The flag words are written by masks of that shape - `and ...,0xfffffffe`,
    `or ...,0x4000`, `xor ...,0x100` - while the neighbouring object fields are written whole."""
    hits = re.findall(r', (0x[0-9a-f]+)$', op_str)
    if not hits:
        return None, None
    value = int(hits[-1], 16) & 0xffffffff
    shaped = value.bit_count() <= 2 or ((~value) & 0xffffffff).bit_count() <= 2
    return value, shaped


def writes(img, entry, loop):
    """(displacement, text) for every store a handler makes in the candidate region."""
    found, todo, seen, steps = [], [(entry, 0)], set(), 0
    addr_of = {}
    while todo and len(seen) < 300 and steps < 1500:
        pc, depth = todo.pop()
        if pc in seen:
            continue
        seen.add(pc)
        for ins in MD.disasm(img.read(pc, 320), pc):
            steps += 1
            if ins.mnemonic == 'lea':
                hit = MEM.search(ins.op_str)
                dest = ins.op_str.split(',')[0].strip()
                if hit and LO <= int(hit.group(2), 16) < HI and re.fullmatch(r'e[a-z]{2}', dest):
                    addr_of[dest] = hit.group(2)
            if ins.mnemonic in STORES:
                hit = MEM.search(ins.op_str)
                target = None
                if hit:
                    # a write has the memory operand on the left of the comma, or the instruction
                    # writes its only operand (`and dword ptr [ebx+0x530], imm` has the comma but
                    # the memory is still first; `and eax, [ebx+0x530]` is a read)
                    before_comma = ins.op_str.split(',')[0]
                    reads = ins.op_str.split(',')[1] if ',' in ins.op_str else ''
                    is_memory = hit.group(0) in (before_comma if reads else ins.op_str)
                    if not reads:
                        is_memory = ins.mnemonic != 'mov' or hit.group(0) == before_comma
                    if is_memory and LO <= int(hit.group(2), 16) < HI:
                        target = (hit.group(2), ins.mnemonic + ' ' + ins.op_str)
                if target is None:
                    only = ONLY.search(ins.op_str)
                    if only and only.group(1) in addr_of:
                        target = (addr_of[only.group(1)],
                                  ins.mnemonic + ' ' + ins.op_str + '   (pointer)')
                if target:
                    found.append(target)
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
    return found


def main():
    title = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--title=')), '16'))
    img, table, default = importlib.import_module('th-anm-handlers').handlers(title)
    loop = loop_of(img, default)
    reg, position = vm_register(img, default)
    real = sorted(op for op, entry in table.items() if entry != default)
    per_slot, handlers, samples = defaultdict(Counter), Counter(), defaultdict(list)
    shaped, shaped_samples = defaultdict(set), defaultdict(list)
    for op in real:
        for disp, text in writes(img, table[op], loop):
            handlers[disp] += 1
            per_slot[disp][op] += 1
            if len(samples[disp]) < 3:
                samples[disp].append(text)
            _, is_shaped = write_shaped(text)
            if is_shaped:
                shaped[disp].add(op)
                if len(shaped_samples[disp]) < 3:
                    shaped_samples[disp].append(text)
    print('  th%d: %d real handlers, default %#x, vm register %s at position %s, loop %s'
          % (title, len(real), default, reg, hex(position) if position else None,
             hex(loop) if loop else None))
    print('  the most-written words of the 0x400 region, by distinct handlers:')
    for disp, count in handlers.most_common(12):
        print('     %s  %3d handlers  %4d instructions  e.g. %s'
              % (disp, count, sum(per_slot[disp].values()), samples[disp][0][:52]))
    pairs = [(a, handlers[a], b, handlers[b]) for a in sorted(handlers) for b in sorted(handlers)
             if int(b, 16) - int(a, 16) == 4 and handlers[a] > 4 and handlers[b] > 4]
    print('  adjacent words both written by more than four handlers: %s'
          % ', '.join('%s(%d) with %s(%d)' % p for p in pairs[:6]))
    print('  ranked by handlers writing a bit-shaped mask there - the shape of a flag word:')
    for disp, ops in sorted(shaped.items(), key=lambda kv: -len(kv[1]))[:8]:
        print('     %s  %3d handlers  %s' % (disp, len(ops), shaped_samples[disp][0][:56]))
    out = ROOT / ('docs/porting/anm-flag-slots-th%d.json' % title)
    out.write_text(json.dumps({
        'how': 'tools/anm-flag-slots.py walks the handlers and counts stores by displacement',
        'title': title, 'realHandlers': len(real), 'default': hex(default),
        'vmRegister': reg, 'positionSlot': hex(position) if position else None,
        'byHandlers': {d: handlers[d] for d, _ in handlers.most_common(20)},
        'samples': {d: samples[d] for d, _ in handlers.most_common(12)}}, indent=2) + '\n',
        encoding='utf-8')
    print('  wrote %s' % out.relative_to(ROOT))


if __name__ == '__main__':
    main()
