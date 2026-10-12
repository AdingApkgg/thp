#!/usr/bin/env python3
"""Find a title's replay-cipher constants in its executable, and validate the search on the title
whose constants are already known.

A replay loader in this engine is a tiny function that sets the second byte-rate key in an 8-bit
register, pushes the key step and the block size, and calls the same cipher twice - TH12's sits at
0x43c424 and is `mov al,0x5e / push 0xe1 / push 0x800` then `mov al,0x7d / push 0x3a / push
0x40`. So the search is: disassemble the code section, and report every window that holds a
small block-sized push next to an 8-bit `mov` immediate, as a (key, step, block) candidate.

Run it on H:/Games/th/12/th12.exe first: the known triple has to come out, which is what makes
the same result for another title a measurement rather than a coincidence.

Usage: th-replay-keys-exe.py <exe> [--expect 5e,e1,800]
"""
import struct
import sys

try:
    import capstone
except ImportError:
    sys.exit('capstone is not available: py -3 -m pip install capstone')

BLOCKISH = {0x20, 0x40, 0x80, 0x100, 0x200, 0x400, 0x800, 0x1000, 0x2000, 0x4000}


def code_section(data):
    lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    nsec, = struct.unpack_from('<H', data, lfanew + 6)
    optsize, = struct.unpack_from('<H', data, lfanew + 20)
    base = lfanew + 24 + optsize
    sections = {}
    for index in range(nsec):
        at = base + index * 40
        name = data[at:at + 8].split(b'\0')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', data, at + 8)
        sections[name] = (rva, raw, min(vsize or rawsize, rawsize))
    for name in ('.text', 'CODE'):
        if name in sections:
            return name, sections[name]
    return max(sections.items(), key=lambda kv: kv[1][2])


def windows(text, addr):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    # Without this, Capstone stops at the first byte it cannot decode, so a scan of the whole
    # section silently ends early - which is exactly how the loader of the known-good title (TH12,
    # at VA 0x43c424) came out as "0 candidates" the first time this ran.
    md.skipdata = True
    items = []
    for ins in md.disasm(text, addr):
        kind = None
        value = None
        if ins.mnemonic == 'mov' and len(ins.operands) == 2 and ins.operands[0].type == capstone.x86.X86_OP_REG \
                and ins.operands[0].reg in (capstone.x86.X86_REG_AL, capstone.x86.X86_REG_CL,
                                             capstone.x86.X86_REG_DL, capstone.x86.X86_REG_BL) \
                and ins.operands[1].type == capstone.x86.X86_OP_IMM:
            kind, value = 'mov8', ins.operands[1].imm & 0xFF
        elif ins.mnemonic == 'push' and len(ins.operands) == 1 and ins.operands[0].type == capstone.x86.X86_OP_IMM:
            imm = ins.operands[0].imm
            if 0 <= imm <= 0xFFFFFFFF:
                kind, value = 'push', imm
        items.append((ins.address, ins.mnemonic, ins.op_str, kind, value))
    return items


def candidates(items, span=12):
    out = []
    for index, (address, _, _, kind, value) in enumerate(items):
        if kind != 'mov8':
            continue
        near = items[max(0, index - span):index + span + 1]
        pushes = [item for item in near if item[3] == 'push']
        for a in pushes:
            for b in pushes:
                if a is b:
                    continue
                if a[4] in BLOCKISH and 0 < b[4] <= 0xFF:
                    out.append((a[0], value, b[4], a[4], address, b[1] + ' ' + b[2], a[1] + ' ' + a[2]))
    return out


def main(path, expect):
    data = open(path, 'rb').read()
    name, (rva, raw, size) = code_section(data)
    text = data[raw:raw + size]
    items = windows(text, rva)
    print('  %s: section %s, %d bytes, %d instructions disassembled' % (path, name, size, len(items)))
    found = candidates(items)
    print('  %d (key, step, block) candidate window(s)' % len(found))
    for address, key, step, block, at, push, mov in found[:40]:
        print('    0x%06x key=0x%02x step=0x%03x block=0x%x   (%s ; %s)' %
              (at, key, step, block, mov, push))
    if expect:
        wanted = tuple(int(part, 16) for part in expect.split(','))
        hit = [f for f in found if (f[1], f[2], f[3]) == wanted]
        print('  expected %s: %s' % (expect, 'FOUND at 0x%06x' % hit[0][0] if hit else 'NOT FOUND'))
        return 0 if hit else 1
    return 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    expect = argv = None
    for flag in sys.argv[1:]:
        if flag.startswith('--expect'):
            expect = flag.split('=', 1)[1] if '=' in flag else None
    if expect is None and '--expect' in sys.argv:
        expect = sys.argv[sys.argv.index('--expect') + 1]
    sys.exit(main(args[0], expect))
