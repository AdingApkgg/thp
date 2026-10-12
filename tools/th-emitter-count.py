"""The clear loop over a title's emitter array, and the count it walks.

TH12's routine at 0x012407 is `push 0x214 / push 0 / push <slot> / call memset` inside a loop that
does `add edi, 0x214 / sub ebx, 1 / jns`: the register that is decremented is the number of slots.
Printing the window from before the loop to its end shows where the count comes from.

  py -3 tools/th-emitter-count.py <exe> [--stride 0x214]
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


def main(path, stride):
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
    print('  %s: %d instruction(s)' % (path.split('/')[-1], len(instructions)))
    found = 0
    for index, (ins, operands) in enumerate(instructions):
        if operands is None:
            continue
        if ins.mnemonic != 'push':
            continue
        if not any(o.type == capstone.x86.X86_OP_IMM and (o.imm & 0xFFFFFFFF) == stride
                   for o in operands):
            continue
        ahead = instructions[index:index + 12]
        if not any(item.mnemonic == 'add' and hex(stride) in item.op_str
                   for item, _ in ahead):
            continue
        found += 1
        start = max(0, index - 16)
        print('  --- clear loop at 0x%06x ---' % ins.address)
        for item, _ in instructions[start:index + 12]:
            print('      0x%06x  %-8s %s' % (item.address, item.mnemonic, item.op_str))
        if found >= 2:
            break
    if not found:
        print('  no clear loop found with stride 0x%x' % stride)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('exe')
    parser.add_argument('--stride', type=lambda text: int(text, 0), default=0x214)
    args = parser.parse_args()
    main(args.exe, args.stride)
