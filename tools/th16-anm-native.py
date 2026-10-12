"""Observe original TH16 ANM handlers in Unicorn. Every constant below was measured off th16.exe.

LOOP   = 0x45fb9a  the address every handler tail jumps to, read from the default handler at 0x4629c8
                    (`movzx eax,[edi+2]; add [ebx+0x28],eax; movss xmm1,[0x494720]; jmp 0x45fb9a`)
COOKIE = 0x47499b  the cmp-ecx-against-a-global check that handler bodies call; replaced with `ret`,
                    the same role th13's 0x47a09f and th14's 0x4854a0 play. The port of the VM
                    arrives in EBX and of the instruction in EDI, and `[ebx+0x28]` is the position
                    every handler advances, so that is what this probe follows.

The case records the context before and after each original handler:
The case records a snapshot of the whole 0x700-byte context rather than named fields, because the
field offsets are this title's own: the handlers write the flag word at +0x530 here, where TH13 keeps
its colours at +0x528 and TH14 at +0x534. Naming is left to the checker, which declares which slot
stands for which port member.

The default run covers the family list. `--all` covers every opcode whose dispatch entry is not the
default handler: the checker then referees the whole measured table instead of a sample of it. The
reference flag names the small value-table id 3, the same input the port's sweep uses, because this
title's resolver is the identity there and the port resolves its 10000-block.
"""
import hashlib
import importlib
import json
import struct
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
VM, CODE, STACK, RETURN, LOOP, COOKIE = 0x70001000, 0x70002000, 0x7001f000, 0x70000000, 0x45fb9a, 0x47499b
SNAPSHOT = 0x700
REFERENCE_INDEX = 3
OPS = [6, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315,
       403, 405, 421, 423, 424, 431, 432, 437, 438, 507]
VALUES = [0, 1, 3, 18, 19, 255, 256, -1, 10000, 10001]
VARIANTS = [0, 1]


def main():
    img, handlers, default = importlib.import_module('th-anm-handlers').handlers(16)
    all_handlers = '--all' in sys.argv
    real = sorted(op for op, entry in handlers.items() if entry != default)
    defaults = [op for op in (0, 313, 316, 439, 440, 509, 611, 613, 617, 628, 633, 634)
                if handlers.get(op, default) == default]
    selected = (real if all_handlers else OPS) + defaults

    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, count in img.sections:
        begin = base & ~4095
        machine.mem_map(begin, ((base + size + 4095) & ~4095) - begin)
        machine.mem_write(base, img.data[raw:raw + count])
    machine.mem_map(RETURN, 0x20000)
    machine.mem_write(COOKIE, b'\xc3')

    def put(p, value):
        machine.mem_write(p, struct.pack('<I', value & 0xffffffff))

    def get(p):
        return struct.unpack('<I', machine.mem_read(p, 4))[0]

    cases = []
    for op in selected:
        for value in VALUES:
            for variant in VARIANTS:
                for refs in (0, 3 if op == 312 else 1):
                    flags = 7 | (0xc0009000 if variant else 0x40000000)
                    flags2 = 0xbc0000 if variant else 0x820000
                    machine.mem_write(VM, bytes(SNAPSHOT))
                    for off, val in [(0x18, flags), (0x1c, flags2), (0x24, 27), (0x28, CODE),
                                     (0x4ac, value), (0x4b0, value ^ 2)]:
                        put(VM + off, val)
                    machine.mem_write(0x60 + VM, struct.pack('<ff', 1., -2.5))
                    machine.mem_write(0x494720, struct.pack('<f', 1.))
                    arg = REFERENCE_INDEX if refs & 1 else value
                    arg2 = REFERENCE_INDEX if refs & 2 else value ^ 2
                    machine.mem_write(CODE, bytes(64))
                    machine.mem_write(CODE, struct.pack('<hHhHII', op, 16 if op == 312 else 12, 0,
                                                        refs, arg & 0xffffffff, arg2 & 0xffffffff))
                    machine.reg_write(UC_X86_REG_ESP, STACK)
                    machine.reg_write(UC_X86_REG_EBP, STACK)
                    machine.reg_write(UC_X86_REG_EDI, CODE)
                    machine.reg_write(UC_X86_REG_EBX, VM)
                    machine.reg_write(UC_X86_REG_XMM1, 0xbf800000)
                    machine.reg_write(UC_X86_REG_FPCW, 0x37f)
                    machine.reg_write(UC_X86_REG_FPSW, 0)
                    machine.reg_write(UC_X86_REG_FPTAG, 0xffff)
                    before = machine.mem_read(VM, SNAPSHOT).hex()   # the state the handler starts from
                    entry = handlers.get(op, default)
                    fault = None
                    try:
                        machine.emu_start(entry, LOOP, count=100000)
                        landing = machine.reg_read(UC_X86_REG_EIP)
                        if landing != LOOP:
                            fault = 'landed at ' + hex(landing)
                    except Exception as error:
                        # The commands that expect a caller frame cannot run from a bare loop: they read
                        # the stack a caller would have left. Recorded, not hidden.
                        fault = str(error)[:48]
                    cases.append(dict(op=op, value=value, variant=variant, refs=refs, arg=arg, arg2=arg2,
                                     handler=hex(entry), position=get(VM + 0x28), fault=fault,
                                     before=before, context=machine.mem_read(VM, SNAPSHOT).hex()))
    report = dict(game='th16',
                  scope='The whole context after each original handler, at the next dispatch '
                        'boundary. Offsets are this title\'s own; no renderer or complete-game claim.',
                  executableSha256=hashlib.sha256(img.data).hexdigest(),
                  measured=dict(loop=hex(LOOP), cookie=hex(COOKIE), snapshot=SNAPSHOT,
                                positionSlot=0x28, defaultHandler=hex(default),
                                entries=len(handlers), measuredFrom='th16.exe',
                                coverage='every real handler' if all_handlers else 'the family list'),
                  realHandlers=len(real), defaultOpcodes=defaults, cases=cases)
    out = ROOT / ('artifacts/th16/anm-native.json' if not all_handlers else 'artifacts/th16/anm-native-all.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, separators=(',', ':')) + '\n', encoding='utf-8')
    deltas = {}
    for row in cases:
        deltas.setdefault(row['op'], set()).add(row['position'] - CODE)
    print(f'{len(cases)} cases over {len(set(r["op"] for r in cases))} opcodes '
          f'({report["measured"]["coverage"]}, {report["realHandlers"]} real handlers); '
          f'{out.name} is {out.stat().st_size} bytes.')
    faults = sum(1 for row in cases if row.get('fault'))
    print(f'{faults} of {len(cases)} cases faulted (the caller-frame family); the checker skips those.')
    print('position advance: ' + ', '.join(f'{op}:{sorted(v)}' for op, v in sorted(deltas.items())[:5]) + ' ...')


if __name__ == '__main__':
    main()
