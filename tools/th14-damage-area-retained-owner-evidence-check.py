"""Prove retail damage allocators preserve owner memory but clear callbacks.

Runs the original two x86 allocators in isolated Unicorn memory. Movement
constructors and memset are controlled boundaries; no native child is started.
"""
import hashlib
import importlib
import json
import struct
from pathlib import Path

import capstone
import unicorn
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_XMM2, UC_X86_REG_XMM3, UC_X86_REG_MXCSR, UC_X86_REG_FPCW, UC_X86_REG_FPSW, UC_X86_REG_FPTAG

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    image = importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    instruction_receipts = []
    for kind, address, length, clear_at in (
        ('circle', 0x450130, 0x140, 0x45024e),
        ('rectangle', 0x450270, 0x1a0, 0x4503e9),
    ):
        instructions = list(md.disasm(image.read(address, length), address))
        clear = next(row for row in instructions if row.address == clear_at)
        assert bytes(clear.bytes) == bytes.fromhex('c787a000000000000000')
        assert clear.mnemonic == 'mov' and clear.op_str == 'dword ptr [edi + 0xa0], 0'
        owner_writes = [row for row in instructions if row.mnemonic.startswith(('mov', 'stos'))
                        and '[edi + 0x9c]' in row.op_str.split(',')[0]]
        assert not owner_writes
        instruction_receipts.append(dict(kind=kind, address=hex(address), bytes=length,
            functionSha256=SHA(image.read(address, length)), callbackClearAddress=hex(clear_at),
            callbackClearHex=bytes(clear.bytes).hex(), callbackClearAssembly=clear.mnemonic + ' ' + clear.op_str,
            ownerField='area+0x9c', callbackField='area+0xa0', ownerWritesInDisassembledAllocator=0))

    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, start, size, raw, amount in image.sections:
        page = start & ~4095
        machine.mem_map(page, ((start + size + 4095) & ~4095) - page)
        machine.mem_write(start, image.data[raw:raw + amount])
    end = 0x70000000
    player, stack, position = end + 0x1000, end + 0x3f000, end + 0x30000
    machine.mem_map(end, 0x40000)
    put = lambda p, value: machine.mem_write(p, struct.pack('<I', value & 0xffffffff))
    get = lambda p: struct.unpack('<I', machine.mem_read(p, 4))[0]
    bits = lambda value: struct.unpack('<I', struct.pack('<f', value))[0]

    def boundary(_, address, size, user):
        if address == 0x48f980:
            sp = machine.reg_read(UC_X86_REG_ESP)
            p = get(sp + 4)
            machine.mem_write(p, bytes(get(sp + 12)))
            machine.reg_write(UC_X86_REG_EAX, p)

    for address in (0x403cd0, 0x403df0, 0x48f980):
        machine.mem_write(address, b'\xc3')
        machine.hook_add(UC_HOOK_CODE, boundary, begin=address, end=address)
    rows = []
    for kind in ('circle', 'rectangle'):
        for cursor, occupied in ((0, 0), (177, 0), (254, 3), (256, 2)):
            for retained_owner in (0, 0x12345678):
                for z_word in (0, bits(2.), 0x004db508):
                    machine.mem_write(end, bytes(0x3e000))
                    put(player + 0xde14, cursor)
                    put(0x4db67c, player)
                    for slot in range(256):
                        area = player + 0xde18 + slot * 0xa4
                        put(area + 0x10, 0x8006)
                        put(area + 0x9c, retained_owner)
                        put(area + 0xa0, 0x87654321)
                        put(area + 0x34, 0xabcdef01)
                    for step in range(occupied):
                        area = player + 0xde18 + ((cursor % 256 + step) % 256) * 0xa4
                        put(area + 0x10, 0x8007)
                    for offset, value in ((0, bits(-12.5)), (4, bits(400.)), (8, z_word)):
                        put(position + offset, value)
                    put(0x4d8f58, bits(1.))
                    put(stack, end)
                    put(stack + 4, position)
                    if kind == 'circle':
                        put(stack + 8, 30)
                        put(stack + 12, 150)
                    else:
                        put(stack + 8, bits(0.))
                        put(stack + 12, 30)
                        put(stack + 16, 150)
                    machine.reg_write(UC_X86_REG_ESP, stack)
                    machine.reg_write(UC_X86_REG_ECX, player)
                    machine.reg_write(UC_X86_REG_XMM2, bits(32.))
                    machine.reg_write(UC_X86_REG_XMM3, bits(16.))
                    machine.reg_write(UC_X86_REG_MXCSR, 0x1f80)
                    machine.emu_start(0x450130 if kind == 'circle' else 0x450270, end, count=20000)
                    area = machine.reg_read(UC_X86_REG_EAX)
                    slot = (area - player - 0xde18) // 0xa4
                    assert slot == (cursor % 256 + occupied) % 256
                    assert get(area + 0x9c) == retained_owner and get(area + 0xa0) == 0
                    assert get(area + 0x34) == z_word
                    rows.append(dict(kind=kind, cursor=cursor, occupied=occupied, selectedSlot=slot,
                        beforeOwner=retained_owner, afterOwner=get(area + 0x9c), beforeCallback=0x87654321,
                        afterCallback=get(area + 0xa0), inputPositionZWord=z_word, outputPositionZWord=get(area + 0x34)))
    assert len(rows) == 48
    polar_rows = []
    for scratch_word in (0, 0x004db508, 366010528):
        put(position + 8, scratch_word)
        put(stack, end)
        put(stack + 4, bits(.37))
        put(stack + 8, bits(112.))
        machine.reg_write(UC_X86_REG_ESP, stack)
        machine.reg_write(UC_X86_REG_ECX, position)
        machine.reg_write(UC_X86_REG_FPCW, 0x37f)
        machine.reg_write(UC_X86_REG_FPSW, 0)
        machine.reg_write(UC_X86_REG_FPTAG, 0xffff)
        machine.emu_start(0x4144a0, end, count=20000)
        assert get(position + 8) == scratch_word
        polar_rows.append(dict(beforeZWord=scratch_word, afterZWord=get(position + 8),
                               outputXWord=get(position), outputYWord=get(position + 4)))
    xy = [(0x4144b2, 'd918'), (0x4144b7, 'd95804')]
    for address, value in xy:
        assert image.read(address, len(bytes.fromhex(value))) == bytes.fromhex(value)
    assert image.read(0x41389e, 5) == bytes.fromhex('e8fd0b0000')
    assert image.read(0x4138ca, 5) == bytes.fromhex('f30f5845d4')
    direct_scratch = [row for row in md.disasm(image.read(0x413630, 0x26e), 0x413630)
                      if '[ebp - 0x2c]' in row.op_str.split(',')[0]]
    assert not direct_scratch
    scratch_evidence = dict(helper='0x4144a0', helperSha256=SHA(image.read(0x4144a0, 0x20)),
        helperWrites=['output+0', 'output+4'], helperRetainsOutputPlus8=True,
        caller='0x413630', callAddress='0x41389e', callHex='e8fd0b0000',
        outputAddress='ebp-0x34', callerZReadAddress='0x4138ca', callerZReadHex='f30f5845d4',
        callerZReadAssembly='addss xmm0, dword ptr [ebp-0x2c]',
        earlierDirectScratchDestinationWrites=0, controlledPolarCases=polar_rows,
        scope='Original polar helper leaves its third output word untouched; the ReimuA caller reads that word into Z. No directEBP-0x2c destination write exists in the disassembled prologue-to-call range. This supports an unwritten stack-input explanation but does not dynamically establish the actual native stack writers responsible for the8 continuous-capture Z differences.')
    names = [
        'runtimes/th12/th12_web/cpp/game/ShotTh14.cpp',
        'runtimes/th12/th12_web/cpp/game/ShotDamageTh14.cpp',
        'runtimes/th12/th12_web/cpp/game/ShotManager.hpp',
        'tools/th-anm-handlers.py', 'tools/th12-pe.py',
    ]
    bindings = {name: dict(bytes=(ROOT / name).stat().st_size, sha256=SHA((ROOT / name).read_bytes())) for name in names}
    production = (ROOT / names[0]).read_text()
    assert production.count('th14_area_owners[index]=nullptr') == 6
    result = dict(diagnosticEvidenceVerified=True, completeGame=False, nativeEquivalent=False,
        nativeExecutableSha256=SHA(image.data), allocatorCases=len(rows), instructions=instruction_receipts,
        allOwnersRetained=True, allCallbacksCleared=True, allPositionZInputsCopiedExactly=True,
        currentProductionExplicitNullStores=6, rows=rows, retainedPolarScratch=scratch_evidence, bindings=bindings,
        emulatorVersions=dict(unicorn=unicorn.__version__, capstone=capstone.__version__),
        verifierSha256=SHA(Path(__file__).read_bytes()),
        scope='Original450130 circle and450270 rectangle allocators execute in isolated x86 emulation with controlled movement constructors and memset.48 allocations cover clean/reused/wrapped slots, null/non-null retained owner words, and three raw Z inputs. Both allocators preserve area+0x9c while explicitly clearing+a0 callback, and copy input Z exactly. Productioncurrently clears owner in six death/Bomb/explosion allocation wrappers; that extra clearing is not supported by these original allocator stores. This is allocator-memory evidence, not a proof of valid owner lifetime, callback delivery, whole gameplay, actual native child startup or pixels/audio. The later continuous-native Z scratch changes are retained differences and are not resolved by this allocator control.')
    output = ROOT / 'docs/porting/th14-damage-area-retained-owner-verified-oct14.json'
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('diagnosticEvidenceVerified', 'allocatorCases',
        'allOwnersRetained', 'allCallbacksCleared', 'allPositionZInputsCopiedExactly', 'currentProductionExplicitNullStores')}))


if __name__ == '__main__':
    main()
