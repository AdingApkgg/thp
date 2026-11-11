"""Execute retail 4510b0 on six retained raw gameplay shot/VM/spec inputs.

This is an isolated component replay, not a new live original branch trace.
Only rotation Z changes in the counterfactual; no data is sent to the port.
"""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import importlib
import json
import struct
import sys

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/actual-slot-update-nov12/verified-v6'
N = R / 'artifacts/th14/original-nine-shot-native-nov05/prefix-slots-v2/native'
C = R / 'artifacts/th14/reimub-shot-coverage-nov08'
A = C / 'run-v3-input-key'
sys.path[:0] = [str(R / 'tools/tmp/th14-analysis-python'), str(R / 'tools')]
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_ECX,
    UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_MXCSR, UC_X86_REG_FPCW,
    UC_X86_REG_FPSW, UC_X86_REG_FPTAG)

load = lambda p: json.loads(p.read_bytes())
sha = lambda b: hashlib.sha256(b).hexdigest()
word = lambda b, o: struct.unpack_from('<I', b, o)[0]
im = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert sha(im.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert load(C / 'input-key-v3-terminal-receipt.json')['reaped']
assert load(C / 'qualified-input-key-v3-nov09.json')['allWorkersHostsGpuAndClockRetired']
ni = {r['callback']: r for r in load(N / 'shot-lifetime-index.json')['snapshots']}
ci = {tuple(r['inputKey']): r for r in load(A / 'shot-index.json')['snapshots']}
keys = {r['nativeCallback']: tuple(r['inputKey']) for r in load(C / 'component-v3-input-key/build.json')['targetInputRows']}
bindings = {}


def bound(p):
    b = p.read_bytes()
    bindings[p.relative_to(R).as_posix()] = dict(bytes=len(b), sha256=sha(b))
    return b


def native(cb):
    item = ni[cb]
    b = bound(N / 'shot-lifetime' / item['file'])
    assert sha(b) == item['sha256']
    return json.loads(gzip.decompress(b))


def cpp(key, slot):
    item = ci[key]
    b = bound(A / item['file'])
    assert sha(b) == item['sha256']
    return struct.unpack_from('<96I', b, slot * 96 * 4)


def run(n, slot, rotation, rate):
    raw_slot = bytes.fromhex(n['shotPoolRawHex'])[slot * 0xd0:(slot + 1) * 0xd0]
    vr = n['vms'][str(slot)]
    raw_vm = bytes.fromhex(vr['rawHex'])
    spec_address = word(raw_slot, 0xbc)
    raw_spec = bytes.fromhex(n['specs'][str(spec_address)])
    globals_ = bytes.fromhex(n['renderGlobalsRawHex'])
    assert len(raw_slot) == 0xd0 and len(raw_vm) == 0x5cc and len(raw_spec) == 64 and len(globals_) == 36
    assert word(raw_slot, 0x98) == 2 and raw_spec[0x21] == 0 and word(raw_spec, 0x2c) == 0
    assert word(raw_slot, 0xc0) == 0 and word(raw_vm, 0x594) == 0
    assert word(raw_slot, 0x14) == vr['handle']
    assert word(raw_slot, 0x24) == 0x4d8f58
    obj = n['playerAddress'] + 0x6c8 + slot * 0xd0
    vm = vr['address']
    stack_base, stack, stop = 0x70000000, 0x700ff000, 0x700fe000
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    mapped = set()

    def map_region(base, count):
        for page in range(base & ~4095, (base + count + 4095) & ~4095, 4096):
            if page not in mapped:
                m.mem_map(page, 4096)
                mapped.add(page)

    for _, base, size, offset, count in im.sections:
        map_region(base, size)
        m.mem_write(base, im.data[offset:offset + count])
    for base, count in [(obj, len(raw_slot)), (vm, len(raw_vm)),
                        (spec_address, len(raw_spec)), (stack_base, 0x100000)]:
        map_region(base, count)
    m.mem_write(obj, raw_slot)
    changed_vm = bytearray(raw_vm)
    struct.pack_into('<I', changed_vm, 0x50, rotation)
    m.mem_write(vm, bytes(changed_vm))
    m.mem_write(spec_address, raw_spec)
    m.mem_write(0x4f7a6c, globals_)
    put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))
    get = lambda p: word(bytes(m.mem_read(p, 4)), 0)
    put(0x4d8f58, word(struct.pack('<f', rate), 0))
    put(0x4db67c, n['playerAddress'])
    # Manager identity is unobserved and only passed to the declared lookup.
    put(0x4f56cc, 0)
    put(0x4d0cc0, 0x13572468)
    # Declared SSE2 CRT path; this startup flag was not in the gameplay snapshot.
    put(0x4fdc94, 1)
    put(stack, stop)
    events, quads, branches, reads, writes = [], [], [], set(), set()
    data_ranges = [(obj, obj + 0xd0), (vm, vm + 0x5cc),
        (spec_address, spec_address + 64), (0x4f7a6c, 0x4f7a6c + len(globals_)),
        (0x4d8f58, 0x4d8f5c), (0x4db67c, 0x4db680),
        (0x4f56cc, 0x4f56d0), (0x4d0cc0, 0x4d0cc4), (0x4fdc94, 0x4fdc98),
        (0x4d67a8, 0x4d6808),  # PE-backed immutable anchor tables in .data
        (stack_base, stack_base + 0x100000)]

    def in_ranges(address, size, ranges):
        return any(lo <= address and address + size <= hi for lo, hi in ranges)

    def read_hook(machine, access, address, size, value, user):
        # Everything outside retained raw records, declared globals and stack
        # must be an image constant/table, not silently zero-filled live state.
        assert in_ranges(address, size, data_ranges) or 0x400000 <= address < 0x4d0000, hex(address)
        reads.add((address, size))

    def write_hook(machine, access, address, size, value, user):
        assert in_ranges(address, size, [(obj, obj + 0xd0), (vm, vm + 0x5cc),
            (stack_base, stack_base + 0x100000)]), hex(address)
        if not stack_base <= address < stack_base + 0x100000:
            writes.add((address, size))

    def hook(machine, address, size, user):
        if address == 0x47f0a0:
            assert get(m.reg_read(UC_X86_REG_ESP) + 4) == vr['handle']
            assert m.reg_read(UC_X86_REG_ECX) == 0
            events.append('lookup')
            m.reg_write(UC_X86_REG_EAX, vm)
        elif address == 0x47f6e0:
            assert m.reg_read(UC_X86_REG_ECX) == obj + 0x14
            assert get(obj + 0x14) == vr['handle']
            events.append('release')
            put(obj + 0x14, 0)
        elif address == 0x4854a0:
            assert m.reg_read(UC_X86_REG_ECX) == 0x13572468
            events.append('cookie')
        elif address == 0x45115f:
            quads.extend(struct.unpack('<12I', m.mem_read(m.reg_read(UC_X86_REG_EBP) - 0x34, 48)))
        else:
            branches.append(hex(address))

    for address, cleanup in [(0x47f0a0, 4), (0x47f6e0, 0), (0x4854a0, 0)]:
        m.mem_write(address, b'\xc2' + struct.pack('<H', cleanup) if cleanup else b'\xc3')
    for address in [0x47f0a0, 0x47f6e0, 0x4854a0, 0x45115f,
                    0x45124e, 0x451288, 0x451290, 0x45129f]:
        m.hook_add(UC_HOOK_CODE, hook, begin=address, end=address)
    m.hook_add(UC_HOOK_MEM_READ, read_hook)
    m.hook_add(UC_HOOK_MEM_WRITE, write_hook)
    for reg, value in [(UC_X86_REG_ESP, stack), (UC_X86_REG_ECX, obj),
        (UC_X86_REG_MXCSR, 0x1f80), (UC_X86_REG_FPCW, 0x37f),
        (UC_X86_REG_FPSW, 0), (UC_X86_REG_FPTAG, 0xffff)]:
        m.reg_write(reg, value)
    m.emu_start(0x4510b0, stop, count=100000)
    assert m.reg_read(UC_X86_REG_EIP) == stop and len(quads) == 12
    state = get(obj + 0x98)
    assert state in (0, 2) and events.count('lookup') == 1 and events.count('cookie') == 2
    assert ('release' in events) == (state == 0)
    assert ('0x451290' in branches) == (state == 0)
    assert ('0x45129f' in branches) == (state == 2)
    assert bytes(m.mem_read(spec_address, len(raw_spec))) == raw_spec
    assert bytes(m.mem_read(0x4f7a6c, len(globals_))) == globals_
    final_slot = bytes(m.mem_read(obj, len(raw_slot)))
    final_vm = bytes(m.mem_read(vm, len(raw_vm)))
    return dict(state=state, returnValue=m.reg_read(UC_X86_REG_EAX),
        handle=get(obj + 0x14), events=events, branches=branches, quadWords=quads,
        slotChangedOffsets=[i for i in range(0, 0xd0, 4) if word(raw_slot, i) != word(final_slot, i)],
        vmChangedOffsets=[i for i in range(0, 0x5cc, 4) if word(changed_vm, i) != word(final_vm, i)],
        comparisonWords=quads + [word(final_slot, o) for o in [0x98]] + [int(word(final_slot, 0x14) != 0)] + [word(final_slot, o) for o in [0x18, 0x1c, 0x20, 0x28, 0x54, 0x58, 0x5c, 0x88, 0x8c, 0x90]] + [word(final_vm, o) for o in [0x59c, 0x5a0, 0x5a4, 0x50]],
        slotSha256=sha(final_slot), vmSha256=sha(final_vm),
        readAddresses=[[hex(a), s] for a, s in sorted(reads)],
        nonStackWriteAddresses=[[hex(a), s] for a, s in sorted(writes)])


