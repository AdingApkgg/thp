"""Observe original damage-area Z consumers in controlled 2D collision cases.

Runs original451430 and collision helpers in isolated Unicorn memory. No native
child, input recording, production code, owner evidence, or old report changes.
"""
import hashlib
import importlib
import itertools
import json
import struct
from pathlib import Path

import capstone
import unicorn
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_READ
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_XMM3, UC_X86_REG_FPCW, UC_X86_REG_FPSW, UC_X86_REG_FPTAG, UC_X86_REG_MXCSR

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda value: hashlib.sha256(value).hexdigest()


def main():
    image = importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, raw, amount in image.sections:
        page = address & ~4095
        machine.mem_map(page, ((address + size + 4095) & ~4095) - page)
        machine.mem_write(address, image.data[raw:raw + amount])
    end = 0x70000000
    player, manager, resource = end + 0x1000, end + 0x20000, end + 0x21000
    target, size_pointer, bomb_out, last_hit = end + 0x22000, end + 0x22020, end + 0x22040, end + 0x22060
    stack = end + 0xff000
    machine.mem_map(end, 0x100000)
    area = player + 0xde18
    put = lambda address, value: machine.mem_write(address, struct.pack('<I', value & 0xffffffff))
    get = lambda address: struct.unpack('<I', machine.mem_read(address, 4))[0]
    bits = lambda value: struct.unpack('<I', struct.pack('<f', value))[0]
    floats = lambda address, *values: machine.mem_write(address, struct.pack('<' + 'f' * len(values), *values))
    reads, all_reads = set(), set()

    def observe(_, access, address, size, value, user):
        for name, watched in (('areaPositionZ', area + 0x34), ('targetPositionZ', target + 8)):
            if address <= watched < address + size:
                entry = (name, machine.reg_read(UC_X86_REG_EIP), address, size)
                reads.add(entry)
                all_reads.add(entry)

    machine.hook_add(UC_HOOK_MEM_READ, observe)
    rows = []
    for area_flags, target_rectangle, area_z, target_z in itertools.product(
            (1, 3), (0, 1), (0, 0x004db508, 366010528, 0x7fc00000), (0, 0x3f800000, 0x7fc00000)):
        reads.clear()
        machine.mem_write(player, bytes(0x19000))
        machine.mem_write(manager, bytes(0x100))
        machine.mem_write(stack - 0x3000, bytes(0x3100))
        put(0x4db67c, player)
        put(0x4db52c, manager)
        put(player + 0x688, resource)
        put(player + 0x68c, 7)
        put(player + 0x690, 8)
        put(resource + 0x28, 9999)
        put(0x4f5830, 0)
        fields = [(0x10, area_flags), (0x14, bits(56.)), (0x1c, 0), (0x24, bits(128.)),
                  (0x28, bits(96.)), (0x2c, 0), (0x30, bits(100.)), (0x34, area_z),
                  (0x70, 7), (0x74, 8), (0x78, bits(8.)), (0x84, 150), (0x88, 0),
                  (0x8c, 9999999), (0x90, 1), (0x94, 0), (0x9c, 0), (0xa0, 0)]
        for offset, value in fields:
            put(area + offset, value)
        floats(target, 0, 100)
        put(target + 8, target_z)
        floats(size_pointer, 32, 32)
        put(bomb_out, 77)
        floats(last_hit, 111, 222, 333)
        arguments = [target, size_pointer if target_rectangle else 0, bits(16.), bomb_out, last_hit, 0, 73, 0]
        put(stack, end)
        for index, value in enumerate(arguments):
            put(stack + 4 + index * 4, value)
        machine.reg_write(UC_X86_REG_ESP, stack)
        machine.reg_write(UC_X86_REG_XMM3, 0)
        machine.reg_write(UC_X86_REG_FPCW, 0x37f)
        machine.reg_write(UC_X86_REG_FPSW, 0)
        machine.reg_write(UC_X86_REG_FPTAG, 0xffff)
        machine.reg_write(UC_X86_REG_MXCSR, 0x1f80)
        machine.emu_start(0x451430, end, count=200000)
        assert machine.reg_read(UC_X86_REG_EIP) == end
        result = [machine.reg_read(UC_X86_REG_EAX), get(bomb_out), get(last_hit), get(last_hit + 4),
                  get(last_hit + 8), get(0x4f5830), get(area + 0x88)]
        assert result == [150, 0, 0, bits(100.), area_z, 2, 150]
        assert reads == {('areaPositionZ', 0x45168b, area + 0x34, 4)}
        rows.append(dict(areaShape='circle' if area_flags & 2 else 'rectangle',
            targetShape='rectangle' if target_rectangle else 'circle', areaFlags=area_flags,
            areaZWord=area_z, targetZWord=target_z, returnedDamage=result[0], bombOutput=result[1],
            lastHitWords=result[2:5], scoreUnits=result[5], accumulatedDamage=result[6]))
    assert len(rows) == 48
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    instructions = []
    for address, raw in ((0x45168b, '8b46c0'), (0x45168e, '660fd602'), (0x451692, '894208')):
        bytecode = bytes.fromhex(raw)
        assert image.read(address, len(bytecode)) == bytecode
        row = next(md.disasm(bytecode, address))
        instructions.append(dict(address=hex(address), hex=raw, assembly=row.mnemonic + ' ' + row.op_str))
    bindings = {name: dict(bytes=(ROOT / name).stat().st_size, sha256=SHA((ROOT / name).read_bytes()))
                for name in ('tools/th-anm-handlers.py', 'tools/th12-pe.py',
                             'runtimes/th12/th12_web/cpp/game/ShotDamageTh14.cpp',
                             'runtimes/th12/th12_web/cpp/game/ShotTh14.cpp')}
    result = dict(diagnosticEvidenceVerified=True, completeGame=False, nativeEquivalent=False,
        nativeExecutableSha256=SHA(image.data), collectorAddress='0x451430', collectorFunctionBytes=0x330,
        collectorFunctionSha256=SHA(image.read(0x451430, 0x330)), collectorCases=len(rows),
        originalInstructionsUnmodified=True, controlledCallbacksDisabled=True, controlledBombClassInactive=True,
        stationaryAreaPositionXY=[0, 100], stationaryTargetPositionXY=[0, 100], areaRadius=56,
        areaRectangleSize=[128, 96], targetCircleRadius=16, targetRectangleSize=[32, 32],
        areaAngle=0, targetAngle=0, advancedFrame=True, probe=False, damageCap=9999,
        damage=150, period=1, previousTimer=7, currentTimer=8,
        allDamageAndScoreIndependentOfTestedZWords=True, targetZReadCount=0,
        areaZReadInstructions=[hex(ip) for name, ip, address, size in sorted(all_reads)],
        areaZCopiedToLastHitOutput=True, observableZOutputRetained=True, instructions=instructions,
        rows=rows, bindings=bindings, emulatorVersions=dict(unicorn=unicorn.__version__, capstone=capstone.__version__),
        verifierSha256=SHA(Path(__file__).read_bytes()),
        scope='48 controlled original451430 collector calls execute original collision helpers with stationary overlapping circular/rectangular areas and circular/rectangular targets. AreaZ varies across zero, two captured raw words and quietNaN; targetZ varies across zero,1.0 and quietNaN. Selected damage, score and accumulated damage are identical, and targetZ is never read in these calls. AreaZ is read at45168b and copied to caller lastHit+8 at451692, so Z is still observable output and is not globally unused. Original executable instructions are unmodified. Area callbacks are disabled, Bomb class inactive, angles zero and frame advanced; this is not all geometry, callback/effect/render, owner-memory, ordinary startup or whole-game equivalence. The8 continuous-native Z failures remain unmodified in their separate source-bound reports; this experiment neither copies host pointer bits into production nor masks those failures.')
    output = ROOT / 'docs/porting/th14-damage-area-z-consumer-verified-oct14.json'
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('diagnosticEvidenceVerified', 'collectorCases',
        'allDamageAndScoreIndependentOfTestedZWords', 'targetZReadCount', 'areaZCopiedToLastHitOutput')}))


if __name__ == '__main__':
    main()
