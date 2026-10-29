"""Separate original TH14 Replay construction from existing-stage restoration.

Executes unchanged original instruction blocks in declared virtual memory.
The decoded replay and virtual pointers are inputs, not observed live state.
File decoding, allocation, callback registration and ordinary GUI are outside
this component. No original process is launched or patched.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import itertools
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decoded', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    sys.path[:0] = [str(ROOT / 'tools/tmp/th14-analysis-python'), str(ROOT / 'tools')]
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_WRITE, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EBX, UC_X86_REG_EIP, UC_X86_REG_ECX
    image = importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    decoded = args.decoded.read_bytes()
    headers = []
    offset = 0x94
    for _ in range(struct.unpack_from('<I', decoded, 0x78)[0]):
        header = decoded[offset:offset + 0xdc]
        stage, seed = struct.unpack_from('<HH', header)
        frames, size = struct.unpack_from('<II', header, 4)
        assert 1 <= stage <= 7 and size >= frames * 6 and len(header) == 0xdc
        headers.append((stage, seed, header))
        offset += 0xdc + size
    assert offset == len(decoded) and headers
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, file_offset, length in image.sections:
        first = address & ~4095
        machine.mem_map(first, ((address + size + 4095) & ~4095) - first)
        machine.mem_write(address, image.data[file_offset:file_offset + length])
    base = 0x70000000
    machine.mem_map(base, 0x20000)
    manager, sheet, control, replay_header = [base + n for n in (0x100, 0x1000, 0x3000, 0x4000)]
    stack = base + 0x1f000

    def put(address, value):
        machine.mem_write(address, struct.pack('<I', value & 0xffffffff))

    def words(address, count):
        return list(struct.unpack('<' + 'I' * count, machine.mem_read(address, count * 4)))

    writes = []

    def observe(uc, access, address, size, value, user):
        if 0x4db508 <= address < 0x4db518 or 0x4f5828 <= address < 0x4f5898 or address == 0x4f58b8:
            writes.append(dict(pc=uc.reg_read(UC_X86_REG_EIP), address=address,
                               bytes=size, value=value & ((1 << (size * 8)) - 1)))

    machine.hook_add(UC_HOOK_MEM_WRITE, observe)
    stop_target = None

    def stop_before(uc, address, size, user):
        if address == stop_target:
            uc.emu_stop()

    # A code hook makes the boundary independent of cached translated blocks.
    machine.hook_add(UC_HOOK_CODE, stop_before)
    cases = []
    for (stage, seed, header), old_script, old_game, calls, flags in itertools.product(
            headers, [0, 1, 0x5d12, 0xffff], [0, 0xffff], [0, 0xfffffffe], [0, 0x10, 0x20]):
        for initial in (True, False):
            machine.mem_write(manager, bytes(0x400))
            put(manager + 0x10, 1)
            put(manager + 0x1c, replay_header)
            put(0x4db688, manager)
            put(0x4db558, control)
            put(0x4f58a4, stage)
            put(0x4f58b8, flags if initial else flags | 2)
            machine.mem_write(replay_header, decoded[:0x94])
            machine.mem_write(sheet, header)
            machine.mem_write(control, bytes(0x100))
            record = manager + (stage * 5 + 0x19) * 8
            put(record, 0x71234560)
            put(record + 8, 0x72345670)
            put(record + 0x10, sheet)
            machine.mem_write(0x4db508, struct.pack('<HHIHHI', old_script, 0xa5a5, calls, old_game, 0x5a5a, calls))
            machine.mem_write(0x4f5828, bytes.fromhex('efbeadde') * 28)
            machine.reg_write(UC_X86_REG_ESP, stack)
            machine.reg_write(UC_X86_REG_EBX, manager if initial else control)
            writes.clear()
            # Initial: successful Replay::load has installed the declared decoded
            # header; execute its real continuation, including mode selection.
            # Existing stage: enter the real worker bit-2 dispatch.
            start, stop = (0x4549cf, 0x454a6c) if initial else (0x435ed0, 0x435f37)
            machine.emu_start(start, stop, count=2000)
            assert machine.reg_read(UC_X86_REG_EIP) == stop
            actual = words(0x4db508, 4)
            expected = [(old_script if initial else seed) | 0xa5a50000, calls, seed | 0x5a5a0000, 0]
            assert actual == expected
            assert bytes(machine.mem_read(0x4f5828, 0x70)) == header[0x14:0x84]
            assert words(record + 4, 1) == [0x71234560]
            assert words(record + 0xc, 1) == [0x72345670]
            assert words(record + 0x14, 1) == [0xffffffff]
            if initial:
                assert bytes(machine.mem_read(control + 0x24, 0x5c)) == decoded[0x18:0x74]
                rng_writes = [w for w in writes if 0x4db508 <= w['address'] < 0x4db518]
                assert [(w['pc'], w['address']) for w in rng_writes] == [(0x454a41, 0x4db510), (0x454a47, 0x4db514)]
                mode = 0x20 if struct.unpack_from('<i', header, 0x14 + 7 * 4)[0] >= 0 else 0
                assert words(0x4f58b8, 1) == [mode]
            else:
                assert [(w['pc'], w['address']) for w in writes[:3]] == [
                    (0x45610f, 0x4db510), (0x456123, 0x4db508), (0x456129, 0x4db514)]
            cases.append(dict(initial=initial, stage=stage, seed=seed, initialScriptSeed=old_script,
                              initialGameSeed=old_game, initialCalls=calls, initialFlags=flags,
                              rngWords=actual, globalsSha256=SHA(header[0x14:0x84]),
                              writeSequence=writes.copy()))
    branch_controls = []
    for flags in [0, 0x10, 0x20, 0x40, 2, 0x12, 0x22, 0x42]:
        put(0x4f58b8, flags)
        put(control + 0x94, 1)
        machine.reg_write(UC_X86_REG_EBX, control)
        machine.reg_write(UC_X86_REG_ESP, stack)
        target = 0x456050 if flags & 2 else 0x454e60
        stop_target = target
        machine.emu_start(0x435ed0, 0, count=20)
        stop_target = None
        assert machine.reg_read(UC_X86_REG_EIP) == target, (hex(flags), hex(target), hex(machine.reg_read(UC_X86_REG_EIP)))
        if not flags & 2:
            assert machine.reg_read(UC_X86_REG_ECX) == 1
        machine.emu_start(0x436060, 0x436067, count=2)
        stable_flags = words(0x4f58b8, 1)[0]
        assert stable_flags == flags & ~0xb
        branch_controls.append(dict(flags=flags, target=target, stableFlags=stable_flags))
    # Supervisor's actual state-13 arm supplies control mode 1, then changes
    # outer state to 7. Stop before allocation; don't replace the factory.
    supervisor = base + 0x6000
    machine.mem_write(supervisor, bytes(0xb00))
    put(supervisor + 0x6e8, 5)  # previous state deliberately avoids title destructor
    put(supervisor + 0x6ec, 13)
    machine.reg_write(UC_X86_REG_ECX, supervisor)
    machine.reg_write(UC_X86_REG_ESP, stack)
    stop_target = 0x436560
    machine.emu_start(0x446930, 0, count=100)
    stop_target = None
    assert machine.reg_read(UC_X86_REG_EIP) == 0x436560
    assert machine.reg_read(UC_X86_REG_ECX) == 1
    assert words(supervisor + 0x6ec, 1) == [7]
    assert words(supervisor + 0x6f8, 1) == [1]
    slices = [(0x446930, 0x138), (0x435ed0, 0x67), (0x4549cf, 0x9d),
              (0x456050, 0xeb), (0x436060, 7), (0x456350, 0x2f)]
    report = dict(schema='th14/replay-construction-native/1', completed=True,
                  caseCount=len(cases), initialCases=sum(c['initial'] for c in cases),
                  existingStageCases=sum(not c['initial'] for c in cases), cases=cases,
                  branches=branch_controls, supervisorMode13CallsControlMode1=True,
                  initialScriptSeedPreserved=True, existingStageBothSeedsRestored=True,
                  scriptCallCountPreserved=True, gameCallCountReset=True,
                  stableReplayBitCleared=True, decodedSha256=SHA(decoded),
                  executableSha256=SHA(image.data),
                  instructionSlices=[dict(address=a, bytes=n, sha256=SHA(image.read(a, n))) for a, n in slices],
                  toolSha256=SHA(Path(__file__).read_bytes()),
                  declaredDecodedVirtualInputsOnly=True, originalInstructionsModified=False,
                  originalProcessLaunched=False, nativeFileLoadExecuted=False,
                  ordinaryMenuInitializationAccepted=False, completeGame=False, nativeEquivalent=False)
    (out / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'run-tool.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k: v for k, v in report.items() if k not in ('cases', 'instructionSlices', 'branches')}), flush=True)


if __name__ == '__main__':
    main()
