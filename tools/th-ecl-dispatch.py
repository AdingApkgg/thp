#!/usr/bin/env python3
"""Resolve a shipped title's ECL dispatch table to one handler address per opcode, from the bytes.

The dispatcher is two tables and four instructions (th13.exe 0x41b2ae..0x41b2d6):

    0x41b2ae  movzx ecx, word ptr [ebx+4]      ; the ECL record's opcode word
    0x41b2b5  add   edx, -0x12C                ; first opcode of the family
    0x41b2c3  cmp   edx, 0x2BF                ; one past the last
    0x41b2cf  movzx edx, byte ptr [edx+GROUP] ; opcode -> group byte
    0x41b2d6  jmp   dword ptr [edx*4+JUMP]    ; group -> handler, absolute VA

Reading both tables is the whole mapping, and it is per title. `tools/ecl-dispatches.json` and
`docs/porting/opcode-handlers.json` record the same tables; this resolves them independently, so a
claim about what a title gives an opcode does not rest on the artifact alone.

Usage: th-ecl-dispatch.py <title> [opcode ...]
"""
import json
import struct
import sys

EXES = {'th12': 'H:/Games/th/12/th12.exe', 'th13': 'H:/Games/th/13/th13.exe',
        'th14': 'H:/Games/th/14/th14.exe', 'th16': 'H:/Games/th/16/th16.exe',
        'th17': 'H:/Games/th/17/th17.exe', 'th18': 'H:/Games/th/18/th18.exe'}

shipped = json.load(open('tools/ecl-dispatches.json'))
title = sys.argv[1]
want = [int(a, 0) for a in sys.argv[2:]]
entry = shipped[title]
image = open(EXES[title], 'rb').read()

pe = struct.unpack_from('<I', image, 0x3C)[0]
count, = struct.unpack_from('<H', image, pe + 6)
optional = struct.unpack_from('<H', image, pe + 20)[0]
image_base, = struct.unpack_from('<I', image, pe + 24 + 28)
sections = []
for i in range(count):
    at = pe + 24 + optional + i * 40
    virtual_size, virtual, raw_size, raw = struct.unpack_from('<IIII', image, at + 8)
    sections.append((image_base + virtual, virtual_size, raw, raw_size))


def raw_at(va, size):
    for base, vsize, raw, rsize in sections:
        if base <= va < base + max(vsize, rsize):
            off = raw + (va - base)
            return image[off:off + size]
    raise SystemExit('0x%x not mapped' % va)


group_table = int(entry['group'], 0)
jump_table = int(entry['jump'], 0)
first = int(entry['first'])
bound = int(entry['bound'])
groups = raw_at(group_table, bound - first)
addresses = struct.unpack_from('<%dI' % entry['targets'], raw_at(jump_table, 4 * entry['targets']), 0)

resolved = {}
for opcode in range(first, bound):
    group = groups[opcode - first]
    if group < len(addresses):
        resolved[opcode] = addresses[group]

artifact = {int(k, 0): int(v, 0) for k, v in
            json.load(open('docs/porting/opcode-handlers.json'))[title]['opcodes'].items()}
agreed = sum(1 for op, target in resolved.items() if artifact.get(op) == target)
disagreed = [op for op, target in resolved.items() if op in artifact and artifact[op] != target]
print('  %s: %d opcodes %d..%d -> %d handlers; only-here=%d; plain-artifact=%s'
      % (title, len(resolved), first, bound - 1, len(set(resolved.values())), len(set(resolved) - set(artifact)),
         'agree' if not disagreed else '%d differ (%s)' % (len(disagreed), ' '.join(hex(o) for o in disagreed[:6]))))
print('  artifact agrees on %d of %d overlapping opcodes' % (agreed, len(set(resolved) & set(artifact))))

if want:
    for opcode in want:
        if not first <= opcode < bound:
            print('  0x%x -> out of family' % opcode);continue
        print('  0x%x -> group %d -> %s' % (opcode, groups[opcode - first],
                                            hex(resolved.get(opcode, 0)) if opcode in resolved else 'out of family'))
else:
    for opcode in (first, first + 21, 0x1f6, 0x141):
        if first <= opcode < bound:
            group = groups[opcode - first]
            print('  0x%x -> group %d -> 0x%x' % (opcode, group, addresses[group]))
