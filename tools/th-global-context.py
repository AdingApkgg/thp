"""Measure the th12 counterpart of th11 0x4c3808 by data context, not by an emulated run.

The globals table's row came from a twin site that was not an instruction start, so the "value" it
decoded was noise. The static route is independent of any emulator: take a window of the th11 image
around the global, and find the same window in the th12 image. Globals move by a shift that has been
measured before (about +0xb660), and a match of several dozen bytes is not a coincidence, so the
address found here is evidence rather than a candidate.
"""
import io
import struct
import sys
from importlib.machinery import SourceFileLoader

FIND = SourceFileLoader('twinfind', 'tools/th-twin-find.py').load_module()


def sections(data):
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    header = struct.unpack_from('<H', data, pe + 20)[0]
    rows = []
    for index in range(count):
        offset = pe + 24 + header + index * 40
        name = data[offset:offset + 8].rstrip(b'\x00').decode(errors='replace')
        size, va, raw_size, raw = struct.unpack_from('<IIII', data, offset + 8)
        rows.append((name, va, size, raw, raw_size))
    return rows


def to_file(sections_, va):
    for name, base, size, raw, raw_size in sections_:
        if base <= va < base + max(size, raw_size):
            return raw + (va - base)
    return None


def main():
    source_address = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x4C3808
    window = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x40
    with io.open('H:/Games/th/11/th11.exe', 'rb') as handle:
        th11 = handle.read()
    with io.open('H:/Games/th/12/th12.exe', 'rb') as handle:
        th12 = handle.read()
    th11_sections, th12_sections = sections(th11), sections(th12)
    offset = to_file(th11_sections, source_address)
    needle = th11[offset:offset + window]
    print('  th11 0x%x -> file 0x%x; searching %d bytes in th12' % (source_address, offset, window))
    hits, at = [], th12.find(needle)
    while at >= 0:
        for name, base, size, raw, raw_size in th12_sections:
            if raw <= at < raw + raw_size:
                hits.append((name, base + (at - raw), at))
        at = th12.find(needle, at + 1)
    for name, va, at in hits:
        print('    match in %-8s file 0x%06x -> va 0x%06x   shift 0x%+x'
              % (name, at, va, va - source_address))
    if not hits:
        print('    no match: the windows are not byte-identical')
    # a shorter window, in case the region was edited between titles
    for length in (16, 8, 4):
        short = th11[offset:offset + length]
        found = [at for at in range(len(th12)) if th12.startswith(short, at)][:6]
        print('    %2d-byte prefix: %d hit(s)%s' % (length, len(found),
              '' if not found else ' -> file ' + ', '.join('0x%x' % f for f in found[:4])))


main()
