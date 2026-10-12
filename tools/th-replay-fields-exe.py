#!/usr/bin/env python3
"""Find the code that reads (or writes) a replay stage record's scalar fields.

The replay's fixed record holds a seed, a score, a power level, point value, lives, fragments,
rank, continues, extends, the spawn position, focus and weapon selectors and twenty spell times.
`Replay.cpp` carries TH12's offsets, and a title with a larger record (TH13's is 0xC4 bytes
against 0xA0) is expected to keep them somewhere else.

The fields are small: the reads are `movzx`/`movsx`/`mov` against `[reg + disp]` with a
displacement of a few dozen bytes, and they come in runs - one run per routine that touches a
record. This scanner prints those runs and the displacements in the order the code uses them, so a
routine's field order can be compared with TH12's known one. Run it on th12.exe first: the run
that holds 2, 4, 8, 12, 16, 20, 24, 26, 28, 32, 36, 48, 52, 56, 60, 64 is the control.

Usage: th-replay-fields-exe.py <exe>
"""
import struct
import sys

import capstone

DISP_MAX = 0x60
RUN_GAP = 0x40
RUN_MIN = 6
FIELDS = set(range(0, DISP_MAX + 1))


def code_section(data):
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


def main(path):
    data = open(path, 'rb').read()
    rva, raw, size = code_section(data)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    hits = []
    for ins in md.disasm(data[raw:raw + size], rva):
        if ins.mnemonic not in ('mov', 'movzx', 'movsx', 'cmp'):
            continue
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and 0 <= op.mem.disp <= DISP_MAX:
                width = op.size
                if width in (1, 2, 4):
                    hits.append((ins.address, ins.mnemonic, op.mem.disp, width, op.mem.base))
                break
    runs = []
    for hit in hits:
        if runs and hit[0] - runs[-1][-1][0] <= RUN_GAP:
            runs[-1].append(hit)
        else:
            runs.append([hit])
    print('  %s: %d field-shaped accesses in %d runs' % (path, len(hits), len(runs)))
    for run in runs:
        if len(run) < RUN_MIN:
            continue
        disps = [h[2] for h in run]
        if len(set(disps)) < 5:
            continue
        print('  --- 0x%06x..0x%06x (%d accesses) ---' % (run[0][0], run[-1][0], len(run)))
        print('      disps: %s' % ' '.join('%d' % d for d in disps))
        print('      first: %s' % '; '.join('0x%x %s[%d]' % (h[0], h[1], h[2]) for h in run[:8]))


if __name__ == '__main__':
    main(sys.argv[1])
