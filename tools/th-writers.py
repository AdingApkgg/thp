#!/usr/bin/env python3
"""Which instructions touch one absolute address: `th-writers.py <exe> <0xVA>`.

An absolute global is named by the instruction that reads or writes it, and a transcription needs
to know which of the two a site is before it can decide whether a fixture may host-write it (a
lazy allocator writes; an accessor reads). Capstone reports the memory operand's `disp` with no
base and no index for `mov eax, dword ptr [0x4ce8f0]`, so a whole-.text pass gives every site
with its mnemonic, destination and (with `--raw`) the bytes.

Usage: th-writers.py <exe> <0xVA> [--window 0x30]
"""
import struct
import sys

args = sys.argv[1:]
window = int(args[args.index('--window') + 1], 0) if '--window' in args else 0x20
path, target = args[0], int(args[1], 0)

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
    if virtual_size and raw_size:
        sections.append((name, image_base + virtual, virtual_size, raw, raw_size))

import capstone

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

sites = []
for name, base, size, raw, raw_size in sections:
    chunk = image[raw:raw + min(size, raw_size)]
    for instruction in md.disasm(chunk, base):
        try:
            operands = instruction.operands
        except capstone.CsError:      # a skipdata byte has no operands
            continue
        writes, reads = [], []
        for index, operand in enumerate(operands):
            if operand.type != capstone.x86.X86_OP_MEM:
                continue
            if operand.mem.base or operand.mem.index:
                continue
            if (operand.mem.disp & 0xffffffff) != target:
                continue
            (writes if index == 0 else reads).append(instruction.mnemonic)
        if writes or reads:
            sites.append((instruction.address, instruction.mnemonic + ' ' + instruction.op_str,
                         'write' if writes else 'read', name))

print('%s  0x%x: %d absolute site(s)' % (path, target, len(sites)))
for address, text, kind, name in sorted(sites):
    print('  %-7s 0x%06x  %s' % (kind, address, text))
    if window:
        for section in sections:
            if section[1] <= address < section[1] + max(section[2], section[4]):
                _, base, size, raw, raw_size = section
                start = max(base, address - window)
                chunk = image[raw + (start - base):raw + (start - base) + (address - start) + window]
                for instruction in md.disasm(chunk, start):
                    if instruction.address == address:
                        break
                    print('          0x%06x  %s' % (instruction.address,
                                                    instruction.mnemonic + ' ' + instruction.op_str))
                break
