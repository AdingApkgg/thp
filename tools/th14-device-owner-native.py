"""Complete retail Supervisor device create/reset and resolution owner.

COM HRESULT, refresh-rate query and logging boundaries are controlled.
No original executable or DLL is modified on disk.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()

def main():
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, raw, count in image.sections:
        first = address & ~4095
        m.mem_map(first, ((address+size+4095) & ~4095)-first)
        m.mem_write(address, image.data[raw:raw+count])
    base, stop, stack = 0x70000000, 0x70000100, 0x7001f000
    d3d, table, device, device_table = base+0x2000, base+0x3000, base+0x4000, base+0x5000
    m.mem_map(base, 0x20000)
    put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))
    get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
    requests, releases, refreshes = [], [], []
    failure = 0x8876086c
    case = {}
    def ret(value, argc):
        sp = m.reg_read(UC_X86_REG_ESP)
        target = get(sp)
        m.reg_write(UC_X86_REG_EAX, value & 0xffffffff)
        m.reg_write(UC_X86_REG_ESP, sp+4+argc*4)
        m.reg_write(UC_X86_REG_EIP, target)
    def observe(machine, address, size, user):
        sp = machine.reg_read(UC_X86_REG_ESP)
        if address in (base+0x1000, base+0x1010):
            reset = address == base+0x1010
            if reset:
                assert get(sp+4) == device
                present, argc = get(sp+8), 2
                kind, flags = None, None
            else:
                assert get(sp+4) == d3d and get(sp+8) == 0
                assert get(sp+16) == 0x12345678 and get(sp+28) == 0x4d8f68
                kind, flags, present, argc = get(sp+12), get(sp+20), get(sp+24), 7
            index = len(requests)
            result = failure if index < case['failures'] else 0
            requests.append(dict(reset=reset, deviceType=kind, behaviorFlags=flags,
                                 width=get(present), height=get(present+4), result=result))
            if not result and not reset:
                put(0x4d8f68, device)
            ret(result, argc)
        elif address == base+0x1020:
            releases.append('device' if get(sp+4) == device else 'd3d')
            ret(0, 1)
        elif address == base+0x1030:
            assert get(sp+4) == 0x12345678
            ret(0x1234, 1)
        elif address == base+0x1040:
            assert get(sp+4) == 0x1234 and get(sp+8) == 0x74
            value = 75 if case.get('badRefresh') and not refreshes else 60
            refreshes.append(value)
            ret(value, 2)
        elif address == base+0x1050:
            assert get(sp+4) == 0x12345678 and get(sp+8) == 0x1234
            ret(1, 2)
        else:
            ret(machine.reg_read(UC_X86_REG_EAX), 0)
    put(d3d, table); put(device, device_table)
    put(table+0x40, base+0x1000); put(device_table+0x40, base+0x1010)
    put(table+8, base+0x1020); put(device_table+8, base+0x1020)
    for slot, target in [(0x4b123c, base+0x1030), (0x4b1010, base+0x1040), (0x4b125c, base+0x1050)]:
        put(slot, target)
    for address in [*(base+0x1000+i*16 for i in range(6)), 0x403100, 0x4031d0]:
        m.hook_add(UC_HOOK_CODE, observe, begin=address, end=address)
    sizes = [[image.u32(0x4da0b0+i*8), image.u32(0x4da0b4+i*8)] for i in range(10)]
    valid_sizes = [s for s in sizes if s[0] >= 640 and s[1] >= 480]
    cases = [
        dict(name='hardware', failures=0, flags=0),
        dict(name='software-fallback', failures=1, flags=0),
        dict(name='reference-fallback', failures=2, flags=0),
        dict(name='forced-reference', failures=0, flags=2),
        dict(name='next-resolution', failures=3, flags=0),
        dict(name='create-all-failed', failures=100, flags=0),
        dict(name='forced-all-failed', failures=100, flags=2),
        dict(name='reset', failures=0, flags=0, reset=True),
        dict(name='reset-next-resolution', failures=1, flags=0, reset=True),
        dict(name='reset-all-failed', failures=100, flags=0, reset=True),
        dict(name='refresh-retry', failures=0, flags=0, badRefresh=True),
    ]
    rows = []
    for case in cases:
        requests.clear(); releases.clear(); refreshes.clear()
        put(0x4d8f64, d3d); put(0x4d8f68, device if case.get('reset') else 0)
        put(0x4d916c, case['flags']); put(0x4d9684, 0xa4)
        put(0x4f5a18, 0x12345678); put(0x4f7a64, 640); put(0x4f7a68, 480)
        put(0x4d9074, 0); put(0x4f7a54, 0x40)
        m.mem_write(0x4d9054, bytes(56))
        put(stack, stop); m.reg_write(UC_X86_REG_ESP, stack)
        m.reg_write(UC_X86_REG_ECX, int(case.get('reset', False)))
        m.emu_start(0x46b1a0, stop, count=200000)
        assert m.reg_read(UC_X86_REG_EIP) == stop
        result = m.reg_read(UC_X86_REG_EAX)
        failed = case['failures'] == 100
        assert result == (0xffffffff if failed else 0)
        if failed:
            multiplier = 1 if case.get('reset') or case['flags'] == 2 else 3
            assert len(requests) == 2*len(valid_sizes)*multiplier
        elif case.get('reset'):
            assert len(requests) == case['failures']+1
            assert all(r['reset'] for r in requests)
        elif case['flags'] == 2:
            assert [(r['deviceType'], r['behaviorFlags']) for r in requests] == [(2, 0x20)]
        else:
            expected = [(1, 0x40), (1, 0x20), (2, 0x20)]
            expected_calls = ([(1, 0x40), (1, 0x40)] if case.get('badRefresh') else
                              [expected[i % 3] for i in range(len(requests))])
            assert [(r['deviceType'], r['behaviorFlags']) for r in requests] == expected_calls
        if case['name'] in ('next-resolution', 'reset-next-resolution', 'refresh-retry'):
            assert [requests[0]['width'], requests[0]['height']] == valid_sizes[0]
            assert [requests[-1]['width'], requests[-1]['height']] == valid_sizes[1]
        if not failed:
            assert [get(0x4d9054), get(0x4d9058)] == [requests[-1]['width'], requests[-1]['height']]
        rows.append(dict(case, requests=requests.copy(), releases=releases.copy(), refreshes=refreshes.copy(),
                         result=result, selectedHardware=bool(get(0x4d9684) & 1),
                         selectedDimensions=[get(0x4d9054), get(0x4d9058)]))
    report = dict(passed=True, completeGame=False, nativeEquivalent=False, entry='0x46b1a0',
                  executableSha256=sha(image.data), functionSha256=sha(image.read(0x46b1a0,0x218)),
                  toolSha256=sha(Path(__file__).read_bytes()), sizeCandidates=sizes, rows=rows,
                  scope='Complete actual Supervisor device create/reset and resolution retry owner. Controlled COM HRESULTs, GetDC/GetDeviceCaps/ReleaseDC and log boundaries; requested logical640x480, refresh60/75. Default HAL hardware0x40, HAL software0x20 and REF software0x20 observed through full owner; no actual retail live device/thread FPU or driver success claim.')
    (ROOT/'docs/porting/th14-device-owner-native-verified-oct12.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS full retail create/reset owner',len(rows),'cases',len(valid_sizes),'resolution candidates')

if __name__ == '__main__':
    main()
