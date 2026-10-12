#!/usr/bin/env python3
"""Tabulate the ANM texture records of the titles' shipped files.

Each ANM chunk holds one texture: a surface format, an embedded-image pointer, and, when the
image is embedded, a THTX block whose pixel format says how the bytes are packed. This reads
every archive of a title and counts the combinations it actually contains, so a format value the
runtime does not know is a measurement ("this title uses it, this often") rather than a guess.

Usage: th-anm-texture-table.py <data-dir> [<other-data-dir> ...]
"""
import glob
import os
import struct
import sys


def chunks(data):
    base = 0
    while True:
        if len(data) - base < 64:
            return
        stride, = struct.unpack_from('<I', data, base + 36)
        size = stride or (len(data) - base)
        yield base, data[base:base + size]
        if not stride:
            return
        base += stride


def textures(path):
    data = open(path, 'rb').read()
    if len(data) < 64 or struct.unpack_from('<I', data, 0)[0] not in (4, 7, 8):
        return
    for base, c in chunks(data):
        if len(c) < 64:
            return
        width, height, surface = struct.unpack_from('<HHH', c, 10)
        name_offset, = struct.unpack_from('<I', c, 16)
        name = c[name_offset:c.index(b'\0', name_offset)].decode('ascii', 'replace')
        has_data = c[32]
        tex, = struct.unpack_from('<I', c, 28)
        record = (os.path.basename(path), name, width, height, surface, has_data)
        if has_data and c[tex:tex + 4] == b'THTX':
            pixel_format, pixel_w, pixel_h, byte_count = struct.unpack_from('<HHHI', c, tex + 6)
            yield record + (pixel_format, pixel_w, pixel_h, byte_count)
        else:
            yield record + (None, None, None, None)


def main(dirs):
    counts = {}
    examples = {}
    for directory in dirs:
        title = os.path.basename(os.path.dirname(directory))
        for path in sorted(glob.glob(os.path.join(directory, '*.anm'))):
            for file, name, width, height, surface, has_data, pixel_format, pixel_w, pixel_h, bytes_ in textures(path):
                pieces = pixel_w * pixel_h if pixel_w else 0
                bpp = bytes_ // pieces if pieces and bytes_ % pieces == 0 else None
                key = (title, surface, has_data and 1 or 0, pixel_format, bpp)
                counts[key] = counts.get(key, 0) + 1
                examples.setdefault(key, '%s:%s %ux%u %ux%u %s' % (file, name, width, height, pixel_w or 0, pixel_h or 0, bytes_))
    print('  title  surface has_data pixel_format bytes/pixel  count  example')
    for key in sorted(counts, key=lambda k: (k[0], k[1], k[3] if k[3] is not None else -1)):
        title, surface, has_data, pixel_format, bpp = key
        print('    %-6s %-7d %-8d %-12s %-11s %-6d %s' %
              (title, surface, has_data, pixel_format, bpp, counts[key], examples[key]))


if __name__ == '__main__':
    main(sys.argv[1:])
