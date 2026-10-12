"""Show how a title's code indexes a pointer array.

The arrays the port has to rebuild are found by tools/th-sample-table.py; the next thing to know is how the
original computes the index into one, because that is what decides whether a table is a constant or a shape. Here
the array's virtual address is located in .text as an immediate (little-endian), and the instructions around each
reference are disassembled, so the index expression can be read off the original rather than inferred.

usage: py -3 tools/th-array-refs.py <exe> <array-va-hex> [--window N] [--after N]
"""
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32


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
    args = sys.argv[1:]
    path, va_arg = args[0], args[1]
    window = int(args[args.index('--window') + 1]) if '--window' in args else 12
    after = int(args[args.index('--after') + 1]) if '--after' in args else 14
    array_va = int(va_arg, 16)
    blob = open(path, 'rb').read()
    image_base, = struct.unpack_from('<I', blob, struct.unpack_from('<I', blob, 0x3C)[0] + 24 + 28)
    secs = sections(blob)
    text = next(s for s in secs if s['name'] == '.text')
    code = blob[text['raw']:text['raw'] + text['rawsize']]
    text_va = image_base + text['va']
    needle = struct.pack('<I', array_va)
    rel = array_va - image_base
    needle_rel = struct.pack('<I', rel)
    hits = []
    for pat, tag in ((needle, 'absolute'), (needle_rel, 'image-relative')):
        start = 0
        while True:
            at = code.find(pat, start)
            if at < 0:
                break
            hits.append((at, tag))
            start = at + 1
    hits.sort()
    print('  %s: .text 0x%08x..0x%08x, array 0x%08x, references: %d' % (path, text_va, text_va + len(code), array_va, len(hits)))
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    for at, tag in hits[:6]:
        begin = max(0, at - window)
        block = code[begin:at + after]
        print('  --- reference at 0x%08x (%s) ---' % (text_va + at, tag))
        for ins in md.disasm(block, text_va + begin):
            mark = ' <== array immediate' if ins.address <= text_va + at < ins.address + ins.size else ''
            print('    0x%08x  %-7s %s%s' % (ins.address, ins.mnemonic, ins.op_str, mark))
    return 0 if hits else 1


if __name__ == '__main__':
    sys.exit(main())
