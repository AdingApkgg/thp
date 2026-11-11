"""Original Control11 attract decisions and Timer under declared rates.

Runs the real callback registration/traversal, whole436620 and408690 timer.
Fade creation, score service, detached-copy updates and CRT allocation are
declared boundaries. No OS worker, actual GPU or whole-replay acceptance.
"""
from pathlib import Path
import argparse, hashlib, importlib, json, struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    image = importlib.import_module('th-anm-handlers').handlers(14)[0]
    sha = lambda b: hashlib.sha256(b).hexdigest()
    assert sha(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, offset, count in image.sections:
        start = address & ~4095
        m.mem_map(start, ((address + size + 4095) & ~4095) - start)
        m.mem_write(address, image.data[offset:offset + count])
    base, stack, stop = 0x70000000, 0x700f0000, 0x700ff000
    m.mem_map(base, 0x100000)
    control, hud, timer_owner, registry = [base + n for n in [0x1000, 0x2000, 0x3000, 0x4000]]
    get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
    put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))
    heap, fades, control_entries = base + 0x10000, [], []

    def ret(value=0, pop=0):
        sp = m.reg_read(UC_X86_REG_ESP)
        m.reg_write(UC_X86_REG_EAX, value)
        m.reg_write(UC_X86_REG_EIP, get(sp))
        m.reg_write(UC_X86_REG_ESP, sp + 4 + pop)

    def boundary(uc, pc, size, unused):
        nonlocal heap
        sp = uc.reg_read(UC_X86_REG_ESP)
        if pc == 0x4854af:
            assert get(sp + 4) == 0x28
            p = heap
            heap += 0x40
            m.mem_write(p, bytes(0x40))
            ret(p)
        elif pc == 0x46d1c0:
            fades.append([uc.reg_read(UC_X86_REG_ECX), uc.reg_read(UC_X86_REG_EDX),
                          *[get(sp + 4 + i * 4) for i in range(4)]])
            ret(0, 16)
        elif pc in [0x434360, 0x46fe50]:
            ret()
        elif pc == 0x436620:
            control_entries.append(pc)

    for pc in [0x4854af, 0x46d1c0, 0x434360, 0x46fe50, 0x436620]:
        m.hook_add(UC_HOOK_CODE, boundary, begin=pc, end=pc)

    def call(pc, owner=0, values=()):
        m.mem_write(stack, struct.pack('<' + 'I' * (len(values) + 1), stop, *values))
        for reg, value in [(UC_X86_REG_ECX, owner), (UC_X86_REG_ESP, stack),
                           (UC_X86_REG_EFLAGS, 0x202), (UC_X86_REG_MXCSR, 0x1f80),
                           (UC_X86_REG_FPCW, 0x37f), (UC_X86_REG_FPSW, 0), (UC_X86_REG_FPTAG, 0xffff)]:
            m.reg_write(reg, value)
        m.emu_start(pc, stop, count=200000)
        assert m.reg_read(UC_X86_REG_EIP) == stop, hex(m.reg_read(UC_X86_REG_EIP))
        return m.reg_read(UC_X86_REG_EAX)

    put(0x4db51c, registry)
    m.mem_write(0x4f5815, b'\0')
    node = call(0x401570, values=(0x436d70,))
    put(node + 4, 3)
    put(node + 0x24, control)
    call(0x401120, registry, (node, 11))
    put(0x4db558, control)
    put(0x4db550, hud)
    put(0x4db688, timer_owner)
    put(timer_owner + 0x10, 1)
    put(0x4db524, 0)
    put(0x4f58b8, 0x40)
    put(0x4d9684, 0)
    # Each row declares a distinct physical Session frame as a negative control;
    # original decision reads only Control+14. No physical frame is injected.
    cases = [
        dict(clock=3839, frame=3840, rate=1., steps=3, enabled=True, raw=0),
        dict(clock=3840, frame=5, rate=0., steps=3, enabled=True, raw=0),
        dict(clock=3839, frame=5, rate=.5, steps=6, enabled=True, raw=0),
        dict(clock=3839, frame=5, rate=1.5, steps=4, enabled=True, raw=0),
        dict(clock=3839, frame=5, rate=2., steps=3, enabled=True, raw=0),
        dict(clock=3899, frame=3900, rate=1., steps=2, enabled=True, raw=0),
        dict(clock=3899, frame=5, rate=.5, steps=4, enabled=True, raw=0),
        dict(clock=3900, frame=5, rate=0., steps=2, enabled=True, raw=0),
        dict(clock=3899, frame=5, rate=1.5, steps=3, enabled=True, raw=0),
        dict(clock=3899, frame=5, rate=2., steps=3, enabled=True, raw=0),
        dict(clock=3840, frame=3840, rate=1., steps=2, enabled=False, raw=0),
        dict(clock=3900, frame=3900, rate=1., steps=2, enabled=False, raw=0),
        dict(clock=3839, frame=5, rate=1., steps=1, enabled=True, raw=1),
        dict(clock=3839, frame=5, rate=1., steps=1, enabled=False, raw=1),
    ]
    for case in cases:
        m.mem_write(control, bytes(0x100))
        put(control + 0x10, case['clock'] - 1)
        put(control + 0x14, case['clock'])
        m.mem_write(control + 0x18, struct.pack('<f', case['clock']))
        put(control + 0x1c, 0x4d8f58)
        put(control + 0x20, 1)
        m.mem_write(0x4d8f58, struct.pack('<f', case['rate']))
        put(node + 4, 3 if case['enabled'] else 1)
        put(0x4d6878, case['raw'])
        case['timeline'] = []
        for step in range(case['steps']):
            fades.clear()
            control_entries.clear()
            put(0x4d964c, 0)
            before = get(control + 0x14)
            call(0x401280, registry)
            assert len(control_entries) == int(case['enabled'])
            assert fades == ([[5, 60, 0, 0, 0, 48]] if case['enabled'] and before == 3840 else [])
            transition = get(0x4d964c)
            assert bool(transition) == (case['enabled'] and (bool(case['raw'] & 0x80103) or before == 3900))
            case['timeline'].append(dict(before=before, timerWords=[get(control + o) for o in [0x10, 0x14, 0x18, 0x20]],
                                         fades=list(fades), transition=transition, called=bool(control_entries)))
    report = dict(cases=cases, originalSha256=sha(image.data), realMainTraversal=True,
                  realControlCallback=True, realTimer=True, fadeFactoryIsDeclaredBoundary=True,
                  noPhysicalWorkerOrGpu=True, completeGame=False, toolSha256=sha(Path(__file__).read_bytes()))
    (out / 'native.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(dict(cases=len(cases), snapshots=sum(len(c['timeline']) for c in cases), passed=True)))


if __name__ == '__main__':
    main()
