"""Compare original ASCII loading across declared Control flags and rates.

Resource/texture/CRT services are declared boundaries. Original scripts, VM
allocation, publication, traversal, interrupts and pooled retirement execute.
This is a controlled logical sequence, not an OS scheduling or GPU test.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import struct
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--ascii', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(ROOT / 'tools'))
    image = importlib.import_module('th-anm-handlers').handlers(14)[0]
    sha = lambda b: hashlib.sha256(b).hexdigest()
    assert sha(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, offset, count in image.sections:
        start = address & ~4095
        m.mem_map(start, ((address + size + 4095) & ~4095) - start)
        m.mem_write(address, image.data[offset:offset + count])
    loader = importlib.import_module('th14-native-transition-resource-loader-nov09').install(m)
    serializer = importlib.import_module('th14-native-title-live-compare-oct27')
    base, stack, end = 0x78000000, 0x780f0000, 0x780ff000
    m.mem_map(base, 0x100000)
    get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
    put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))

    def run(address, owner=0, args=()):
        m.mem_write(stack, struct.pack('<' + 'I' * (len(args) + 1), end, *args))
        for register, value in [(UC_X86_REG_ESP, stack), (UC_X86_REG_ECX, owner),
                                (UC_X86_REG_MXCSR, 0x1f80), (UC_X86_REG_FPCW, 0x37f),
                                (UC_X86_REG_FPSW, 0), (UC_X86_REG_FPTAG, 0xffff)]:
            m.reg_write(register, value)
        m.emu_start(address, end, count=5000000)
        assert m.reg_read(UC_X86_REG_EIP) == end, hex(m.reg_read(UC_X86_REG_EIP))
        return m.reg_read(UC_X86_REG_EAX)

    def free_service(uc, pc, size, unused):
        sp = uc.reg_read(UC_X86_REG_ESP)
        uc.reg_write(UC_X86_REG_EIP, get(sp))
        uc.reg_write(UC_X86_REG_ESP, sp + 4)

    m.hook_add(UC_HOOK_CODE, free_service, begin=0x4854fe, end=0x4854fe)
    ascii_path = args.ascii.resolve()
    blob = ascii_path.read_bytes()
    assert sha(blob) == 'fc1c2295fda07140b475b2ddd45d221920534e4a011c529e76578609d69a9284'
    resource = loader.load('ascii.anm', blob, 2, 1.)
    put(loader.manager + 0x191e4, resource.resource)
    manager = loader.manager
    control = base + 0x9000
    put(0x4db558, control)  # Declared Control owner; original consumers execute.
    registry = base + 0x6000
    put(0x4db51c, registry)
    # Execute the real constructor's two allocation/registration fragments;
    # the CRT allocator remains the loader's declared service boundary.
    m.reg_write(UC_X86_REG_ESP, stack)
    m.reg_write(UC_X86_REG_EBP, stack - 0x100)
    put(stack - 0x118, manager)
    loader.context['loading'] = True
    m.emu_start(0x47aa08, 0x47aae5, count=100000)
    loader.context['loading'] = False
    assert m.reg_read(UC_X86_REG_EIP) == 0x47aae5
    callback_entries = []

    def observe_callback(uc, pc, size, unused):
        callback_entries.append(pc)

    for pc in [0x47e7f0, 0x47e7c0]:
        m.hook_add(UC_HOOK_CODE, observe_callback, begin=pc, end=pc)
    sentinel = manager + 0xbc7af8
    # A declared 64-entry pool supplies the same initial retail slots as the
    # full descending 8191-slot chain. Exhaustion is forbidden in this test.
    vms = [manager + 0xdc + (8190 - i) * 0x5e4 for i in range(64)]

    def reset(rate):
        put(control + 0x80, 0)
        m.mem_write(0x4d8f58, struct.pack("<f", rate))
        for offset in [0xfe8208, 0xfe820c, 0xfe8210, 0xfe8214, 0xff52c8]:
            put(manager + offset, 0)
        m.mem_write(sentinel, bytes(16))
        put(sentinel + 4, vms[0] + 0x5cc)
        for i, vm in enumerate(vms):
            m.mem_write(vm, bytes(0x5e4))
            run(0x40cc90, vm)
            put(vm + 0x5cc, vm)
            put(vm + 0x5d0, vms[i + 1] + 0x5cc if i + 1 < len(vms) else 0)
            put(vm + 0x5d4, vms[i - 1] + 0x5cc if i else sentinel)
            put(vm + 0x5e0, 8190 - i)
        m.mem_write(0x4db508, struct.pack('<HHIHHI', 12345, 0, 0, 54321, 0, 0))
        m.mem_write(base + 0x1000, struct.pack('<3f', 960., 784., 0.))
        run(0x47ed10, resource.resource, (base + 0x2000, 17, base + 0x1000, 0, 0xffffffff, 0, 0))
        return get(base + 0x2000)

    def capture(frame):
        rows = []
        for offset in [0xfe8208, 0xfe8210]:
            node = get(manager + offset)
            while node:
                address = get(node)
                assert address in vms, 'Pool exhaustion or unrelated VM'
                raw = bytes(m.mem_read(address, 0x5cc))
                w = lambda at: struct.unpack_from('<I', raw, at)[0]
                row = dict(rawVmHex=raw.hex(), handle=w(0x540),
                           file=struct.unpack_from('<H', raw, 0x36)[0],
                           script=struct.unpack_from('<H', raw, 0x4aa)[0],
                           timerPrevious=w(0x548), timerCurrent=w(0x54c), timerFraction=w(0x550),
                           pendingInterrupt=w(0x4a0), ageCurrent=w(0x560), address=address)
                rows.append(row)
                assert len(rows) <= 64
                node = get(node + 4)
        addresses = {row['address']: row['handle'] for row in rows}
        data = [frame, len(rows), get(0x4db508) & 0xffff, get(0x4db50c),
                get(0x4db510) & 0xffff, get(0x4db514)]
        for row in rows:
            fields, values = serializer.native_words(row, addresses)
            assert len(values) == 303
            data.extend(values)
        return data

    cases = []
    with (output / 'snapshots.u32').open('wb') as stream:
        for case in [
            dict(name='rate1-open', rate=1., frozenFlags=0),
            dict(name='rate1-bit2', rate=1., frozenFlags=2),
            dict(name='rate1-bits3', rate=1., frozenFlags=3),
            dict(name='rate1-bits7', rate=1., frozenFlags=7),
            dict(name='rate-half-bits3', rate=.5, frozenFlags=3),
            dict(name='rate-onehalf-bit2', rate=1.5, frozenFlags=2),
            dict(name='rate-zero-open', rate=0., frozenFlags=0),
        ]:
            finish, frames = 40, 160
            handle = reset(case['rate'])
            record = dict(**case, finishBeforeUpdate=finish, frames=frames,
                          freezeBegin=20, freezeEnd=60, byteOffset=stream.tell(), rootHandle=handle)
            for frame in range(frames + 1):
                put(control + 0x80, case['frozenFlags'] if 20 <= frame < 60 else 0)
                if frame:
                    if frame == finish:
                        run(0x47f140, manager, (handle, 1))
                    callback_entries.clear()
                    run(0x401280, registry)
                    assert callback_entries == [0x47e7f0, 0x47e7c0]
                words = capture(frame)
                stream.write(struct.pack('<' + 'I' * len(words), *words))
            record['byteLength'] = stream.tell() - record['byteOffset']
            record['remainingVms'] = capture(frames)[1]
            cases.append(record)
    report = dict(cases=cases, wordsPerVm=303, actualNativeFactory=True,
                  actualNativeRegistryUpdates=True, actualNativeDeferredInterrupt=True,
                  actualNativePooledRetirement=True, declaredInitialPoolCapacity=64,
                  callbackOrder=['Overlay8:47e7f0->47e6c0', 'Normal29:47e7c0->47e5e0'],
                  originalCallbackRegistrationsAndMainTraversal=True,
                  initialRng=[12345, 0, 54321, 0], controlOwnerPresent=True,
                  controlFlagsOffset=0x80, controlFlagProducerDeclared=True,
                  finishWhileFrozen=True, rateValues=[0., .5, 1., 1.5],
                  poolExhaustionAllowed=False, physicalSchedulingAccepted=False,
                  graphicsOrAudioDevicesOpened=0, completeGame=False,
                  originalSha256=sha(image.data), asciiSha256=sha(blob),
                  snapshotsSha256=sha((output / 'snapshots.u32').read_bytes()),
                  toolSha256=sha(Path(__file__).read_bytes()),
                  loaderSha256=sha((ROOT / 'tools/th14-native-transition-resource-loader-nov09.py').read_bytes()),
                  serializerSha256=sha((ROOT / 'tools/th14-native-title-live-compare-oct27.py').read_bytes()))
    (output / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
