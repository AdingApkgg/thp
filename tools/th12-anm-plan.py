"""Measure the constants a TH12 ANM oracle needs, the way the other titles' oracles carry them.

The handler table is already read for title 12 by tools/th-anm-handlers.py: the dispatch at 0x45569d
is `movsx eax, word [esi]; inc eax; cmp eax, 0x6f; ja default; jmp [eax*4+0x458730]`, a flat
table with the -1 sentinel, default 0x457c91. The three older oracles additionally need the address
a handler returns to, which they call the boundary, and the register convention of the call. This
tool reads both off the image and prints the evidence; it asserts nothing it has not read.

Usage: py -3 tools/th12-anm-plan.py [--window=N]
"""
import importlib, struct, sys
from pathlib import Path

Image = importlib.import_module('th12-pe').Image
ROOT = Path(__file__).resolve().parents[1]
GUARD = 0x45569d          # the dispatch of title 12
TABLE = 0x458730
DEFAULT = 0x457c91


def find_entry(img, address, reach=0x400):
    """The function enclosing `address`: the nearest prologue before it."""
    for back in range(reach):
        here = address - back
        if img.read(here, 3) == bytes.fromhex('558bec'):
            return here
    return None


def walk_prologue(img, entry, span=64):
    r32 = {0: 'eax', 1: 'ecx', 2: 'edx', 3: 'ebx', 4: 'esp', 5: 'ebp', 6: 'esi', 7: 'edi'}
    reads = []
    at = entry
    while at < entry + span:
        op = img.read(at, 1)
        if not op:
            break
        if op[0] == 0x8b:
            modrm = img.read(at + 1, 1)[0]
            if (modrm & 0xc7) == 0x45:                       # mov r32, [ebp+disp8]
                reads.append((at, r32[(modrm >> 3) & 7], struct.unpack('<b', bytes([img.read(at + 2, 1)[0]]))[0]))
                at += 3
                continue
        if op[0] == 0x55:
            at += 1
            continue
        op2 = img.read(at + 1, 2)
        at += 2 if op[0] == 0x51 or op[0] == 0x53 or op[0] == 0x56 or op[0] == 0x57 else 1
        void = op2
    return reads


def backward_jumps(img, begin, end):
    out = []
    at = begin
    while at < end:
        byte = img.read(at, 1)[0]
        if byte == 0xeb and at + 1 < end:
            rel = struct.unpack('<b', bytes([img.read(at + 1, 1)[0]]))[0]
            target = (at + 2 + rel) & 0xffffffff
            if rel < 0:
                out.append((at, target, 'jmp short'))
            at += 2
            continue
        if byte == 0xe9 and at + 4 < end:
            rel = struct.unpack('<i', bytes(img.read(at + 1, 4)))[0]
            out.append((at, (at + 5 + rel) & 0xffffffff, 'jmp near'))
            at += 5
            continue
        if byte == 0x0f and at + 5 < end and 0x80 <= img.read(at + 1, 1)[0] <= 0x8f:
            rel = struct.unpack('<i', bytes(img.read(at + 2, 4)))[0]
            out.append((at, (at + 6 + rel) & 0xffffffff, 'jcc'))
            at += 6
            continue
        at += 1
    return out


