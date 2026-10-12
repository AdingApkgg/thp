#!/usr/bin/env python3
"""Find the call site that hands a stage record's entry pair to the restore.

The TH13 comment in `Replay.hpp` names the shape: a record is picked out of the stage table, the
pair is taken from `record + 0xC`, and the pair-restore is called with that pointer:

    th13.exe 0x048fe4  mov edi, dword ptr [ebx + ecx*8 + 0xd8]   ; this stage's record
    th13.exe 0x048feb  lea ecx, [edi + 0xc]
    th13.exe 0x048ff4  call 0x47850

So the scanner looks for `lea reg,[reg + disp]` with the pair's displacement, close to a call,
inside a window that also indexes a table. Run it on th13.exe first: that site must be reported,
which is the control. Then the newer titles are asked the same question.

Usage: th-replay-entry-exe.py <exe> [--disp 0xc]
"""
import argparse
import struct
import sys

import capstone


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


def scan(path, disp, window=5):
    data = open(path, 'rb').read()
    rva, raw, size = code_section(data)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    instructions = list(md.disasm(data[raw:raw + size], rva))
    sites = []
    for index, ins in enumerate(instructions):
        if ins.mnemonic != 'lea' or len(ins.operands) != 2:
            continue
        destination, source = ins.operands
        if source.type != capstone.x86.X86_OP_MEM or source.mem.disp != disp:
            continue
        if source.mem.base in (capstone.x86.X86_REG_EBP, capstone.x86.X86_REG_ESP):
            continue
        after = instructions[index + 1:index + 1 + window]
        call = next((i for i in after if i.mnemonic == 'call'), None)
        if call is None:
            continue
        before = instructions[max(0, index - 4):index]
        table = next((i for i in before if i.mnemonic == 'mov' and any(
            op.type == capstone.x86.X86_OP_MEM and op.mem.index != 0 for op in i.operands)), None)
        sites.append((ins.address, table, ins, call, before, after))
    print('  %s: %d site(s) with a +0x%x pair and a call in the next %d instructions'
          % (path.split('\\')[-1], len(sites), disp, window))
    for address, table, ins, call, before, after in sites[:8]:
        if table:
            print('      table: 0x%06x %s %s' % (table.address, table.mnemonic, table.op_str))
        print('      pair : 0x%06x %s %s' % (address, ins.mnemonic, ins.op_str))
        print('      call : 0x%06x %s %s' % (call.address, call.mnemonic, call.op_str))
    return sites


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('exe')
    parser.add_argument('--disp', type=lambda text: int(text, 0), default=0xC)
    parser.add_argument('paths', nargs='*')
    args = parser.parse_args()
    scan(args.exe, args.disp)
    for extra in args.paths:
        scan(extra, args.disp)
