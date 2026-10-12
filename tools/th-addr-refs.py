#!/usr/bin/env python3
"""Find every instruction in a PE's .text that carries a given absolute address as an immediate.

Movs to and from absolute addresses embed the address literally (`A1`/`A3`/`8B 0D`/`89 15` and the
like), so searching the raw bytes for the address finds every reader and writer of a global without
decoding the whole image. Each hit prints the instruction address and the bytes around it, which is
enough to tell a load from a store and to disassemble the site with tools/th-code-region.py.

Usage: th-addr-refs.py <exe> 0x4c22dc [0x4c2188 ...]
"""
import struct
import sys


def text_section(image):
    pe = struct.unpack_from('<I', image, 0x3C)[0]
    count = struct.unpack_from('<H', image, pe + 6)[0]
    option = struct.unpack_from('<H', image, pe + 20)[0]
    base = struct.unpack_from('<I', image, pe + 24 + 28)[0]
    for index in range(count):
        at = pe + 24 + option + index * 40
        name = image[at:at + 8].split(b'\x00')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', image, at + 8)
        if name == '.text':
            return base + rva, image[raw:raw + max(vsize, rawsize)]
    raise SystemExit('no .text')


def main():
    image = open(sys.argv[1], 'rb').read()
    va, blob = text_section(image)
    for argument in sys.argv[2:]:
        value = int(argument, 0)
        needle = struct.pack('<I', value)
        hits = []
        at = blob.find(needle)
        while at >= 0:
            # the immediate sits at at; print from two bytes before it so the opcode is visible
            start = max(0, at - 2)
            hits.append((va + at, blob[start:at + 6]))
            at = blob.find(needle, at + 1)
        print('  0x%08x: %d reference(s)' % (value, len(hits)))
        for address, window in hits[:40]:
            print('    imm at 0x%x  bytes %s' % (address, ' '.join('%02x' % b for b in window)))


if __name__ == '__main__':
    main()
