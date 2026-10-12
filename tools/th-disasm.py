"""Disassemble a region of a title's executable.

Companion to tools/th-sample-table.py (which finds the pointer arrays) and tools/th-array-refs.py (which finds how a
table is indexed): this one prints the code at a virtual address, so a structure can be read off the routine that
parses it instead of inferred from the files.
"""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_MODE_64


def sections(blob):
    lfanew = struct.unpack_from('<I', blob, 0x3C)[0]
    coff = lfanew + 4
    nsec, = struct.unpack_from('<H', blob, coff + 2)
    optsize, = struct.unpack_from('<H', blob, coff + 16)
    sec = coff + 20 + optsize
    out = []
    for i in range(nsec):
        base = sec + i * 40
        name = blob[base:base + 8].rstrip(b'\0').decode('latin1').encode('ascii', 'replace').decode()
        vsize, va, rawsize, raw = struct.unpack_from('<IIII', blob, base + 8)
        out.append({'name': name, 'va': va, 'vsize': vsize, 'raw': raw, 'rawsize': rawsize})
    return out


def main():
    path, va_arg = sys.argv[1], sys.argv[2]
    count = int(sys.argv[sys.argv.index('--count') + 1]) if '--count' in sys.argv else 40
    blob = open(path, 'rb').read()
    lfanew = struct.unpack_from('<I', blob, 0x3C)[0]
    magic, = struct.unpack_from('<H', blob, lfanew + 24)
    if magic not in (0x10b,0x20b):
        raise ValueError('unsupported PE optional header')
    is64=magic==0x20b
    image_base, = struct.unpack_from('<Q' if is64 else '<I', blob, lfanew + 24 + (24 if is64 else 28))
    va = int(va_arg, 16)
    sec = next(s for s in sections(blob) if image_base + s['va'] <= va < image_base + s['va'] + s['rawsize'])
    start = sec['raw'] + (va - image_base - sec['va'])
    md = Cs(CS_ARCH_X86, CS_MODE_64 if is64 else CS_MODE_32)
    md.detail = False
    lines = 0
    for ins in md.disasm(blob[start:start + 16 * count], va):
        print('  0x%08x  %-9s %s' % (ins.address, ins.mnemonic, ins.op_str))
        lines += 1
        if lines >= count:
            break
    return 0


if __name__ == '__main__':
    sys.exit(main())
