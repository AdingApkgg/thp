#!/usr/bin/env python3
"""Check a ring log against the executable ranges of the shipped image.

Section 284 asked for this check and section 285 used it: of 65,242 ring entries in two suite logs, zero were
outside the executable ranges, and the one entry a size-1 ring kept (0xbb40e64e, a cookie seed) was the
reason the check exists at all. Usage: `py -3 tools/th-ring-check.py <log> [<log> ...]`; exit status 1 when
any recorded pc cannot be executed.

The image path and the loader base are the same two constants tools/th-interior-calls.py uses.
"""
import io
import re
import struct
import sys

IMAGE = 'H:/Games/th/12/th12.exe'
IMAGE_BASE = 0x400000


def executable_ranges(blob):
    """Every section whose IMAGE_SCN_MEM_EXECUTE is set, as (name, low, high, executable)."""
    pe = struct.unpack_from('<I', blob, 0x3c)[0]
    count = struct.unpack_from('<H', blob, pe + 6)[0]
    header = struct.unpack_from('<H', blob, pe + 20)[0]
    out = []
    for index in range(count):
        offset = pe + 24 + header + index * 40
        name = blob[offset:offset + 8].rstrip(b'\x00').decode('latin1')
        virtual, rva, raw, rawptr = struct.unpack_from('<IIII', blob, offset + 8)
        characteristics = struct.unpack_from('<I', blob, offset + 36)[0]
        low = IMAGE_BASE + rva
        high = low + max(raw, virtual)
        out.append((name, low, high, bool(characteristics & 0x20000000)))
    return out


def main(paths):
    blob = open(IMAGE, 'rb').read()
    ranges = [r for r in executable_ranges(blob) if r[3]]
    if not ranges:
        print('  no executable section in the image: the check cannot say anything')
        return 1
    total = windows = bad = 0
    for path in paths:
        text = io.open(path, encoding='utf-8', errors='replace').read()
        for entry, payload in re.findall(r'eip-ring-call (0x[0-9a-fA-F]+) (.*)', text):
            windows += 1
            for element in payload.split(' | '):
                match = re.match(r'0x([0-9a-fA-F]+)\s', element)
                if not match:
                    continue
                value = int(match.group(1), 16)
                total += 1
                if not any(low <= value < high for _, low, high, _exec in ranges):
                    bad += 1
                    if bad <= 6:
                        print('  NOT EXECUTABLE %#010x in %s' % (value, path))
    print('  ring entries: %d in %d windows; outside the executable ranges: %d' % (total, windows, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
