#!/usr/bin/env python3
"""Find jump-table dispatches and the bound that guards them, so a title's VM switch can be read.

Every ZUN executable routes by number through a `cmp reg, bound` plus `jmp dword ptr [reg*4 + base]`
pair. The port already knows the ECL *command* dispatcher of each title (tools/ecl-dispatches.json),
which is the family at 0x1xx; the *bytecode* switch, which is what tells TH13's extra opcodes
(22, 23, 62, 84, 91, 93 per `th-ecl-opcode-census.py`) from TH12's, sits somewhere else and has a
bound near 0x5a.

This scans the code section, keeps every indexed `jmp`, remembers the nearest preceding `cmp reg, imm`
with the same register, and prints each pair with the targets the table points at. A candidate whose
targets all land in one code region and whose bound matches a plausible opcode range is the switch.

Usage: th-jump-tables.py <exe> [--min-bound N] [--max-bound N] [--text VA]
"""
import struct
import sys

import capstone

args = sys.argv[1:]
path = args[0]


def option(name, default):
    return int(args[args.index(name) + 1], 0) if name in args else default


min_bound, max_bound = option('--min-bound', 40), option('--max-bound', 0x200)
only_text = option('--text', 0)

image = open(path, 'rb').read()
pe = struct.unpack_from('<I', image, 0x3C)[0]
count, = struct.unpack_from('<H', image, pe + 6)
optional = struct.unpack_from('<H', image, pe + 20)[0]
image_base, = struct.unpack_from('<I', image, pe + 24 + 28)
sections = []
for i in range(count):
    at = pe + 24 + optional + i * 40
    name = image[at:at + 8].split(b'\0')[0].decode('ascii', 'replace')
    virtual_size, virtual, raw_size, raw = struct.unpack_from('<IIII', image, at + 8)
    sections.append((name, image_base + virtual, virtual_size, raw, raw_size))


def region(va):
    """The whole containing section, as (section base, bytes). The previous version returned a slice
    that started at the table and then compared `table + span` against the slice's own base, which
    rejected every table that did not start exactly at the section's first byte."""
    for name, base, vsize, raw, rsize in sections:
        if base <= va < base + max(vsize, rsize):
            return name, base, image[raw:raw + min(vsize, rsize)]
    return None, 0, b''


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
# Without data skipping, one undecodable byte stops the sweep: the same section reaches 216849
# instructions here against a handful otherwise, and a table's own zero padding is enough to stop it.
md.skipdata = True
for name, start, vsize, raw, rsize in sections:
    if name not in ('.text', 'CODE') or (only_text and start != only_text):
        continue
    blob = image[raw:raw + min(vsize, rsize)]
    last_cmp = (0, None)
    found = []
    for ins in md.disasm(blob, start):
        if ins.id == 0:
            continue
        if ins.mnemonic == 'cmp' and len(ins.operands) == 2 and ins.operands[0].type == capstone.x86.X86_OP_REG \
                and ins.operands[1].type == capstone.x86.X86_OP_IMM:
            # The guard may test the opcode while the jmp indexes a group byte read from that opcode
            # (the two-table form the ECL dispatchers use), so the register is not required to match.
            last_cmp = (ins.address, ins.operands[1].imm)
        if ins.mnemonic == 'jmp' and len(ins.operands) == 1 and ins.operands[0].type == capstone.x86.X86_OP_MEM:
            mem = ins.operands[0].mem
            if mem.index == 0 or mem.scale & (mem.scale - 1):
                continue
            where, bound = last_cmp
            if bound is None or not (min_bound <= bound <= max_bound):
                continue
            table = mem.disp
            _, base, section = region(table)
            span = (bound + 1) * 4
            if not section or table - base + span > len(section):
                continue
            entries = span // mem.scale
            targets = struct.unpack_from('<%dI' % entries, section, table - base)
            found.append((ins.address, where, bound, table, targets, entries))
    for address, where, bound, table, targets, entries in found:
        low, high = min(targets), max(targets)
        print('  0x%06x jmp [reg*s+0x%x]  bound %d at 0x%x -> %d entries, targets 0x%x..0x%x (%d distinct)'
              % (address, table, bound, where, entries, low, high, len(set(targets))))
