"""Execute original RNG transactions interrupted by the original seed store.

An isolated instruction component with a declared scheduler and input words.
This is not an observation of a live game's thread order.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import itertools
import json
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
EXE = 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
POINTS = {
    16: {'counter_committed': 0x4032c0, 'before_read': 0x4032c5,
         'seed_read': 0x4032c8, 'before_store': 0x4032e0, 'seed_written': 0x4032e3},
    32: {'before_read': 0x403336, 'seed_read': 0x403339,
         'counter_committed': 0x40333d, 'before_store': 0x403373, 'seed_written': 0x403376},
}


def observe():
    image, *_ = importlib.import_module('th-anm-handlers').handlers(14)
    assert SHA(image.data) == EXE
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, raw, length in image.sections:
        first = address & ~4095
        m.mem_map(first, ((address + size + 4095) & ~4095) - first)
        m.mem_write(address, image.data[raw:raw+length])
    base, stack, rng = 0x70000000, 0x7000f000, 0x4db508
    m.mem_map(base, 0x10000)
    # Declare the OS critical-section services while executing the actual
    # original lock branches, including the enabled next16 return reload.
    enter,leave=base+0x100,base+0x110
    m.mem_write(enter,bytes.fromhex('c20400'));m.mem_write(leave,bytes.fromhex('c20400'))
    m.mem_write(0x4b1078,struct.pack('<I',enter));m.mem_write(0x4b107c,struct.pack('<I',leave))
    lock_events=[]
    def lock_service(machine,pc,size,user):lock_events.append('enter'if pc==enter else'leave')
    m.hook_add(UC_HOOK_CODE,lock_service,begin=enter,end=enter)
    m.hook_add(UC_HOOK_CODE,lock_service,begin=leave,end=leave)
    entry = {16: 0x4032a0, 32: 0x403310}
    assert image.read(0x456123, 6) == bytes.fromhex('66a308b54d00')
    read_state = lambda: list(struct.unpack('<HHI', bytes(m.mem_read(rng, 8))))
    rows = []
    for bits, seed, restore, calls, locking in itertools.product(
            (16,32), (0,1,12345,0xc9e9,0xffff), (0,18535,0xac80,0xffff), (0,0xfffffffe),(0,1)):
        for phase, pc in POINTS[bits].items():
            m.mem_write(rng, struct.pack('<HHI', seed, 0xbeef, calls))
            m.mem_write(0x4f5815,bytes([locking]));m.mem_write(0x4f5812,b'\0');lock_events.clear()
            m.mem_write(stack, struct.pack('<I', base))
            m.reg_write(UC_X86_REG_ESP, stack)
            m.reg_write(UC_X86_REG_ECX, rng)
            m.emu_start(entry[bits], pc, count=500)
            assert m.reg_read(UC_X86_REG_EIP) == pc
            before = read_state()
            saved = m.context_save()
            # The worker's actual six-byte store executes. Restoring the main
            # CPU context preserves shared memory, including this store.
            m.reg_write(UC_X86_REG_EAX, restore)
            m.emu_start(0x456123, 0x456129, count=1)
            assert m.reg_read(UC_X86_REG_EIP) == 0x456129
            after_worker = read_state()
            assert after_worker == [restore, before[1], before[2]]
            m.context_restore(saved)
            m.emu_start(pc, base, count=500)
            assert m.reg_read(UC_X86_REG_EIP) == base
            final = read_state()
            assert lock_events==(['enter','leave']if locking else[])
            assert bytes(m.mem_read(0x4f5812,1))==b'\0'
            assert final[1] == 0xbeef
            assert final[2] == (calls + (1 if bits==16 else 2)) & 0xffffffff
            result = m.reg_read(UC_X86_REG_EAX) & ((1<<bits)-1)
            rows.append(dict(bits=bits,seed=seed,restore=restore,calls=calls,locking=locking,phase=phase,
                pc=hex(pc),before=before,afterWorker=after_worker,
                final=final,result=result,lockServices=list(lock_events)))
    assert len(rows) == 800
    assert len({tuple(r[k]for k in('bits','seed','restore','calls','locking','phase'))for r in rows})==800
    return dict(schema='th14/rng-instruction-store-boundaries/1',
        executableSha256=EXE,toolSha256=SHA(Path(__file__).read_bytes()),
        rngCodeSha256=SHA(image.read(0x4032a0,0x100)),
        workerStoreCodeSha256=SHA(image.read(0x456123,6)),
        originalNext16='0x4032a0',originalNext32='0x403310',originalWorkerStore='0x456123',
        phases=POINTS,profiles=rows,originalInstructionsUnmodified=True,
        originalOptionalLockModes=[0,1],declaredLockServiceBoundary='Original Enter/LeaveCriticalSection IAT calls execute stdcall return stubs; OS mutual exclusion is not emulated.',
        declaredSyntheticInputsAndScheduler=True,
        actualLiveProcessObserved=False,historicalRaceOrderProved=False,
        productionChanged=False,strictCampaignGateUnchanged=True,
        completeGame=False,nativeEquivalent=False)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    assert output.is_relative_to(ROOT/'artifacts/th14') and not output.exists()
    output.parent.mkdir(parents=True,exist_ok=True)
    result=observe()
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(profiles=len(result['profiles']),actualLiveProcessObserved=False,productionChanged=False,completeGame=False)))
