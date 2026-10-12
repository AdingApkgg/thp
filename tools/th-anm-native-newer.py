"""Observe original ANM handlers of the newer titles (16, 17, 18) in Unicorn, every anchor measured.

Shared by the three titles because they are one engine family, and validated against the anchors that
are already known for title 16 (loop 0x45fb9a, position slot 0x28, vm register ebx, float constant
0x494720, cookie 0x47499b with 308 call sites). The finder reproduces all five of them on title 16,
so it is trusted to name the same five on 17 and 18:

  LOOP, the address the handler tail jumps to, read from the default handler's own tail;
  the position slot (`add [reg+disp],eax` in that same tail) and the register that holds the VM,
    which is `ebx` on 16 and `esi` on 17, and so is discovered rather than assumed;
  COOKIE, the `cmp ecx,[global]` site the handler bodies call, found as the one with the most call
    sites in .text and replaced with `ret`, exactly as the TH13/TH14/TH16 probes do.
The context layout is the title's own, so a case keeps a whole 0x700-byte snapshot and naming is left
to the checker. Run with --discover to print the anchors and a small run's touched offsets, and with
--title=18 (or 16) to do the same there.
"""
import hashlib
import importlib
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parents[1]
TITLE = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--title=')), '17'))
VM, CODE, STACK, RETURN = 0x70001000, 0x70002000, 0x7001f000, 0x70000000
SNAPSHOT = 0x700
REFERENCE_INDEX = 3
OPS = [6, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315,
       403, 405, 421, 423, 424, 431, 432, 437, 438, 507]
VALUES = [0, 1, 3, 18, 19, 255, 256, -1, 10000, 10001]
VARIANTS = [0, 1]
MD = Cs(CS_ARCH_X86, CS_MODE_32)
REGISTERS = {'eax': UC_X86_REG_EAX, 'ebx': UC_X86_REG_EBX, 'ecx': UC_X86_REG_ECX,
             'edx': UC_X86_REG_EDX, 'esi': UC_X86_REG_ESI, 'edi': UC_X86_REG_EDI,
             'ebp': UC_X86_REG_EBP}


def anchors(img, default, table):
    facts = {'positionSlot': None, 'loop': None, 'floatConstant': None, 'vmReg': None}
    for ins in MD.disasm(img.read(default, 48), default):
        if ins.mnemonic == 'add':
            hit = re.search(r'\[(\w+) \+ (0x[0-9a-f]+)\]', ins.op_str)
            if hit and facts['positionSlot'] is None and ins.op_str.rstrip().endswith('eax'):
                facts['positionSlot'] = int(hit.group(2), 16)
                facts['vmReg'] = hit.group(1)
        if ins.mnemonic == 'add' and facts['vmReg'] is None:
            hit = re.search(r'\[(\w+) \+ (0x[0-9a-f]+)\]', ins.op_str)
            if hit:
                facts['vmReg'] = hit.group(1)
        if ins.mnemonic == 'movss':
            hit = re.search(r'\[(0x[0-9a-f]+)\]', ins.op_str)
            if hit:
                facts['floatConstant'] = int(hit.group(1), 16)
        if ins.mnemonic == 'and' and facts['vmReg'] and '0x530' in ins.op_str:
            hit = re.search(r'\[(\w+) \+ 0x530\]', ins.op_str)
            if hit:
                facts['vmReg'] = hit.group(1)
        if ins.mnemonic == 'jmp':
            facts['loop'] = int(ins.op_str, 16)
            break

    def va_of(off):
        for _, base, size, raw, count in img.sections:
            if raw <= off < raw + count:
                return base + (off - raw)
        return None

    calls = Counter()
    at = 0
    while True:
        found = img.data.find(b'\xe8', at)
        if found < 0 or found + 5 > len(img.data):
            break
        here = va_of(found)
        if here is not None:
            calls[here + 5 + struct.unpack_from('<i', img.data, found + 1)[0]] += 1
        at = found + 1
    candidates = []
    at = 0
    while True:
        found = img.data.find(b'\x3b\x0d', at)
        if found < 0 or found + 6 > len(img.data):
            break
        target = va_of(found)
        if target and img.is_code(target):
            candidates.append((calls[target], target, found))
        at = found + 1
    candidates.sort(reverse=True)
    facts['cookie'] = candidates[0][1] if candidates else None
    facts['cookieCallers'] = candidates[0][0] if candidates else 0
    facts['cookieRivals'] = [(n, hex(t)) for n, t, _ in candidates[:4]]
    return facts


