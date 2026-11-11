"""Native Main registry visibility for a Control enable overlapping Overlay8.

Callback bodies declare publication/observation events; native allocation-node
construction, ordered insertion, Main traversal and 41d720 enable execute in
the emulator. This does not claim a physical worker or full Control body.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / 'artifacts/th14/initial-overlay-publication-nov11'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HOME / 'native-registry.json')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error('Choose a new output file to preserve earlier observations.')
    image, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
    assert hashlib.sha256(image.data).hexdigest() == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    cases = []
    for publication in ['before-main', 'overlay8', 'normal29', 'never']:
        m = Uc(UC_ARCH_X86, UC_MODE_32)
        for _, address, size, offset, count in image.sections:
            start = address & ~4095
            m.mem_map(start, ((address + size + 4095) & ~4095) - start)
            m.mem_write(address, image.data[offset:offset + count])
        base = 0x70000000
        m.mem_map(base, 0x100000)
        registry, control, count, stack, end = [base + n for n in [0x1000, 0x2000, 0x3000, 0xf0000, 0xff000]]
        get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
        put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))
        heap = base + 0x10000
        m.mem_write(0x4854af, b'\xc3')

        def allocate(uc, pc, size, _):
            nonlocal heap
            assert get(uc.reg_read(UC_X86_REG_ESP) + 4) == 0x28
            uc.reg_write(UC_X86_REG_EAX, heap)
            heap += 0x30

        m.hook_add(UC_HOOK_CODE, allocate, begin=0x4854af, end=0x4854af)
        put(0x4db51c, registry)
        m.mem_write(0x4f5815, b'\0')

        def call(pc, owner=0, args=()):
            put(stack, end)
            for index, value in enumerate(args):
                put(stack + 4 + index * 4, value)
            m.reg_write(UC_X86_REG_ECX, owner)
            m.reg_write(UC_X86_REG_ESP, stack)
            m.emu_start(pc, end, count=100000)
            assert m.reg_read(UC_X86_REG_EIP) == end
            return m.reg_read(UC_X86_REG_EAX)

        noop, enable, observe = base + 0x4000, base + 0x4100, base + 0x4200
        m.mem_write(noop, b'\xb8\x01\x00\x00\x00\xc3')
        # A declared publication event calls the unchanged native enable body.
        code = b'\xb9' + struct.pack('<I', control)
        code += b'\xe8' + struct.pack('<i', 0x41d720 - (enable + len(code) + 5))
        code += b'\xb8\x01\x00\x00\x00\xc3'
        m.mem_write(enable, code)
        m.mem_write(observe, b'\xff\x05' + struct.pack('<I', count) + b'\xb8\x01\x00\x00\x00\xc3')
        nodes = {}
        for priority in [1, 8, 9, 11, 29]:
            callback = observe if priority == 11 else enable if (
                priority == 8 and publication == 'overlay8' or priority == 29 and publication == 'normal29') else noop
            node = call(0x401570, args=(callback,))
            put(node + 4, 1 if priority == 11 else 3)
            put(node + 0x24, control)
            call(0x401120, registry, (node, priority))
            nodes[priority] = node
        put(control + 8, nodes[11])
        if publication == 'before-main':
            call(0x41d720, control)
        observations = []
        for _ in range(2):
            call(0x401280, registry)
            observations.append(get(count))
        expected = [1, 2] if publication in ['before-main', 'overlay8'] else [0, 1] if publication == 'normal29' else [0, 0]
        assert observations == expected, (publication, observations)
        cases.append(dict(publication=publication, controlCallbacksAfterEachPass=observations))
    report = dict(originalSha256=hashlib.sha256(image.data).hexdigest(), cases=cases,
                  actualNodeConstruction=True, actualSortedInsertion=True, actualMainTraversal=True,
                  actualControlEnableInstructions=True, callbackBodiesDeclared=True,
                  physicalWorkerSchedulingAccepted=False, fullControlBodyAccepted=False,
                  graphicsOrAudioDevicesOpened=0, completeGame=False,
                  toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(dict(passed=True, cases=cases)))


if __name__ == '__main__':
    main()
