import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
"""Fit geometries the way the port reads the records: interval at 0x00, angle at 0x14, speed at
0x18 (ShotSpec's own offsets after the verbatim 0x1c prefix), terminator = a negative first byte.

An earlier pass read the floats at 0x10/0x14 and accepted a TH18 candidate the port then rejected;
the mismatch is why this reads the port's offsets.

  py -3 tools/tmp/sht-fit3.py
"""
import glob
import json
import math
import struct

TITLES = (14, 16, 17, 18)
STRIDES = list(range(0x40, 0xc8, 4))


def counts_of(b, groups, header, base, stride):
    n = len(b)
    if header + groups * 4 > n:
        return None
    table_end = header + groups * 4
    if base and table_end > base:
        return None
    counts = []
    for i in range(groups):
        rel = struct.unpack_from('<I', b, header + i * 4)[0]
        off = rel + base
        if off < table_end or off >= n:
            return None
        specs = 0
        while True:
            if off >= n:
                return None
            if struct.unpack_from('<b', b, off)[0] < 0:
                break
            if n - off < stride:
                return None
            interval = struct.unpack_from('<b', b, off)[0]
            angle, speed = struct.unpack_from('<ff', b, off + 0x14)
            if not (interval > 0 and math.isfinite(angle) and math.isfinite(speed)):
                return None
            specs += 1
            if specs > 400:
                return None
            off += stride
        counts.append(specs)
    return counts


def ladder(counts, levels):
    """A sheet is `levels` unfocused groups then the same focused; both halves climb by level."""
    if len(counts) != 2 * levels:
        return False
    a, c = counts[:levels], counts[levels:]
    return all(a[i] <= a[i + 1] for i in range(levels - 1)) and \
           all(c[i] <= c[i + 1] for i in range(levels - 1))


out = {}
for t in TITLES:
    path = sorted(glob.glob('artifacts/th12/sht-dump/th%d/*.sht' % t))[0]
    b = open(path, 'rb').read()
    version, groups = struct.unpack_from('<HH', b, 0)
    levels = groups // 2
    hits = []
    for header in range(0x80, 0x300, 4):
        bases = [header + groups * 4, 0] + list(range(0x100, 0x240, 4))
        for base in bases:
            for stride in STRIDES:
                counts = counts_of(b, groups, header, base, stride)
                if counts and ladder(counts, levels):
                    hits.append((len(set(counts)), sum(counts), header, base, stride, counts))
    hits.sort(key=lambda h: (-h[0], -h[1]))
    out['th%d' % t] = {'file': path.split('\\')[-1], 'groups': groups, 'fits': len(hits),
                       'top': [{'distinct': h[0], 'specs': h[1], 'header': h[2], 'base': h[3],
                                'stride': h[4], 'counts': h[5]} for h in hits[:3]]}
    print('  th%-3d v%u groups=%-3d ladder fits in the space: %d' % (t, version, groups, len(hits)))
    for h in hits[:3]:
        print('      distinct=%-3d specs=%-4d header=0x%-3x base=0x%-3x stride=0x%x counts=%s'
              % (h[0], h[1], h[2], h[3], h[4], h[5][:8]))

json.dump({'method': 'tools/tmp/sht-fit3.py: terminator plus structural specs at the port\'s own '
                     'offsets, and the two-half ladder a sheet\'s power levels give',
           'reading': 'TH14 is the control; the other rows are what the title\'s own sheet fits',
           'titles': out},
          open('docs/porting/sht-geometry.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