def main():
    discover = '--discover' in sys.argv
    img, handlers, default = importlib.import_module('th-anm-handlers').handlers(TITLE)
    facts = anchors(img, default, handlers)
    real = sorted(op for op, entry in handlers.items() if entry != default)
    selected = OPS if not discover else [op for op in OPS if op in real][:8]
    print('  th%d anchors measured off the executable:' % TITLE)
    print('    loop            %s' % hex(facts['loop']))
    print('    position slot   %s' % hex(facts['positionSlot'] if facts['positionSlot'] else 0))
    print('    vm register     %s' % facts['vmReg'])
    print('    float constant  %s'
          % (hex(facts['floatConstant']) if facts['floatConstant'] else 'none in the tail'))
    print('    cookie          %s  with %d call sites; rivals %s'
          % (hex(facts['cookie']), facts['cookieCallers'], facts['cookieRivals']))
    print('    handlers %d, real handlers %d, default %s' % (len(handlers), len(real), hex(default)))

    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, count in img.sections:
        begin = base & ~4095
        machine.mem_map(begin, ((base + size + 4095) & ~4095) - begin)
        machine.mem_write(base, img.data[raw:raw + count])
    machine.mem_map(RETURN, 0x20000)
    machine.mem_write(facts['cookie'], b'\xc3')

    def put(p, value):
        machine.mem_write(p, struct.pack('<I', value & 0xffffffff))

    def get(p):
        return struct.unpack('<I', machine.mem_read(p, 4))[0]

    cases = []
    for op in selected:
        for value in VALUES:
            for variant in VARIANTS:
                for refs in (0, 3 if op == 312 else 1):
                    machine.mem_write(VM, bytes(SNAPSHOT))
                    for off, val in [(0x18, 7 | (0xc0009000 if variant else 0x40000000)),
                                     (0x1c, 0xbc0000 if variant else 0x820000), (0x24, 27),
                                     (0x28, CODE), (0x4ac, value), (0x4b0, value ^ 2)]:
                        put(VM + off, val)
                    machine.mem_write(0x60 + VM, struct.pack('<ff', 1., -2.5))
                    if facts['floatConstant']:
                        machine.mem_write(facts['floatConstant'], struct.pack('<f', 1.))
                    arg = REFERENCE_INDEX if refs & 1 else value
                    arg2 = REFERENCE_INDEX if refs & 2 else value ^ 2
                    machine.mem_write(CODE, bytes(64))
                    machine.mem_write(CODE, struct.pack('<hHhHII', op, 16 if op == 312 else 12, 0,
                                                        refs, arg & 0xffffffff, arg2 & 0xffffffff))
                    for reg in (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                                UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP):
                        machine.reg_write(reg, 0)
                    machine.reg_write(REGISTERS[facts['vmReg']], VM)
                    machine.reg_write(UC_X86_REG_ESP, STACK)
                    machine.reg_write(UC_X86_REG_EBP, STACK)
                    machine.reg_write(UC_X86_REG_EDI, CODE)
                    machine.reg_write(UC_X86_REG_XMM1, 0xbf800000)
                    machine.reg_write(UC_X86_REG_FPCW, 0x37f)
                    machine.reg_write(UC_X86_REG_FPSW, 0)
                    machine.reg_write(UC_X86_REG_FPTAG, 0xffff)
                    before = machine.mem_read(VM, SNAPSHOT).hex()
                    entry = handlers.get(op, default)
                    fault = None
                    try:
                        machine.emu_start(entry, facts['loop'], count=100000)
                        landing = machine.reg_read(UC_X86_REG_EIP)
                        if landing != facts['loop']:
                            fault = 'landed at ' + hex(landing)
                    except Exception as error:
                        fault = str(error)[:48]
                    cases.append(dict(op=op, value=value, variant=variant, refs=refs, arg=arg, arg2=arg2,
                                     handler=hex(entry), position=get(VM + (facts['positionSlot'] or 0)),
                                     fault=fault, before=before,
                                     context=machine.mem_read(VM, SNAPSHOT).hex()))

    touched = Counter()
    for row in cases:
        a, b = bytes.fromhex(row['before']), bytes.fromhex(row['context'])
        for i in range(0, min(len(a), len(b)) - 3, 4):
            if a[i:i + 4] != b[i:i + 4]:
                touched[i] += 1
    print('  %d cases, %d faulted' % (len(cases), sum(1 for r in cases if r['fault'])))
    print('  offsets the handlers move (top 8): %s'
          % ', '.join('0x%x x%d' % (off, n) for off, n in touched.most_common(8)))
    if discover:
        return
    report = dict(game='th%d' % TITLE,
                  scope='The whole context after each original handler, at the next dispatch '
                        'boundary. Offsets are this title\'s own; no renderer or complete-game claim.',
                  executableSha256=hashlib.sha256(img.data).hexdigest(),
                  measured=dict(loop=hex(facts['loop']), cookie=hex(facts['cookie']),
                                positionSlot=facts['positionSlot'],
                                floatConstant=(hex(facts['floatConstant'])
                                              if facts['floatConstant'] else None),
                                snapshot=SNAPSHOT, defaultHandler=hex(default),
                                entries=len(handlers), cookieCallers=facts['cookieCallers'],
                                cookieRivals=facts['cookieRivals'], measuredFrom='th%d.exe' % TITLE,
                                coverage='the family list'),
                  realHandlers=len(real), defaultOpcodes=[op for op in selected if handlers.get(op) == default],
                  cases=cases)
    out = ROOT / ('artifacts/th%d/anm-native.json' % TITLE)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, separators=(',', ':')) + '\n', encoding='utf-8')
    print('  wrote %s (%d bytes)' % (out.relative_to(ROOT), out.stat().st_size))


if __name__ == '__main__':
    main()
