"""Measure the effect signature of every dispatched TH16 ANM handler, not just the family list.

The oracle of tools/th16-anm-native.py answers for 32 hand-picked opcodes with whole contexts. The table
this title needs (section 302.5) has 529 rows, so this instrument runs all of them and keeps, per case,
only what changed: the position delta and the 4-byte slots whose value differs from the preset. That is
the raw material from which the next round matches each handler onto the port's existing vocabulary; the
whole context would be 80 MB and answer the same question.

Every constant is the one measured in section 300: LOOP 0x45fb9a, COOKIE 0x47499b, the default
handler 0x4629c8, the instruction at CODE with the opcode at +0 and the length at +2.
"""
import hashlib
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
VM, CODE, STACK, LOOP, COOKIE = 0x70001000, 0x70002000, 0x7001f000, 0x45fb9a, 0x47499b
SNAPSHOT = 0x700
PRESET = [(0x18, 0x40000007), (0x1c, 0x820000), (0x24, 27), (0x28, CODE), (0x4ac, 0),
          (0x4b0, 2)]
# The reference flag names an index into the value table, so the grid's reference case uses a small
# one on both sides: the port's resolver indexes that table directly, and 10000 left it.
GRID = [(0, 0, 0), (0, 0, 1), (18, 0, 0), (18, 0, 1),
        (1, 1, 0), (1, 1, 1), (2, 0, 1), (0, 1, 1)]
REFERENCE_INDEX = 3


def main():
    img, handlers, default = importlib.import_module('th-anm-handlers').handlers(16)
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, count in img.sections:
        begin = base & ~4095
        machine.mem_map(begin, ((base + size + 4095) & ~4095) - begin)
        machine.mem_write(base, img.data[raw:raw + count])
    machine.mem_map(0x70000000, 0x20000)
    machine.mem_write(COOKIE, b'\xc3')

    def put(p, value):
        machine.mem_write(p, struct.pack('<I', value & 0xffffffff))

    preset = bytes(SNAPSHOT)
    table = {}
    faults = []
    for op in sorted(handlers):
        handler = handlers[op]
        cases = []
        for value, variant, refs in GRID:
            flags = 7 | (0xc0009000 if variant else 0x40000000)
            machine.mem_write(VM, preset)
            put(VM + 0x18, flags)
            put(VM + 0x1c, 0xbc0000 if variant else 0x820000)
            put(VM + 0x4ac, value)
            put(VM + 0x4b0, value ^ 2)
            put(VM + 0x28, CODE)
            put(VM + 0x60, 0x3f800000)
            put(VM + 0x64, 0xc0200000)
            put(0x494720, 0x3f800000)
            before = bytes(machine.mem_read(VM, SNAPSHOT))
            machine.mem_write(CODE, bytes(64))
            machine.mem_write(CODE, struct.pack('<hHhHII', op, 12, 0, refs,
                                               REFERENCE_INDEX if refs else value, value ^ 2))
            machine.reg_write(UC_X86_REG_ESP, STACK)
            machine.reg_write(UC_X86_REG_EBP, STACK)
            machine.reg_write(UC_X86_REG_EDI, CODE)
            machine.reg_write(UC_X86_REG_EBX, VM)
            machine.reg_write(UC_X86_REG_XMM1, 0xbf800000)
            machine.reg_write(UC_X86_REG_FPCW, 0x37f)
            try:
                machine.emu_start(handler, LOOP, count=100000)
                landing = machine.reg_read(UC_X86_REG_EIP)
            except Exception as error:  # a handler that expects a caller frame
                faults.append({'op': op, 'handler': hex(handler), 'error': str(error)[:60]})
                break
            if landing != LOOP:
                faults.append({'op': op, 'handler': hex(handler), 'landing': hex(landing)})
                break
            after = bytes(machine.mem_read(VM, SNAPSHOT))
            position = struct.unpack('<I', after[0x28:0x2c])[0]
            slots = {}
            for offset in range(0, SNAPSHOT, 4):
                if after[offset:offset + 4] != before[offset:offset + 4]:
                    slots[f'0x{offset:x}'] = after[offset:offset + 4].hex()
            cases.append({'in': [value, variant, refs], 'delta': (position - CODE) & 0xffffffff,
                         'slots': slots})
        table[op] = {'handler': hex(handler), 'isDefault': handler == default, 'cases': cases}
    report = dict(game='th16', scope='Every dispatched handler of this title, reduced to the slots it '
                                   'changed and how far it moved the position. No renderer claim.',
                 executableSha256=hashlib.sha256(img.data).hexdigest(),
                 measured=dict(loop=hex(LOOP), cookie=hex(COOKIE), snapshot=SNAPSHOT,
                              defaultHandler=hex(default), entries=len(handlers)),
                 preset={f'0x{off:x}': f'{val:08x}' for off, val in PRESET},
                 grid=[list(g) for g in GRID], table=table, faults=faults)
    out = ROOT / 'artifacts/th16/anm-signatures.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, separators=(',', ':')) + '\n', encoding='utf-8')
    footprints = {}
    for op, row in table.items():
        if row['isDefault']:
            continue
        touched = frozenset().union(*[frozenset(c['slots']) for c in row['cases']]) if row['cases'] else frozenset()
        footprints.setdefault(tuple(sorted(touched)), []).append(op)
    distinct = len({row['handler'] for row in table.values()})
    print(f'{len(table)} handlers measured with {len(GRID)} inputs each; {len(faults)} faults; '
          f'{distinct} distinct handler addresses; {sum(1 for r in table.values() if r["isDefault"])} on the default path.')
    print('footprint classes (slots -> handlers): ' +
          '  '.join(f'[{",".join(k)}]:{len(v)}' for k, v in sorted(footprints.items(), key=lambda kv: -len(kv[1]))[:8]))
    deltas = {}
    for op, row in table.items():
        if row['isDefault']:
            continue
        deltas.setdefault(tuple(sorted({c['delta'] for c in row['cases']})), []).append(op)
    print('position deltas: ' + '  '.join(f'{k}:{len(v)}' for k, v in sorted(deltas.items(), key=lambda kv: -len(kv[1]))[:6]))
    print('distinct footprint classes for the non-default handlers:', len(footprints))


if __name__ == '__main__':
    main()
