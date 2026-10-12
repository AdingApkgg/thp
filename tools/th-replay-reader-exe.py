#!/usr/bin/env python3
"""Find the routine that consumes a replay stage record, and print the field order it uses.

`Replay.cpp` carries TH12's record offsets (seed +2, score +0xc, power +0x10, points +0x14,
lives +0x18, fragments +0x1a, rank +0x1c, continues +0x20, extends +0x24, spawn x +0x30, y +0x34,
focused +0x38, graze +0x3c, weapon +0x40). A routine that reads a record touches one register base
many times at small, distinct displacements with mixed widths, and it does so in a run.

This scanner groups memory operands by base register inside a sliding window and prints the windows
where one base is used at least `--min` times at three or more distinct small displacements, with
the displacements in the order the instructions use them. Run against th12.exe first: the window
whose displacements are the set above is the control.

Usage: th-replay-reader-exe.py <exe> [--min 6] [--window 60] [--limit 4]
"""
import struct
import sys

import capstone

args = sys.argv[1:]
min_hits = 6
window = 60
limit = 4
if '--min' in args:
    min_hits = int(args[args.index('--min') + 1])
if '--window' in args:
    window = int(args[args.index('--window') + 1])
if '--limit' in args:
    limit = int(args[args.index('--limit') + 1])
path = args[0]


def code_section(data):
    lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    nsec, = struct.unpack_from('<H', data, lfanew + 6)
    optsize, = struct.unpack_from('<H', data, lfanew + 20)
    base = lfanew + 24 + optsize
    for index in range(nsec):
        at = base + index * 40
        name = data[at:at + 8].split(b'\0')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', data, at + 8)
        if name in ('.text', 'CODE'):
            return rva, raw, min(vsize, rawsize) or rawsize
    raise SystemExit('no code section')


data = open(path, 'rb').read()
rva, raw, size = code_section(data)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
rows = []
for ins in md.disasm(data[raw:raw + size], rva):
    access = None
    if ins.id != 0 and ins.mnemonic in ('mov', 'movzx', 'movsx', 'cmp', 'add', 'sub'):
        try:
            for op in ins.operands:
                if (op.type == capstone.x86.X86_OP_MEM and 0 <= op.mem.disp <= 0x60
                        and op.mem.index == 0):
                    access = (op.mem.base, op.mem.disp, op.size)
                    break
        except capstone.CsError:
            access = None
    rows.append((ins.address, ins.mnemonic + ' ' + ins.op_str, access))

print('  %s: %d instructions, %d with a small-displacement memory operand'
      % (path, len(rows), sum(1 for r in rows if r[2])))
found = []
for start in range(0, len(rows), 10):
    chunk = rows[start:start + window]
    for base, _, _ in [r[2] for r in chunk if r[2]]:
        hits = [(r[0], r[2][1], r[2][2]) for r in chunk if r[2] and r[2][0] == base]
        disps = {h[1] for h in hits}
        if len(hits) >= min_hits and len(disps) >= max(4, min_hits - 2):
            entry = (chunk[0][0], base, tuple(h[1] for h in hits))
            if not any(abs(entry[0] - e[0]) < window and entry[1] == e[1] for e in found):
                found.append(entry)
for address, base, disps in found[:limit]:
    print('  --- window at 0x%06x, base %s, %d distinct disps ---' % (address, base, len(set(disps))))
    print('      order: %s' % ' '.join('0x%x' % d for d in disps))
