#!/usr/bin/env python3
"""Read a title's replay record sizes out of the loader that uses them.

`Replay.hpp` gets TH12's stage-record size from th12.exe's loader, which computes the payload as
`lea edx,[eax+0xa0]` and the next record as `lea eax,[eax+ecx+0xa0]`. The same `lea` pair in
another title's loader gives that title's two offsets, which is a reading of the original rather
than an inference from files.

The scanner prints every `lea reg,[reg+imm]` with an immediate in the plausible record range from a
window around the replay cipher calls, and, when asked with --expect, says whether the known pair is
found (the control).

Usage: th-replay-sizes-exe.py <exe> [--expect 0xa0]
"""
import struct
import sys

try:
    import capstone
except ImportError:
    sys.exit('capstone is not available')


def text_section(data):
    lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    nsec, = struct.unpack_from('<H', data, lfanew + 6)
    optsize, = struct.unpack_from('<H', data, lfanew + 20)
    base = lfanew + 24 + optsize
    for index in range(nsec):
        at = base + index * 40
        name = data[at:at + 8].split(b'\0')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', data, at + 8)
        if name in ('.text', 'CODE'):
            return rva, raw, min(vsize, rawsize) or rawsize
    raise SystemExit('no code section')


def main(path, expect):
    data = open(path, 'rb').read()
    rva, raw, size = text_section(data)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    text = data[raw:raw + size]
    hits = []
    for ins in md.disasm(text, rva):
        if ins.mnemonic != 'lea' or len(ins.operands) != 2:
            continue
        dst, src = ins.operands
        if dst.type != capstone.x86.X86_OP_REG or src.type != capstone.x86.X86_OP_MEM:
            continue
        imm = src.mem.disp
        if 0x40 <= imm <= 0x200:
            hits.append((ins.address, imm, ins.op_str))
    # Group by proximity: a loader's sizes appear within a few dozen bytes of each other.
    print('  %s: %d `lea` with an immediate in 0x40..0x200' % (path, len(hits)))
    for window in range(0, len(hits)):
        address, imm, text_form = hits[window]
        near = [h for h in hits if abs(h[0] - address) <= 0x80]
        values = sorted({h[1] for h in near})
        if len(values) >= 2:
            print('    0x%06x: %s   (nearby: %s)' %
                  (address, text_form, ', '.join('0x%x' % v for v in values)))
    if expect:
        wanted = [int(v, 16) for v in expect.split(',')]
        print('  expected %s: %s' % (expect, 'present' if all(any(h[1] == w for h in hits) for w in wanted) else 'MISSING'))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    expect = None
    if '--expect' in sys.argv:
        expect = sys.argv[sys.argv.index('--expect') + 1]
    main(args[0], expect)
