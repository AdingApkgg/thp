#!/usr/bin/env python3
"""Pair the globals a title copies into a replay stage record with the offsets they land at.

A snapshot of the game state is a run of adjacent instruction pairs: a load (`mov reg, [global]`
or `mov reg, [runtime + disp]`) followed straight away by a store of that register into the record
(`mov [base + disp], reg`). The stream of pairs names the record's layout without ambiguity, and
because only the immediately previous load counts, a register reused later cannot leak into it.

On th12.exe the run must contain 0x4b0c44 -> +0xc, 0x4b0c48 -> +0x10 (a word: the power level),
0x4b0c98 -> +0x18 and 0x4b0c9c -> +0x1a (words), the position pair at runtime +0x988/+0x98c ->
+0x30/+0x34 and 0x4b0cd8 -> +0x3c. That is the control: the same run on another title is that
title's record layout.

Usage: th-replay-writer-exe.py <exe> [--min 8] [--limit 2]
"""
import struct
import sys

import capstone

args = sys.argv[1:]
min_pairs = 8
limit = 2
if '--min' in args:
    min_pairs = int(args[args.index('--min') + 1])
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


def load_of(instruction, md):
    """(register, description) when this instruction loads one register from memory."""
    address, mnemonic, operands = instruction
    if mnemonic != 'mov' or len(operands) != 2:
        return None
    if operands[0].type != capstone.x86.X86_OP_REG:
        return None
    source = operands[1]
    if source.type != capstone.x86.X86_OP_MEM or source.mem.index != 0:
        return None
    if source.mem.base == 0:
        return operands[0].reg, '0x%x' % source.mem.disp
    return operands[0].reg, '%s+0x%x' % (md.reg_name(source.mem.base), source.mem.disp)


def store_of(instruction, md):
    """(register, destination) when this instruction stores one register into memory."""
    address, mnemonic, operands = instruction
    if mnemonic != 'mov' or len(operands) != 2:
        return None
    destination = operands[0]
    if destination.type != capstone.x86.X86_OP_MEM or destination.mem.index != 0:
        return None
    if operands[1].type != capstone.x86.X86_OP_REG:
        return None
    where = ('%s+0x%x' % (md.reg_name(destination.mem.base), destination.mem.disp)
             if destination.mem.base else '+0x%x' % destination.mem.disp)
    return operands[1].reg, (where, destination.size)


data = open(path, 'rb').read()
rva, raw, size = code_section(data)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
instructions = []
for ins in md.disasm(data[raw:raw + size], rva):
    operands = []
    if ins.id != 0:
        try:
            operands = list(ins.operands)
        except capstone.CsError:
            operands = []
    instructions.append((ins.address, ins.mnemonic, operands))

pairs = []
for index in range(1, len(instructions)):
    loaded = load_of(instructions[index - 1], md)
    if loaded is None:
        continue
    stored = store_of(instructions[index], md)
    if stored is None or stored[0] != loaded[0]:
        continue
    where, width = stored[1]
    pairs.append((instructions[index][0], loaded[1], where, width))

print('  %s: %d adjacent load/store pairs' % (path, len(pairs)))
runs = []
for start in range(len(pairs)):
    run = [pairs[start]]
    for item in pairs[start + 1:]:
        if item[0] - run[-1][0] > 0x60:
            break
        run.append(item)
    if len(run) >= min_pairs:
        runs.append(run)

shown = 0
def absolute(pair):
    return pair[1].startswith('0x')


for run in runs:
    if '--abs' in args and sum(1 for item in run if absolute(item)) < min_pairs:
        continue
    print('  --- run from 0x%06x (%d pairs, %d from an absolute address) ---'
          % (run[0][0], len(run), sum(1 for item in run if absolute(item))))
    for address, origin, where, width in run:
        print('    0x%06x  %s (%d bytes) -> [%s]' % (address, origin, width, where))
    print()
    shown += 1
    if shown >= limit:
        break
