import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
"""Walk a dumped sheet's structure in Python, on the wide layout the port uses, and report where.

  py -3 tools/tmp/sht-walk.py <file> [base] [stride]
"""
import glob
import math
import struct
import sys

HEADER = 0xe0
ENTRY = 4
BASE = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x108
STRIDE = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x58


def walk(path, base=BASE, stride=STRIDE, verbose=True):
    b = open(path, 'rb').read()
    version, groups = struct.unpack_from('<HH', b, 0)
    out = []
    end = HEADER + groups * ENTRY
    for i in range(groups):
        rel = struct.unpack_from('<I', b, HEADER + i * ENTRY)[0]
        off = rel + base
        specs = 0
        first = None
        while True:
            if off >= len(b):
                out.append((i, rel, off, specs, 'over size'))
                break
            if struct.unpack_from('<b', b, off)[0] < 0:
                out.append((i, rel, off, specs, 'clean'))
                break
            if len(b) - off < stride:
                out.append((i, rel, off, specs, 'short'))
                break
            interval, delay = struct.unpack_from('<bb', b, off)
            angle, speed = struct.unpack_from('<ff', b, off + 0x10)
            ok = interval > 0 and math.isfinite(angle) and math.isfinite(speed)
            if first is None:
                first = (interval, delay, round(angle, 3), round(speed, 3), b[off:off + 0x24].hex(' '))
            specs += 1
            off += stride
            if specs > 400:
                out.append((i, rel, off, specs, 'runaway'))
                break
    if verbose:
        print('  %s v%u groups=%d base=0x%x stride=0x%x' % (path.split('\\')[-1], version, groups,
                                                           base, stride))
        bad = [o for o in out if o[4] not in ('clean',)]
        print('    groups walked: %d, non-clean: %s' % (len(out), bad[:3]))
        total = sum(o[3] for o in out)
        print('    specs total: %d' % total)
        clean = [o for o in out if o[4] == 'clean']
        if clean:
            totals = sorted(set(o[3] for o in clean))
            print('    specs per clean group: %s' % totals)
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] != 'all':
        walk(sys.argv[1])
    else:
        for t in (14, 16, 17, 18):
            files = sorted(glob.glob('artifacts/th12/sht-dump/th%d/*.sht' % t))
            for path in files[:1]:
                walk(path)
