"""Take the whole-context snapshot of an original TH13 or TH14 handler, as titles 16 to 18 have.

The corpora of titles 13 and 14 record named fields, which is why their flag words were inherited
rather than read. This probe records the whole 0x700-byte context before and after one handler, with
the anchors the earlier work measured by hand and the register conventions it used (title 13: the
instruction in EDI and the object in EBX; title 14: the instruction in EBX and the object in EDI
and ECX). The offsets of the seed are the earlier work's as well, so a difference between the
labels it used and the offsets this probe shows is itself a measurement.

Output: artifacts/th13/anm-native-context.json and artifacts/th14/anm-native-context.json, the
touched-offset census printed in one line, since that census is the answer to "where does this
title keep its flags".
"""
import hashlib
import importlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
VM, CODE, STACK, RETURN, SNAPSHOT = 0x70001000, 0x70002000, 0x7001f000, 0x70000000, 0x700
FAMILY = [1, 2, 6, 302, 304, 306, 309, 310, 312, 403, 405, 423, 424, 431, 432, 437, 438, 507]
DEFAULTS = {13: [313, 314, 315, 316, 317, 318, 439, 440, 441, 509, 609, 610, 612, 613, 614, 617,
                 618, 628, 633, 634],
            14: [313, 314, 315, 316, 317, 318, 439, 440, 441, 509, 609, 610, 612, 613, 614, 617,
                 618, 628, 633, 634]}
VALUES = [0, 1, 3, 18, 255, -1]

PLANS = {
    13: {'loop': 0x4624fd, 'cookie': 0x47a09f, 'ip': 'EDI', 'vm': ['EBX'],
         'seed': [(0x18, 'flags'), (0x1c, 'flags2'), (0x24, 27), (0x28, 'CODE'),
                  (0x528, 0xab123456), (0x52c, 0x78345678), (0x4ac, 'value'),
                  (0x4b0, 'value^2'), (0x544, 0x4c0a28), (0x548, 1)],
         'floatAt': (0x4c0a28, 1.0)},
    14: {'loop': 0x47007e, 'cookie': 0x4854a0, 'ip': 'EBX', 'vm': ['EDI', 'ECX'],
         'seed': [(0x18, 'flags'), (0x1c, 'flags2'), (0x24, 27), (0x28, 'CODE'),
                  (0x534, 0xab123456), (0x538, 0x78345678), (0x4ac, 'value'),
                  (0x4b0, 'value^2'), (0x554, 0x4d8f58), (0x558, 1)],
         'floatAt': (0x4d8f58, 1.0)}}
REGS = {'EAX': UC_X86_REG_EAX, 'EBX': UC_X86_REG_EBX, 'ECX': UC_X86_REG_ECX,
        'EDX': UC_X86_REG_EDX, 'ESI': UC_X86_REG_ESI, 'EDI': UC_X86_REG_EDI}


