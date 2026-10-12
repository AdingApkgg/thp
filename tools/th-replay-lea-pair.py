"""Find a title's replay record size from the two `lea` shapes its loader uses, the pair TH12's
comment names: `lea edx,[eax+imm]` for the payload and `lea eax,[eax+ecx+imm]` for the next
record. The scan reports the instruction pairs whose two displacements agree, so the number is a
reading of the loader rather than a guess. Checked on th12 (0xa0) and th13 (0xc4) first.

  py -3 tools/tmp/replay-record-size.py <exe>...
"""
import struct
import sys

import capstone


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


def scan(path):
    data = open(path, 'rb').read()
    rva, raw, size = text_section(data)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    plain, indexed = [], []
    for ins in md.disasm(data[raw:raw + size], rva):
        if ins.mnemonic != 'lea' or len(ins.operands) != 2:
            continue
        dst, src = ins.operands
        if dst.type != capstone.x86.X86_OP_REG or src.type != capstone.x86.X86_OP_MEM:
            continue
        imm = src.mem.disp & 0xFFFFFFFF
        if not 0x40 <= imm <= 0x400:
            continue
        (indexed if src.mem.index else plain).append((ins.address, imm, src.mem.base, src.mem.index, ins.op_str))
    pairs = []
    for address, imm, base, index, form in indexed:
        for other, oimm, obase, oindex, oform in plain:
            if oimm == imm and abs(other - address) <= 0x120:
                pairs.append((address, imm, form, oform, other))
                break
    return pairs


if __name__ == '__main__':
    for path in sys.argv[1:]:
        pairs = scan(path)
        print('  %s: %d agreeing pair(s)' % (path, len(pairs)))
        for address, imm, form, oform, other in pairs[:6]:
            print('    0x%06x %-26s with 0x%06x %-22s (size 0x%x)' % (address, form, other, oform, imm))
