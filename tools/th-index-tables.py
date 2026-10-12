#!/usr/bin/env python3
"""Find `mov reg,[absolute]; mov reg,[reg*4+absolute]` - an index into a per-character table.

Several per-title decisions are one global index into one absolute table: which portrait script a
character's dialogue uses (TH12: th12.exe 0x42013f reads [0x4b0c90] then [eax*4+0x4b2f84]), and
similar selections for the message file and the stage tables. The pattern is exact enough to scan
for, and the scanner checks itself on the pair that is already transcribed: it must report
0x42013f with the two addresses the port's comment names.

Usage: th-index-tables.py <exe> [--near 0xVAL] [--window N] [--check ADDR]
"""
import re
import struct
import sys

KEY = 0x00401000


def sections(image):
    pe = struct.unpack_from('<I', image, 0x3C)[0]
    count = struct.unpack_from('<H', image, pe + 6)[0]
    option = struct.unpack_from('<H', image, pe + 20)[0]
    base = struct.unpack_from('<I', image, pe + 24 + 28)[0]
    out = []
    for i in range(count):
        at = pe + 24 + option + i * 40
        name = image[at:at + 8].split(b'\x00')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', image, at + 8)
        out.append((name, base + rva, vsize, raw, rawsize))
    return out


def main():
    path = sys.argv[1]
    args = sys.argv[2:]
    near = int(args[args.index('--near') + 1], 0) if '--near' in args else None
    window = int(args[args.index('--window') + 1], 0) if '--window' in args else 0x40000
    check = int(args[args.index('--check') + 1], 0) if '--check' in args else None
    image = open(path, 'rb').read()
    name, base, vsize, raw, rsize = [s for s in sections(image) if s[0] == '.text'][0]
    text = image[raw:raw + rsize]

    hits = []
    for at in range(len(text) - 14):
        if text[at] != 0xA1:                                  # mov eax,[absolute]
            continue
        table = struct.unpack_from('<I', text, at + 8)[0]      # the load is five bytes, then 8B 0C 85 and the table address
        if text[at + 5:at + 8] != b'\x8b\x0c\x85':
            continue
        global_value = struct.unpack_from('<I', text, at + 1)[0]
        address = base + at
        if not (KEY < global_value < 0x800000 and KEY < table < 0x800000):
            continue
        if near is not None and abs(address - near) > window:
            continue
        hits.append((address, global_value, table))
    print('  %s: %d pattern occurrence(s)%s'
          % (path, len(hits), ' near 0x%x' % near if near is not None else ''))
    for address, global_value, table in hits[:20]:
        print('    0x%x  index [0x%x]  table [0x%x]' % (address, global_value, table))
    if check is not None:
        got = [h for h in hits if h[0] == check]
        print('  check: 0x%x %s' % (check, 'found %s' % (got[0],) if got else 'MISSING'))


if __name__ == '__main__':
    main()
