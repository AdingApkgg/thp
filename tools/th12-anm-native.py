"""Observe original TH12 ANM handlers in Unicorn, in the shape of the other five oracles.

Title 12 has the oldest ANM ABI of the six and the smallest domain: a flat table of 112 entries
from the -1 sentinel to opcode 110, dispatch `movsx eax, word [esi]; inc eax; cmp eax, 0x6f;
ja default; jmp dword ptr [eax*4 + 0x458730]` at 0x45569d. The oracle's constants are the ones
tools/th12-anm-plan.py measured off the image and confirmed live - the boundary 0x455686, the VM in
EDI, the script pointer at [edi+0x3f0] and the script itself in ESI - and this generator holds
them to a second route as well: the boundary is looked for in the default handler's own tail, which
is how the oracles of 16, 17 and 18 found theirs.

Every real handler of the table, over the value and variant sweep the other titles use, with the two
fields the interpreter itself reads before the handler (`[edi+0x3c4]` and `[edi+0x6c]`) carrying
the variant. A case carries `before` and `context`, the whole snapshot on both sides of the call,
so the checker compares what a case changes rather than what the corpus seeded.

Usage: py -3 tools/th12-anm-native.py [--quick]
"""
import argparse, hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDI, UC_X86_REG_EBP,
                              UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_FPCW, UC_X86_REG_FPSW,
                              UC_X86_REG_FPTAG)

ROOT = Path(__file__).resolve().parents[1]
VM, CODE, STACK = 0x70100000, 0x70110000, 0x7011f000
SNAPSHOT = 0x700
GUARD = 0x45569d
BOUNDARY_MEASURED = 0x455686      # tools/th12-anm-plan.py: the guard minus 0x17
VM_ARG_OFFSET = 0x3f0             # where the interpreter loads the script pointer from
VALUES = [0, 1, 2, 3, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 29, 30, 31, 32, 255, -1]