def main():
    assert not H.exists(), 'Evidence directory already exists; preserve prior results.'
    H.mkdir(parents=True)
    cases = []
    for cb, slot in [(16395, 201), (19766, 228), (20537, 189),
                     (20538, 210), (20543, 159), (32367, 216)]:
        n = native(cb)
        nn = native(cb + 1)
        p = cpp(keys[cb], slot)
        pn = cpp(keys[cb + 1], slot)
        raw_vm = bytes.fromhex(n['vms'][str(slot)]['rawHex'])
        native_state = word(bytes.fromhex(nn['shotPoolRawHex']), slot * 0xd0 + 0x98)
        controls = []
        for rate in [0, .5, 1, 1.5, 2]:
            original = run(n, slot, word(raw_vm, 0x50), rate)
            changed = run(n, slot, p[49], rate)
            restored = run(n, slot, word(raw_vm, 0x50), rate)
            assert restored == original
            assert original['state'] == native_state and changed['state'] == pn[1]
            assert changed['quadWords'] == list(p[68:80])
            assert original['state'] != changed['state']
            controls.append(dict(declaredRate=rate, original=original, rotationOnly=changed,
                restoredExactly=True, baselineMatchesRetainedNextNativeState=True,
                rotationOnlyMatchesRetainedNextCppState=True,
                rotationOnlyAll12QuadWordsMatchRetainedCpp=True))
        case = dict(nativeCallback=cb, slot=slot, inputKey=keys[cb],
            nextInputKey=keys[cb + 1], nextNativeState=native_state, nextCppState=pn[1],
            nativeRotationBits=word(raw_vm, 0x50), cppRotationBits=p[49], controls=controls)
        cases.append(case)
        (H / 'partial-cases.json').write_text(json.dumps(cases, indent=2) + '\n')
    for p in [Path(__file__), N / 'shot-lifetime-index.json', A / 'shot-index.json',
              C / 'component-v3-input-key/build.json', C / 'input-key-v3-terminal-receipt.json',
              C / 'qualified-input-key-v3-nov09.json', C / 'angle-retirement-components-nov09.json']:
        bound(p)
    report = dict(schema='th14/actual-raw-shot-retail-component/1',
        recordedAt=datetime.now(timezone.utc).isoformat(), passed=True,
        cases=cases, actualRawGameplaySlots=6, declaredRates=5,
        completeOriginalSingleShotExecutions=90, rotationOnlyControls=30,
        originalSlotVmSpecAndRenderGlobalsUsed=True,
        noUnobservedPointerDereferences=True,
        retailWholeShotUpdateExecuted=True, retailQuadExecuted=True,
        originalGameplayBranchDirectlyTraced=False,
        ratesAreDeclaredNotObservedNativeValues=True,
        declaredServices=['ANM handle lookup returns captured raw VM',
            'ANM release records call and clears handle; pooled destructor not executed',
            'security cookie check validates declared cookie and returns'],
        unobservedGlobals={'ANM manager': 'zero sentinel passed only to lookup service',
            'security cookie': 'declared 0x13572468',
            'CRT math dispatch 0x4fdc94': 'declared 1 (SSE2 path); not captured gameplay state'},
        imageSha256=sha(im.data), instructionBindings=[dict(pc=hex(pc), bytes=count,
            sha256=sha(im.read(pc, count))) for pc, count in [(0x4510b0, 0x2ca), (0x479560, 0x100), (0x4d67a8, 0x60)]],
        originalOsGameOrGpuStarted=False, nativeValuesProvidedToPort=False,
        liveStateOrRngOrInputWritten=False, productionChanged=False,
        seventhMissingNativePoolNotFilled=True, uniqueRngProducerProven=False,
        strictReplayFailuresUnchanged=True, completeGame=False, nativeEquivalent=False,
        bindings=bindings)
    (H / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, actualRawSlots=6, declaredRateControls=30,
        originalSingleShotExecutions=90, directlyTracedOriginalGameplayBranch=False,
        productionChanged=False, completeGame=False)))


if __name__ == '__main__':
    main()
