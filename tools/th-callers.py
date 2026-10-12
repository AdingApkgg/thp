"""Every direct caller of an address, as a self-testing instrument.

Reading a wall's chain by hand costs a round per link: a caller is found, its `ecx` is traced, the next caller
appears. This does it mechanically - it parses the PE section table for the VA/file-offset map, then scans the
executable section for `call rel32` whose target is the address, which is how the caller of `0x454ee0` was found
by hand in section 132.

The tool is tested against a known answer before its output is believed: `0x454ee0` was reached from `0x40a835`
and `0x428844` by hand, so both must appear in its list.

One trap, recorded because it is the same one section 122.3 hit: the section table's `VirtualAddress` is an
**RVA**, not a VA. The first version of this tool added the instruction's RVA to the section's RVA and compared
against absolute addresses, so it reported zero callers for a function with two known ones. Every address here
is an absolute VA and the image base from the optional header is added exactly once.

  py -3 tools/th-callers.py IMAGE ADDRESS [ADDRESS ...]
"""
import struct
import sys


def headers(data):
    """(image_base, [(name, rva, vsize, raw, rsize)]) from the PE headers."""
    e = struct.unpack_from('<I', data, 0x3c)[0]
    if data[e:e + 4] != b'PE\0\0':
        raise SystemExit('  not a PE file')
    count = struct.unpack_from('<H', data, e + 6)[0]
    opt = struct.unpack_from('<H', data, e + 20)[0]
    base = struct.unpack_from('<I', data, e + 24 + 0x1c)[0]
    out = []
    for i in range(count):
        o = e + 24 + opt + 40 * i
        name = data[o:o + 8].rstrip(b'\0').decode('latin-1')
        vsize, rva, rsize, raw = struct.unpack_from('<IIII', data, o + 8)
        out.append((name, rva, vsize, raw, rsize))
    return base, out


def find(image, want):
    data = open(image, 'rb').read()
    base, secs = headers(data)
    hits = []
    for name, rva, vsize, raw, rsize in secs:
        for i in range(raw, raw + rsize - 5):
            if data[i] != 0xE8:
                continue
            here = base + rva + (i - raw)
            target = here + 5 + struct.unpack_from('<i', data, i + 1)[0]
            if target == want:
                hits.append((here, name))
    return hits, base


def calls_in(image, lo, hi):
    """(site, target) for every plausible direct call whose site lies in [lo, hi).

    An E8 byte is not proof of a call: it can sit inside another instruction's operands, and this tool's first
    range listing showed both shapes of the mistake - a target computed outside the image (0x454b38 ->
    0x-17ba67cf) and a "call" into the `ret`/int3 padding that ends a function (0x45487e -> 0x454b00, which is
    a `ret`). So a target is kept only if it lies inside a section and does not begin with int3 padding.
    """
    data = open(image, 'rb').read()
    base, secs = headers(data)
    limit = base + max(rva + max(vsize, rsize) for name, rva, vsize, raw, rsize in secs)
    out = []
    for name, rva, vsize, raw, rsize in secs:
        for i in range(raw, raw + rsize - 5):
            here = base + rva + (i - raw)
            if not lo <= here < hi or data[i] != 0xE8:
                continue
            target = here + 5 + struct.unpack_from('<i', data, i + 1)[0]
            if not base <= target < limit:
                continue
            off = offset_of(secs, base, target)
            if off is None or data[off] == 0xCC:
                continue
            out.append((here, target))
    return sorted(out)


def offset_of(secs, base, va):
    for name, rva, vsize, raw, rsize in secs:
        if base + rva <= va < base + rva + rsize:
            return raw + (va - base - rva)
    return None


if len(sys.argv) < 3:
    raise SystemExit(__doc__)
image = sys.argv[1]
if sys.argv[2] == '--targets':
    found = calls_in(image, int(sys.argv[3], 16), int(sys.argv[4], 16))
    print('  direct calls sited in [0x%s, 0x%s) of %s: %d' % (sys.argv[3], sys.argv[4],
                                                              image.split('/')[-1], len(found)))
    for site, target in found:
        print('    0x%08x -> 0x%08x' % (site, target))
    raise SystemExit(0)
for arg in sys.argv[2:]:
    want = int(arg, 16)
    hits, base = find(image, want)
    print('  callers of 0x%08x in %s (image base 0x%08x): %d' % (want, image.split('/')[-1], base, len(hits)))
    for va, name in hits:
        print('    0x%08x  %s' % (va, name))
