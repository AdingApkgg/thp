"""Bounded retail 452050 experiment with explicitly controlled scratch-stack Z.

This is a Unicorn component experiment, not a live game-stack observation or a
proof about later animation lifecycle. Allocation, sound and interrupt services
are recorded return stubs, as in th14-shot-hit-native.py.
"""
import argparse
import hashlib
import importlib
import itertools
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_READ
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
EXE_SHA = 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'


def observe():
    image, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
    assert SHA(image.data) == EXE_SHA
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, length in image.sections:
        start = base & ~4095
        machine.mem_map(start, ((base + size + 4095) & ~4095) - start)
        machine.mem_write(base, image.data[raw:raw + length])
    end, shot, area, player, visual, stack = (
        0x70000000, 0x70001000, 0x70002000, 0x70010000, 0x70030000, 0x700ff000)
    machine.mem_map(end, 0x100000)
    scratch_z = stack - 16  # entry push ebp; ebp = entry ESP - 4; local = ebp - 12
    get = lambda p: struct.unpack('<I', machine.mem_read(p, 4))[0]
    put = lambda p, value: machine.mem_write(p, struct.pack('<I', value & 0xffffffff))
    floats = lambda p, *values: machine.mem_write(p, struct.pack('<' + 'f' * len(values), *values))
    accesses, effects, services = [], [], []

    def memory_hook(_machine, access, address, size, value, _user):
        accesses.append(dict(pc=machine.reg_read(UC_X86_REG_EIP),
                             operation='read' if access == UC_MEM_READ else 'write',
                             address=address, size=size))

    machine.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory_hook,
                     begin=scratch_z, end=scratch_z + 3)

    def service_hook(_machine, pc, _size, _user):
        sp = machine.reg_read(UC_X86_REG_ESP)
        if pc == 0x47f140:
            services.append(['interrupt', get(sp + 8)])
        elif pc == 0x46e470:
            services.append(['sound', get(sp + 4), machine.reg_read(UC_X86_REG_XMM2) & 0xffffffff])
        else:
            p = get(sp + 12)
            effects.append([get(p), get(p + 4), get(p + 8), get(sp + 16)])
            services.append(['effect', get(sp + 8), get(sp + 20), get(sp + 24), get(sp + 28)])

    for pc, cleanup in [(0x47f140, 8), (0x46e470, 4), (0x47ed10, 28)]:
        machine.mem_write(pc, b'\xc2' + struct.pack('<H', cleanup))
        machine.hook_add(UC_HOOK_CODE, service_hook, begin=pc, end=pc)

    # These are declared synthetic stack inputs. None is copied from a live VM.
    poisons = [0, 0x00800000, 0x0d800000, 0x3f000000, 0x3f800000,
               0xbf800000, 0x67800000]
    cases = []
    for age, power, seed, radius in itertools.product([8, 16, 24, 32], [0, 4],
                                                     [0, 0x9630, 0xffff], [0., 32.]):
        baseline = None
        for poison in poisons:
            accesses.clear(); effects.clear(); services.clear()
            for p, size in [(shot, 0x100), (area, 0x100), (player, 0x19000),
                            (stack - 0x2000, 0x2100)]:
                machine.mem_write(p, bytes(size))
            put(scratch_z, poison)
            put(0x4db67c, player); put(0x4db53c, visual); put(visual + 0x10, visual + 0x100)
            put(shot + 0x14, 73); put(shot + 0xc0, area)
            put(shot + 0x18, age - 1); put(shot + 0x1c, age)
            floats(shot + 0x54, 17, 123, 0); floats(shot + 0x6c, 8, -1.25)
            floats(shot + 0xb8, 8); put(shot + 0x40, 9); put(shot + 0x44, 10)
            floats(shot + 0x48, 10); put(shot + 0x4c, 0x4d8f58); put(shot + 0x50, 1)
            floats(area + 0x14, radius); put(area + 0x84, 19)
            put(player + 0x184b8, 1234); put(0x4f5858, power * 40); put(0x4f5860, 40)
            put(0x4db508, seed); put(0x4db50c, 123); floats(0x4d8f58, 1)
            put(stack, end); machine.reg_write(UC_X86_REG_ESP, stack)
            machine.reg_write(UC_X86_REG_ECX, shot)
            for register, value in [(UC_X86_REG_FPCW, 0x37f), (UC_X86_REG_FPSW, 0),
                                    (UC_X86_REG_FPTAG, 0xffff), (UC_X86_REG_MXCSR, 0x1f80)]:
                machine.reg_write(register, value)
            machine.emu_start(0x452050, end, count=100000)
            assert machine.reg_read(UC_X86_REG_EIP) == end
            effect_services = [row for row in services if row[0] == 'effect']
            assert len(effects) == len(effect_services) == 1
            assert effect_services[0][1] == 149 and effects[0][2] == poison
            assert accesses == [dict(pc=0x4520f2, operation='read', address=scratch_z, size=4),
                                dict(pc=0x4520f7, operation='write', address=scratch_z, size=4)]
            state = [get(shot + 0x6c), get(shot + 0xb8),
                     *[get(shot + 0x40 + n * 4) for n in range(3)],
                     get(player + 0x184b8), get(0x4db508), get(0x4db50c),
                     machine.reg_read(UC_X86_REG_EAX), effects[0][0], effects[0][1], effects[0][3]]
            comparison = [state, [row[:] for row in services]]
            if baseline is None:
                baseline = comparison
            assert comparison == baseline, 'Declared stack Z changed another observed result'
            cases.append(dict(age=age, power=power, seed=seed, radius=radius,
                              syntheticScratchZWord=poison, readsBeforeFirstWrite=1,
                              factoryZEqualsDeclaredScratch=True,
                              remainingSelectedStateAndServicesEqual=True))
    return dict(schema='th14/shot-hit-scratch-z-component/1', executableSha256=EXE_SHA,
                toolSha256=SHA(Path(__file__).read_bytes()), cases=len(cases),
                inputCombinations=len(cases)//len(poisons), declaredScratchWords=poisons,
                firstScratchReadPc='0x4520f2', firstScratchWritePc='0x4520f7',
                originalPolarHelper='0x454510', factoryBoundary='0x47ed10', factoryScript=149,
                everyCaseReadsUnwrittenScratch=True, everyFactoryZEqualsDeclaredInput=True,
                allOtherSelectedResultsInvariant=True, caseSummarySha256=SHA(json.dumps(cases, sort_keys=True).encode()),
                limitations=['Controlled Unicorn stack inputs; no actual live stack producer or allocation address is inferred.',
                             'Shot Z is declared zero. Only the stated age/power/seed/radius combinations are covered.',
                             'Three service boundaries return through recorded stubs; the actual factory is not executed.',
                             'No child creation, later lifecycle, visual equivalence or full campaign pass is proved.'],
                productionChanged=False, completeGame=False, nativeEquivalent=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = observe()
    output = ROOT/'docs/porting/th14-shot-hit-stack-z-component-oct26.json'
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ['cases', 'everyCaseReadsUnwrittenScratch',
                                                   'everyFactoryZEqualsDeclaredInput',
                                                   'allOtherSelectedResultsInvariant']}))


if __name__ == '__main__':
    main()
