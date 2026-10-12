#!/usr/bin/env python3
"""Disassemble a virtual-address window of a shipped executable, with a correct section mapping.

`tools/tmp/th-dis-region.py` reads `raw + (va - section_rva)` as a file offset, which drops the
image base: for a VA in the middle of an executable it lands past the end of the file and prints
nothing. That silent empty result was the reason the TH13 dispatcher looked empty.

This maps the VA through the section table properly and prints the bytes, so a claim like "the
dispatcher reads the opcode and indexes a 403-entry table" comes with the instructions that say it.

Usage: th-code-region.py <exe> <va> <length> [--raw]
"""
import struct
import sys

args = sys.argv[1:]
show_raw = '--raw' in args
if show_raw:
    args.remove('--raw')
path, start, length = args[0], int(args[1], 0), int(args[2], 0)

import capstone  # imported after argument parsing so --help is cheap

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


def offset_of(va):
    for name, base, size, raw, raw_size in sections:
        if base <= va < base + max(size, raw_size):
            return raw + (va - base)
    return None


offset = offset_of(start)
if offset is None:
    sys.exit('0x%x is not inside any section of %s' % (start, path))
print('%s  0x%x..0x%x  (%d sections, image base 0x%x)'
      % (path, start, start + length, count, image_base))
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
for instruction in md.disasm(image[offset:offset + length], start):
    if show_raw:
        raw = image[offset + (instruction.address - start):offset + (instruction.address - start) + instruction.size]
        print('  0x%06x  %-32s ; %s' % (instruction.address,
                                        instruction.mnemonic + ' ' + instruction.op_str,
                                        ' '.join('%02x' % b for b in raw)))
    else:
        print('  0x%06x  %s' % (instruction.address, instruction.mnemonic + ' ' + instruction.op_str))