def tail_targets(img, entry, span=64):
    """Every jump target in the first `span` bytes of a handler body, without a disassembler."""
    out = []
    at = entry
    while at < entry + span:
        byte = img.read(at, 1)[0]
        if byte == 0xeb:
            rel = struct.unpack('<b', bytes([img.read(at + 1, 1)[0]]))[0]
            out.append(((at + 2 + rel) & 0xffffffff, 'jmp short'))
            at += 2
            continue
        if byte == 0xe9:
            rel = struct.unpack('<i', bytes(img.read(at + 1, 4)))[0]
            out.append(((at + 5 + rel) & 0xffffffff, 'jmp near'))
            at += 5
            continue
        if byte == 0x0f and 0x80 <= img.read(at + 1, 1)[0] <= 0x8f:
            rel = struct.unpack('<i', bytes(img.read(at + 2, 4)))[0]
            out.append(((at + 6 + rel) & 0xffffffff, 'jcc'))
            at += 6
            continue
        at += 1
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true', help='one value per handler')
    args = parser.parse_args()
    img, table, default = importlib.import_module('th-anm-handlers').handlers(12)
    assert img.read(GUARD, 7) == bytes.fromhex('0fbf064083f86f'), 'the dispatch guard moved'
    real = sorted(op for op, entry in table.items() if entry != default)
    targets = tail_targets(img, default)
    inside = [(address, kind) for address, kind in targets
              if 0x454000 <= address <= 0x460000]
    print('  th12 anchors: %d table entries, %d real handlers, default 0x%x' %
          (len(table), len(real), default))
    print('    boundary held by the plan: 0x%x (the guard 0x%x minus 0x17)' %
          (BOUNDARY_MEASURED, GUARD))
    print('    the default handler\'s tail jumps to: %s' %
          (', '.join('0x%x %s' % t for t in targets) or 'none in reach'))
    print('    of those inside the interpreter region: %s' %
          (', '.join('0x%x %s' % t for t in inside) or 'none'))
    print('    the plan\'s boundary among the tail targets: %s' %
          any(address == BOUNDARY_MEASURED for address, _ in targets))

    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, n in img.sections:
        begin = base & ~4095
        m.mem_map(begin, ((base + size + 4095) & ~4095) - begin)
        m.mem_write(base, img.data[raw:raw + n])
    m.mem_map(VM, 0x20000)
    table_values = table  # the census is the corpus's coverage claim

    cases = []
    values = VALUES[:1] if args.quick else VALUES
    for op in real:
        for value in values:
            for variant in (0, 1):
                refs = variant & 1
                arg = 10000 if refs else (value & 0xffffffff)
                arg2 = 10001 if refs else ((value ^ 2) & 0xffffffff)
                m.mem_write(VM, bytes(SNAPSHOT))
                m.mem_write(VM + 0x3c4, struct.pack('<H', 1 if variant else 0))
                m.mem_write(VM + 0x6c, struct.pack('<f', 1.5 if variant else 0.0))
                m.mem_write(VM + VM_ARG_OFFSET, struct.pack('<I', CODE))
                m.mem_write(CODE, struct.pack('<hHhHII', op, 12, 0, refs, arg, arg2))
                m.reg_write(UC_X86_REG_EDI, VM)
                m.reg_write(UC_X86_REG_ESI, CODE)
                m.reg_write(UC_X86_REG_EBX, VM)
                m.reg_write(UC_X86_REG_ECX, VM)
                m.reg_write(UC_X86_REG_ESP, STACK)
                m.reg_write(UC_X86_REG_EBP, STACK)
                m.reg_write(UC_X86_REG_FPCW, 0x37f)
                m.reg_write(UC_X86_REG_FPSW, 0)
                m.reg_write(UC_X86_REG_FPTAG, 0xffff)
                before = m.mem_read(VM, SNAPSHOT).hex()
                fault = None
                try:
                    m.emu_start(table[op], BOUNDARY_MEASURED, count=200000)
                    landing = m.reg_read(UC_X86_REG_EIP)
                    if landing != BOUNDARY_MEASURED:
                        fault = 'landed at 0x%x' % landing
                except Exception as error:
                    fault = str(error)[:48]
                cases.append(dict(op=op, value=value, variant=variant, refs=refs, arg=arg,
                                 arg2=arg2, fault=fault, before=before,
                                 context=m.mem_read(VM, SNAPSHOT).hex()))
    faulted = sum(1 for case in cases if case['fault'])
    script_after = [struct.unpack('<I', bytes.fromhex(case['context'])[VM_ARG_OFFSET:VM_ARG_OFFSET + 4])[0]
                    for case in cases if not case['fault']]
    moved = sum(1 for pointer in script_after if pointer != CODE)
    report = dict(
        game='th12',
        scope='The context on both sides of one handler call, at the dispatch boundary. The native '
              'layout is TH12\'s own ABI; the plan is measured in tools/th12-anm-plan.py and '
              'confirmed live. No renderer and no complete-game equivalence is claimed.',
        executableSha256=hashlib.sha256(img.data).hexdigest(),
        measured=dict(loop=hex(BOUNDARY_MEASURED), guard=hex(GUARD),
                      loopRelation='the dispatch guard minus 0x17, and the TH13 oracle uses the '
                                   'same relation',
                      snapshot=SNAPSHOT, defaultHandler=hex(default),
                      positionSlot=hex(VM_ARG_OFFSET), codeBase=hex(CODE),
                      tableEntries=len(table), realHandlers=len(real),
                      callConvention='the VM in EDI, the script pointer at [edi+0x3f0], the '
                                     'script in ESI',
                      measuredFrom='th12.exe, read off the image',
                      coverage='every real handler of the flat table'),
        realHandlers=len(real),
        cases=cases)
    out = ROOT / 'artifacts/th12/anm-native.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('  %d cases over %d real handlers, %d faulted, %d advanced the script pointer past the '
          'instruction' % (len(cases), len(real), faulted, moved))
    print('  written: %s (%d bytes)' % (out.relative_to(ROOT), out.stat().st_size))
    del table_values


if __name__ == '__main__':
    main()
