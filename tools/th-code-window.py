"""Print instructions at an RVA (the address space the scans in tools/tmp print).

  py -3 tools/th-code-window.py <exe> <rva> [count] [--from-start N]
"""
import argparse
import struct

import capstone


def code_section(blob):
    lfanew = struct.unpack_from('<I', blob, 0x3C)[0]
    nsec, = struct.unpack_from('<H', blob, lfanew + 6)
    optsize, = struct.unpack_from('<H', blob, lfanew + 20)
    base = lfanew + 24 + optsize
    for index in range(nsec):
        at = base + index * 40
        name = blob[at:at + 8].split(b'\0')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', blob, at + 8)
        if name in ('.text', 'CODE'):
            return rva, raw, min(vsize, rawsize) or rawsize
    raise SystemExit('no code section')


def main(path, start, count, prefix):
    blob = open(path, 'rb').read()
    rva, raw, size = code_section(blob)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    instructions = []
    for ins in md.disasm(blob[raw:raw + size], rva):
        try:
            if ins.operands:
                pass
        except capstone.CsError:
            instructions.append((ins, None))
            continue
        instructions.append((ins, ins.operands))
    index = next((i for i, (item, _) in enumerate(instructions) if item.address >= start),
                 len(instructions))
    for item, _ in instructions[max(0, index - prefix):index + count]:
        print('  0x%06x  %s %s' % (item.address, item.mnemonic, item.op_str))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('exe')
    parser.add_argument('rva', type=lambda text: int(text, 0))
    parser.add_argument('count', nargs='?', type=int, default=24)
    parser.add_argument('--from-start', dest='prefix', type=int, default=0)
    args = parser.parse_args()
    main(args.exe, args.rva, args.count, args.prefix)
