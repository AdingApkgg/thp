#!/usr/bin/env python3
"""Write the section ranges of an original image, so a translator can reject an impossible target.

A row in the address tables claims that one title's address has a counterpart in another. Nothing about
a bare number says whether it could be an address at all, and the translator's only sanity check was
`target < 0x10000000`, which admits 0x01035c8d - a value recorded once by a search that had no site to
support it, and applied since. The image itself knows better: an address is possible only inside one of
its sections. This tool writes those ranges.

Usage: th-image-sections.py <image.exe> <out.json> [--title th12]
"""
import io
import json
import struct
import sys


def sections(data):
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    header = struct.unpack_from('<H', data, pe + 20)[0]
    rows = []
    for index in range(count):
        offset = pe + 24 + header + index * 40
        name = data[offset:offset + 8].rstrip(b'\x00').decode('latin1')
        virtual_size, va, raw_size, raw = struct.unpack_from('<IIII', data, offset + 8)
        if not virtual_size:
            continue
        rows.append({'name': name, 'va': 0x400000 + va,
                     'size': max(virtual_size, raw_size), 'raw': raw_size})
    return rows


def main():
    image, out = sys.argv[1], sys.argv[2]
    title = sys.argv[sys.argv.index('--title') + 1] if '--title' in sys.argv else 'th12'
    data = io.open(image, 'rb').read()
    rows = sections(data)
    document = {'image': image, 'title': title, 'rows': rows}
    io.open(out, 'w', encoding='utf-8', newline='').write(
        json.dumps(document, ensure_ascii=False, indent=2).replace('\n', '\r\n'))
    for row in rows:
        print('  %-8s 0x%06x .. 0x%06x  (%d file-backed)' % (
            row['name'], row['va'], row['va'] + row['size'], row['raw']))
    low = min(row['va'] for row in rows)
    high = max(row['va'] + row['size'] for row in rows)
    print('  image window: 0x%06x .. 0x%06x' % (low, high))


main()
