"""Execute original replay/record RNG stores with controlled main-thread draws.

The cameras, input stream and live game are not involved. Each profile executes
the original seed/counter instructions and original next16/next32; the scheduler
and RNG words are declared synthetic component inputs.
"""
from pathlib import Path
import argparse, hashlib, importlib, itertools, json, struct, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_ESI, UC_X86_REG_EIP, UC_X86_REG_EAX

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
sha = lambda raw: hashlib.sha256(raw).hexdigest()
EXE = 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
# Modes0/1/2: initial playback, existing-controller playback, recording.
# Phases0/1/2/3: gameplay seed, recorded seed, script seed, gameplay counter.
PATHS = {
    0: dict(start=0x454a3d, end=0x454a51, points={0x454a47: 0, 0x454a51: 3}),
    1: dict(start=0x45610b, end=0x456133, points={0x456115: 0, 0x456129: 2, 0x456133: 3}),
    2: dict(start=0x45609c, end=0x4560c1, points={0x4560a7: 1, 0x4560b0: 2, 0x4560c1: 3})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') and not output.exists()
    img = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(img.data) == EXE
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, offset, count in img.sections:
        first = address & ~4095
        m.mem_map(first, ((address+size+4095)&~4095)-first)
        m.mem_write(address, img.data[offset:offset+count])
    base, header, stack = 0x70000000, 0x70002000, 0x7000f000
    m.mem_map(base, 0x10000)
    enter, leave = base+0x100, base+0x110
    # The original optional lock branches run through declared stdcall
    # service boundaries. OS mutual exclusion and DLL stack effects are out
    # of scope for this store-order component.
    m.mem_write(enter, bytes.fromhex('c20400'))
    m.mem_write(leave, bytes.fromhex('c20400'))
    m.mem_write(0x4b1078, struct.pack('<I', enter))
    m.mem_write(0x4b107c, struct.pack('<I', leave))
    lock_events = []
    m.hook_add(UC_HOOK_CODE, lambda machine, pc, size, user: lock_events.append(pc), begin=enter, end=leave)
    gameplay, script = 0x4db510, 0x4db508

    def state():
        gs, gr, gc = struct.unpack('<HHI', m.mem_read(gameplay, 8))
        ss, sr, sc = struct.unpack('<HHI', m.mem_read(script, 8))
        return [gs, gr, gc, ss, sr, sc, struct.unpack('<H', m.mem_read(header+2, 2))[0]]

    profiles = []
    for mode in PATHS:
        route = PATHS[mode]
        for gs, ss, seed, calls, choice, bits, locking, target in itertools.product(
                (0, 1, 12345, 0xc9e9, 0xffff), (1, 1337, 0xffff), (0, 18535, 0xac80, 0xffff),
                (0, 7, 0xfffffffe), (0, 1), (16, 32), (0, 1), (*route['points'].values(), 4)):
            script_calls = calls ^ 0x13579bdf
            m.mem_write(gameplay, struct.pack('<HHI', gs, 0xabcd, calls))
            m.mem_write(script, struct.pack('<HHI', ss, 0xbeef, script_calls))
            m.mem_write(header, bytes(0xdc))
            m.mem_write(header+2, struct.pack('<H', seed))
            m.mem_write(0x4f5815, bytes([locking]))
            m.mem_write(0x4f5812, b'\0')
            m.reg_write(UC_X86_REG_ESI, header+0x14)
            m.reg_write(UC_X86_REG_ECX, header)
            m.reg_write(UC_X86_REG_ESP, stack)
            pc = route['start']
            trace = []
            result, main_calls = 0, 0
            for stop, point in route['points'].items():
                m.emu_start(pc, stop, count=40)
                assert m.reg_read(UC_X86_REG_EIP) == stop
                trace.append([point, *state()])
                if target == point:
                    worker = m.context_save()
                    m.mem_write(stack-0x100, struct.pack('<I', base))
                    m.reg_write(UC_X86_REG_ESP, stack-0x100)
                    m.reg_write(UC_X86_REG_ECX, gameplay if choice == 0 else script)
                    lock_events.clear()
                    m.emu_start(0x4032a0 if bits == 16 else 0x403310, base, count=100)
                    assert m.reg_read(UC_X86_REG_EIP) == base
                    assert lock_events == ([enter, leave] if locking else [])
                    assert bytes(m.mem_read(0x4f5812, 1)) == b'\0'
                    result = m.reg_read(UC_X86_REG_EAX) & (0xffff if bits == 16 else 0xffffffff)
                    main_calls += 1
                    m.context_restore(worker)
                pc = stop
            assert main_calls == int(target != 4)
            profiles.append(dict(input=[mode, gs, ss, seed, calls, script_calls, choice, bits, locking, target],
                                 trace=trace, final=[*state(), result, main_calls]))
    assert len(profiles) == 15840
    result = dict(executedOriginalReplayRecordStoresAndMainRng=True, profiles=profiles,
                  cases=len(profiles), routePcs=PATHS, executableSha256=EXE,
                  instructionBytesUnmodified=True, originalRngFunctions=['0x4032a0', '0x403310'],
                  optionalLockServicesDeclared=True, syntheticInputsAndCpuSchedule=True,
                  liveOriginalProcess=False, actualOldRecordingOrderRecovered=False,
                  oldRngOrBulletFailuresClosed=False, completeGame=False, nativeEquivalent=False,
                  codeHashes={hex(start): sha(img.read(start, end-start)) for start, end in
                              ((0x454a3d,0x454a51),(0x45609c,0x4560c1),(0x45610b,0x456133),(0x4032a0,0x40339b))},
                  toolSha256=sha(Path(__file__).read_bytes()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes((json.dumps(result, separators=(',', ':'))+'\n').encode())
    print(json.dumps({key: value for key, value in result.items() if key != 'profiles'}))


if __name__ == '__main__':
    main()
