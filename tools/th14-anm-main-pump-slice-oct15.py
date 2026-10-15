"""Run one explicitly called original ANM main helper from a bound RAM pause.

This is a helper slice, not a resumed main frame or a graphics device service.
Unknown external code stops before execution. No API success is synthesized.
"""
import hashlib
import json
import struct
import sys
from collections import deque
from pathlib import Path

import unicorn
from unicorn import Uc, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import x86_const as XR
from unicorn.unicorn_py3.unicorn import UcContext

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
CHECKPOINT = ROOT / 'artifacts/th14/worker-anm-wait-checkpoint-oct15/run/checkpoint'
OUT = ROOT / 'artifacts/th14/anm-main-pump-slice-oct15'
MANIFEST_SHA = 'bb905088944f0bf3eeae1e7202b008516dc864362eadfc04f45400e48f60d975'
FILE = 0x0cfb9430
STACK = 0x63000000
SENTINEL = STACK + 0x10000


def bound(row):
    path = (CHECKPOINT / row['path']).resolve()
    assert path.is_relative_to(CHECKPOINT.resolve()) and not path.is_symlink()
    raw = path.read_bytes()
    assert len(raw) == row['bytes'] and SHA(raw) == row['sha256']
    return raw


def context(row):
    raw = bound(row)
    result = UcContext.__new__(UcContext)
    result.__setstate__((raw, len(raw), row['arch'], row['mode']))
    assert bytes(result) == raw
    return result


def main():
    if not sys.argv[1:]:
        print(json.dumps(dict(prepared=True, originalCodeExecuted=False)))
        return
    assert sys.argv[1:] == ['--execute-prepared']
    plan_raw = (OUT / 'plan.json').read_bytes()
    plan = json.loads(plan_raw)
    assert plan['sourceSha256'] == SHA(Path(__file__).read_bytes())
    assert not (OUT / 'receipt.json').exists()
    manifest = (CHECKPOINT / 'manifest.json').read_bytes()
    assert SHA(manifest) == MANIFEST_SHA == plan['manifestSha256']
    state = json.loads(manifest)
    assert state['unicornVersion'] == unicorn.__version__ == '2.1.4'
    wrapper = Path(sys.modules[UcContext.__module__].__file__)
    assert SHA(wrapper.read_bytes()) == state['contextWrapper']['sha256']
    assert state['mainPausedAt'] == 0x445b65 and not state['mainSchedulerResumeSupported']
    row = state['contexts']['main']
    uc = Uc(row['arch'], row['mode'])
    for region in state['regions']:
        raw = bound(region)
        assert not (region['base'] < SENTINEL + 0x1000 and STACK < region['base'] + len(raw))
        uc.mem_map(region['base'], len(raw), region['permissions'])
        uc.mem_write(region['base'], raw)
    uc.context_restore(context(row))
    get = lambda at: struct.unpack('<I', uc.mem_read(at, 4))[0]
    regs = lambda: {name: int(uc.reg_read(getattr(XR, 'UC_X86_REG_' + name)))
                    for name in ['EIP', 'ESP', 'EBP', 'EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EFLAGS', 'FS', 'FS_BASE', 'FPCW', 'MXCSR']}
    saved_main = regs()
    assert saved_main['EIP'] == state['mainPausedAt'] and saved_main['FS_BASE'] == state['mainTeb']
    tid = get(state['mainTeb'] + 0x24)
    manager = get(0x4f56cc)
    assert get(manager + 0xbc7b0c + 6 * 4) == FILE
    assert get(FILE + 0x128) == 1 and get(FILE + 0x12c) == 0
    raw_pointer = get(FILE + 0x108)
    assert SHA(bytes(uc.mem_read(raw_pointer, 362096))) == '4ed48733ce14f094cef2a9c4f9eb58786ff018b80f3cc70260c72d09413f9607'
    # A new scratch stack and explicit stdcall helper invocation are declared.
    # Neither the ordinary main EIP nor the waiting worker is advanced.
    uc.mem_map(STACK, 0x10000, 3)
    uc.mem_write(STACK, b'\xa5' * 0x10000)
    sp = SENTINEL - 0x100
    uc.mem_write(sp, struct.pack('<II', SENTINEL, FILE))
    uc.reg_write(XR.UC_X86_REG_ESP, sp)
    uc.reg_write(XR.UC_X86_REG_EIP, 0x47d230)
    count, stop, stores, trace = 0, {}, [], deque(maxlen=80)
    executable = []
    for base_string, module in state['modules'].items():
        base = int(base_string)
        if not module['pe32']:
            continue
        pe = base + get(base + 0x3c)
        section_count = struct.unpack('<H', uc.mem_read(pe + 6, 2))[0]
        optional_bytes = struct.unpack('<H', uc.mem_read(pe + 20, 2))[0]
        for index in range(section_count):
            section = pe + 24 + optional_bytes + index * 40
            size, rva, raw_size = [get(section + off) for off in (8, 12, 16)]
            if get(section + 36) & 0x20000000:
                executable.append((base + rva, base + rva + max(size, raw_size), module['name']))
    imports = {int(key): value for key, value in state['imports'].items()}

    def observed(machine, address, size, user):
        nonlocal count
        count += 1
        trace.append(dict(pc=hex(address), size=size))
        names = [name for lo, hi, name in executable if lo <= address < hi]
        # First profile executes only original TH14 instructions.
        if not any(name.lower() == 'th14.exe' for name in names):
            stop.update(kind='UNSERVICED_EXTERNAL_CODE', pc=hex(address), modules=names,
                        imports=imports.get(address, []), registers=regs(),
                        stack=[get(machine.reg_read(XR.UC_X86_REG_ESP) + i * 4) for i in range(12)])
            machine.emu_stop()

    def written(machine, access, address, size, value, user):
        stores.append(dict(pc=hex(machine.reg_read(XR.UC_X86_REG_EIP)), address=hex(address), bytes=size, value=value))

    uc.hook_add(UC_HOOK_CODE, observed)
    uc.hook_add(UC_HOOK_MEM_WRITE, written, begin=FILE + 0x128, end=FILE + 0x12f)
    error = ''
    try:
        uc.emu_start(0x47d230, SENTINEL, timeout=10_000_000, count=100000)
    except Exception as exc:
        error = str(exc)
        stop.update(kind='EXECUTION_EXCEPTION', pc=hex(uc.reg_read(XR.UC_X86_REG_EIP)), error=error)
    if not stop:
        stop.update(kind='HELPER_RETURNED' if uc.reg_read(XR.UC_X86_REG_EIP) == SENTINEL else 'BOUNDED_STOP', registers=regs())
    report = dict(status='INCOMPLETE', sourceSha256=plan['sourceSha256'], planSha256=SHA(plan_raw),
                  checkpointManifestSha256=MANIFEST_SHA, mainHelperEntry='0x47d230',
                  invocation='declared stdcall(FILE) on A5 scratch stack with saved main CPU/FS',
                  savedMain=saved_main, capturedMainThreadId=tid, file=hex(FILE),
                  filePendingBefore=1, filePendingAfter=get(FILE + 0x128), fileSyncStores=stores,
                  stopped=stop, observations=count, recentCode=list(trace), error=error,
                  originalMainFrameResumed=False, workerResumed=False, hostApiResultsSynthesized=False,
                  actualGraphicsDeviceInvoked=False, actualAudioPlayed=False, completeGame=False, nativeEquivalent=False)
    with (OUT / 'receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(stop=stop, observations=count, filePendingAfter=report['filePendingAfter'])))


if __name__ == '__main__':
    main()