def try_run(ops, boundary):
    """Run title 12's own handlers and see whether they reach the measured boundary.

    The convention read off the prologue: the interpreter takes the VM in EDI, loads the script
    pointer from [edi+0x3f0] into ESI, and its own per-instruction back edge is the boundary. A
    handler called directly with those registers must end at the boundary, which is the assertion
    every other title's oracle makes.
    """
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import (UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDI,
                                  UC_X86_REG_EBP, UC_X86_REG_EIP, UC_X86_REG_ESI,
                                  UC_X86_REG_ESP, UC_X86_REG_FPCW, UC_X86_REG_FPSW,
                                  UC_X86_REG_FPTAG)
    importlib.import_module('th-anm-handlers')
    table = importlib.import_module('th12-anm-handlers-cache') if False else None
    void = table
    VM = 0x70200000
    CODE = 0x70210000
    STACK = 0x7021f000
    img, handlers, default = importlib.import_module('th-anm-handlers').handlers(12)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, n in img.sections:
        begin = base & ~4095
        length = ((base + size + 4095) & ~4095) - begin
        m.mem_map(begin, length)
        m.mem_write(base, img.data[raw:raw + n])
    m.mem_map(VM, 0x30000)
    m.mem_write(0x4c0a28, struct.pack('<f', 1.))
    for op in ops:
        for value in (0, 3, -1):
            m.mem_write(VM, bytes(0x400))
            m.mem_write(CODE, struct.pack('<hHhHII', op, 12, 0, 0, value & 0xffffffff, 0))
            img_void = img
            m.mem_write(VM + 0x3f0, struct.pack('<I', CODE))
            m.mem_write(0x4c0a28, struct.pack('<f', 1.))
            m.reg_write(UC_X86_REG_EDI, VM)
            m.reg_write(UC_X86_REG_ESI, CODE)
            m.reg_write(UC_X86_REG_EBX, VM)
            m.reg_write(UC_X86_REG_ECX, VM)
            m.reg_write(UC_X86_REG_ESP, STACK)
            m.reg_write(UC_X86_REG_EBP, STACK)
            m.reg_write(UC_X86_REG_FPCW, 0x37f)
            m.reg_write(UC_X86_REG_FPSW, 0)
            m.reg_write(UC_X86_REG_FPTAG, 0xffff)
            entry = handlers.get(op, default)
            try:
                m.emu_start(entry, boundary, count=200000)
                eip = m.reg_read(UC_X86_REG_EIP)
                print('    op %-3d value %-3d from 0x%x: EIP 0x%x %s' % (
                    op, value, entry, eip,
                    'reached the boundary' if eip == boundary else 'DID NOT reach it'))
            except Exception as error:
                print('    op %-3d value %-3d from 0x%x: fault %s (EIP 0x%x)' % (
                    op, value, entry, type(error).__name__, m.reg_read(UC_X86_REG_EIP)))
        void2 = img_void
        del void2


def main():
    want = [int(a.split('=')[1]) for a in sys.argv if a.startswith('--try=')]
    if want:
        print('  the measured constants, put to work on ordinary handlers:')
        try_run(want, 0x455686)
        return

    handlers = importlib.import_module('th-anm-handlers')
    img, table, default = handlers.handlers(12)
    entries = sorted(table)
    sentinel = table[-1]
    print('  the table of title 12: %d entries, opcodes %d..%d, sentinel opcode -1 at 0x%x, '
          'default 0x%x' % (len(entries), entries[0], entries[-1], sentinel, default))
    print('  dispatch guard 0x%x: %s' % (GUARD, img.read(GUARD, 7).hex(' ')))
    print('  handlers reachable: %d of %d are inside the image' % (
        sum(1 for op in entries if 0x401000 <= table[op] < 0x470000), len(entries)))
    entry = find_entry(img, GUARD)
    print('  the enclosing function begins at %s' % (hex(entry) if entry else 'not found'))
    if entry:
        print('  its prologue: %s' % img.read(entry, 32).hex(' '))
        for at, register, disp in walk_prologue(img, entry):
            print('    +0x%x: mov %s, [ebp%+d]   the call convention of this function'
                  % (at - entry, register, disp))
    print('  backward jumps around the dispatch, candidates for the boundary the oracles call LOOP:')
    for at, target, kind in backward_jumps(img, max(0x455000, (entry or GUARD) - 0x200),
                                          GUARD + 0x40):
        mark = 'inside the function' if entry and entry - 0x100 <= target <= GUARD + 0x40 else 'far'
        print('    +0x%05x %-9s -> 0x%x  %s' % (at, kind, target, mark))
    window = int(([a for a in sys.argv if a.startswith('--window=')] or ['--window=48'])[0]
                 .split('=')[1])
    print('  the guard in context (0x%x bytes before it):' % window)
    print('    %s' % img.read(GUARD - window, window + 16).hex(' '))


main()
