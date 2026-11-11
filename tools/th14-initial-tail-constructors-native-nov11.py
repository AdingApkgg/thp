"""Execute TH14's Laser/Pause/ScorePopup factories and native registration.

CRT allocation/memset and diagnostic logging are delivery boundaries. The
factories, object initializers, cached resource lookup, sprite bind and both
registry insertion routines execute original instructions. No game process,
graphics/audio backend, readiness schedule or RNG adjustment is used.
"""
from pathlib import Path
import hashlib
import importlib
import json
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / 'artifacts/th14/initial-tail-constructors-nov11'


def main():
    image, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
    digest = hashlib.sha256(image.data).hexdigest()
    assert digest == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, offset, count in image.sections:
        start = address & ~4095
        machine.mem_map(start, ((address + size + 4095) & ~4095) - start)
        machine.mem_write(address, image.data[offset:offset + count])
    base, manager = 0x70000000, 0x71000000
    machine.mem_map(base, 0x100000)
    machine.mem_map(manager, 0xc00000)
    registry, ascii_owner, resource, atlas = base + 0x1000, base + 0x2000, base + 0x22000, base + 0x24000
    stack, terminal = base + 0xef000, base + 0xff000
    heap = base + 0x40000
    allocations, registrations, cached_lookups, sprite_binds, rng_writes = [], [], [], [], []
    get = lambda p: struct.unpack('<I', machine.mem_read(p, 4))[0]
    put = lambda p, v: machine.mem_write(p, struct.pack('<I', v & 0xffffffff))
    f32 = lambda v: struct.unpack('<I', struct.pack('<f', v))[0]
    put(0x4db51c, registry)
    put(0x4db520, ascii_owner)
    put(ascii_owner + 0x191e4, resource)
    put(0x4f56cc, manager)
    put(manager + 0xbc7b0c + 7 * 4, resource)
    put(resource + 0x108, 1)
    put(resource + 0x11c, atlas)
    for index in range(300):
        sprite = atlas + index * 72
        for offset, value in [(0x1c, 256), (0x20, 512), (0x24, 0), (0x28, 1),
                              (0x2c, 0), (0x30, 1), (0x34, 16), (0x38, 8), (0x3c, 1), (0x40, 1)]:
            put(sprite + offset, f32(value))
    put(0x4d8f58, f32(1))
    machine.mem_write(0x4f5815, b'\0')
    initial_rng = bytes.fromhex('3412000078560000bc9a0000f0de0000')
    machine.mem_write(0x4db508, initial_rng)

    def boundary(uc, pc, size, _):
        nonlocal heap
        sp = uc.reg_read(UC_X86_REG_ESP)
        if pc == 0x4854af:
            size = get(sp + 4)
            pointer = heap
            heap += (size + 15) & ~15
            assert heap < stack - 0x10000
            allocations.append(dict(bytes=size, pointer=pointer))
            uc.reg_write(UC_X86_REG_EAX, pointer)
        elif pc == 0x48f980:
            pointer, value, length = get(sp + 4), get(sp + 8), get(sp + 12)
            assert base <= pointer < pointer + length <= heap
            uc.mem_write(pointer, bytes([value & 255]) * length)
            uc.reg_write(UC_X86_REG_EAX, pointer)
        elif pc in (0x401120, 0x4011d0):
            node = get(sp + 4)
            registrations.append(dict(registry='main' if pc == 0x401120 else 'draw',
                                      priority=get(sp + 8), callback=get(node + 8),
                                      flags=get(node + 4), owner=get(node + 0x24), node=node))
        elif pc == 0x47d090:
            cached_lookups.append(dict(slot=get(sp + 4), namePointer=get(sp + 8)))
        elif pc == 0x46f1e0:
            sprite_binds.append(dict(resource=uc.reg_read(UC_X86_REG_ECX), vm=get(sp + 4), sprite=get(sp + 8)))

    # These services have no game RNG or registry semantics. Leave all native
    # factories and insertion instructions intact, including callback flags.
    for pc in (0x4854af, 0x48f980, 0x47ff50):
        machine.mem_write(pc, b'\xc3')
    machine.hook_add(UC_HOOK_CODE, boundary)
    machine.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, address, size, value, _: rng_writes.append(
        dict(address=address, bytes=size, value=value)), begin=0x4db508, end=0x4db517)

    factories = []
    for name, entry, global_pointer, size in [('laser', 0x43a4c0, 0x4db664, 0x600),
                                               ('pause', 0x448270, 0x4db678, 0x3e8),
                                               ('scorePopups', 0x457900, 0x4db694, 0xaf4)]:
        before_alloc, before_registration = len(allocations), len(registrations)
        put(stack, terminal)
        machine.reg_write(UC_X86_REG_ESP, stack)
        machine.emu_start(entry, terminal, count=100000)
        assert machine.reg_read(UC_X86_REG_EIP) == terminal
        owner = machine.reg_read(UC_X86_REG_EAX)
        assert owner and get(global_pointer) == owner
        assert allocations[before_alloc]['bytes'] == size
        rows = registrations[before_registration:]
        assert len(rows) == 2 and all(row['owner'] == owner and row['flags'] & 2 == 0 for row in rows)
        factories.append(dict(name=name, entry=entry, owner=owner, allocations=allocations[before_alloc:],
                              registrations=rows, objectSha256=hashlib.sha256(bytes(machine.mem_read(owner, size))).hexdigest()))

    assert [(r['registry'], r['priority']) for r in registrations] == [
        ('main', 22), ('draw', 33), ('main', 9), ('draw', 64), ('main', 17), ('draw', 44)]
    assert len(cached_lookups) == 1 and cached_lookups[0]['slot'] == 7
    assert len(sprite_binds) == 1 and sprite_binds[0]['sprite'] == 259
    assert not rng_writes and bytes(machine.mem_read(0x4db508, 16)) == initial_rng
    score = get(0x4db694)
    assert all(bytes(machine.mem_read(score + 0x5e4 + index * 72, 72)) == bytes(72) for index in range(18))
    pause = get(0x4db678)
    assert [get(pause + offset) for offset in (0x10, 0x14, 0x18, 0x20, 0x24, 0x28, 0x2c, 0x34)] == [
        0xffffffff, 0, 0, 1, 0xffffffff, 0, 0, 1]
    report = dict(originalSha256=digest, factories=factories, cachedLookups=cached_lookups,
                  spriteBinds=sprite_binds, actualRngWrites=rng_writes, bothRngStatesUnchanged=True,
                  cachedBulletResourceReused=True, popup259IsSpriteNotScript=True,
                  nativeRegistryInsertionExecuted=True, graphicsOrAudioDevicesOpened=0,
                  originalFileModified=False, productionChanged=False, wholeStartupTimingAccepted=False,
                  completeGame=False, toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    HOME.mkdir(exist_ok=False)
    (HOME / 'native.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: report[key] for key in ['bothRngStatesUnchanged', 'cachedBulletResourceReused',
                                                'popup259IsSpriteNotScript', 'nativeRegistryInsertionExecuted']}))


if __name__ == '__main__':
    main()