def main():
    title = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--title=')), '13'))
    plan = PLANS[title]
    img, handlers, default = importlib.import_module('th-anm-handlers').handlers(title)
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, count in img.sections:
        begin = base & ~4095
        machine.mem_map(begin, ((base + size + 4095) & ~4095) - begin)
        machine.mem_write(base, img.data[raw:raw + count])
    machine.mem_map(RETURN, 0x20000)
    machine.mem_write(plan['cookie'], b'\xc3')

    def put(p, value):
        machine.mem_write(p, struct.pack('<I', value & 0xffffffff))

    def get(p):
        return struct.unpack('<I', machine.mem_read(p, 4))[0]

    cases = []
    everyone = '--all' in sys.argv
    if everyone:
        selected = sorted(op for op, entry in handlers.items() if entry != default)
        extra = [op for op in DEFAULT_OPS_FOR(title) if handlers.get(op, default) == default]
    else:
        selected = [op for op in FAMILY if op in handlers]
        extra = []
    for op in selected + extra:
        for value in VALUES:
            for variant in (0, 1):
                flags = 7 | (0xc0009000 if variant else 0x40000000)
                flags2 = 0x840000 if variant else 0x800000
                machine.mem_write(VM, bytes(SNAPSHOT))
                for off, val in plan['seed']:
                    put(VM + off, {'flags': flags, 'flags2': flags2, 'value': value,
                                   'value^2': value ^ 2, 'CODE': CODE}.get(val, val))
                machine.mem_write(VM + 0x60, struct.pack('<ff', 1., -2.5))
                machine.mem_write(plan['floatAt'][0], struct.pack('<f', plan['floatAt'][1]))
                machine.mem_write(CODE, bytes(64))
                machine.mem_write(CODE, struct.pack('<hHhHII', op, 12, 0, refs(op, variant),
                                                    value & 0xffffffff, (value ^ 2) & 0xffffffff))
                for reg in REGS.values():
                    machine.reg_write(reg, 0)
                for name in plan['vm']:
                    machine.reg_write(REGS[name], VM)
                machine.reg_write(REGS[plan['ip']], CODE)
                machine.reg_write(UC_X86_REG_ESP, STACK)
                machine.reg_write(UC_X86_REG_EBP, STACK)
                machine.reg_write(UC_X86_REG_FPCW, 0x37f)
                machine.reg_write(UC_X86_REG_FPSW, 0)
                machine.reg_write(UC_X86_REG_FPTAG, 0xffff)
                before = machine.mem_read(VM, SNAPSHOT).hex()
                fault = None
                try:
                    machine.emu_start(handlers.get(op, default), plan['loop'], count=200000)
                    landing = machine.reg_read(UC_X86_REG_EIP)
                    if landing != plan['loop']:
                        fault = 'landed at ' + hex(landing)
                except Exception as error:
                    fault = str(error)[:48]
                cases.append(dict(op=op, value=value, variant=variant, arg=value, arg2=value ^ 2,
                                 handler=hex(handlers.get(op, default)), fault=fault,
                                 before=before, context=machine.mem_read(VM, SNAPSHOT).hex()))
    touched = Counter()
    for row in cases:
        a, b = bytes.fromhex(row['before']), bytes.fromhex(row['context'])
        for off in range(0, SNAPSHOT - 3, 4):
            if a[off:off + 4] != b[off:off + 4]:
                touched[off] += 1
    print('  th%d: %d cases, %d faulted over %d handlers' %
          (title, len(cases), sum(1 for r in cases if r['fault']), len(selected)))
    print('  offsets the handlers move (top 10): %s'
          % ', '.join('0x%x x%d' % (off, n) for off, n in touched.most_common(10)))
    out = ROOT / ('artifacts/th%d/anm-native-context%s.json'
                  % (title, '-all' if everyone else ''))
    out.write_text(json.dumps(dict(game='th%d' % title,
                                 scope='The whole context after one original handler. Offsets are '
                                       'this title\'s own; no renderer or gameplay claim.',
                                 executableSha256=hashlib.sha256(img.data).hexdigest(),
                                 measured=dict(loop=hex(plan['loop']), cookie=hex(plan['cookie']),
                                               ipRegister=plan['ip'], vmRegisters=plan['vm'],
                                               seedOffsets=[hex(off) for off, _ in plan['seed']],
                                               measuredFrom='th%d.exe' % title,
                                               coverage='the family list and the defaults'),
                                 cases=cases), separators=(',', ':')) + '\n', encoding='utf-8')
    print('  wrote %s (%d bytes)' % (out.relative_to(ROOT), out.stat().st_size))


def refs(op, variant):
    return (3 if op == 312 else 1) if variant and op in (6, 306, 312, 403, 405, 432, 437, 507) else 0


def DEFAULT_OPS_FOR(title):
    return DEFAULTS[title]


if __name__ == '__main__':
    main()
