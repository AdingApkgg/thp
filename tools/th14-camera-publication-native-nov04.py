"""Execute original draw branches and worker copies at a declared publication cut."""
from pathlib import Path
import argparse, hashlib, importlib, itertools, json, struct, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_EBX

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') and not output.exists()
    img = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(img.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, raw, count in img.sections:
        first = address & ~4095
        m.mem_map(first, ((address+size+4095)&~4095)-first)
        m.mem_write(address, img.data[raw:raw+count])
    base, old, new, stack, world = 0x70000000, 0x70001000, 0x70010000, 0x7003f000, 0x4d9514
    m.mem_map(base, 0x40000)
    stops = {0x40e365, 0x40e4f6, 0x40e770, 0x40e7f1, 0x40e962, 0x40eb65}
    flushes = 0

    def code(machine, pc, size, user):
        nonlocal flushes
        if pc in stops:
            m.emu_stop()
        elif pc == 0x475eb0:
            # Renderer flush is the declared component boundary. No original
            # draw/worker instruction bytes are modified.
            sp = m.reg_read(UC_X86_REG_ESP)
            target = struct.unpack('<I', m.mem_read(sp, 4))[0]
            m.reg_write(UC_X86_REG_ESP, sp+4)
            m.reg_write(UC_X86_REG_EIP, target)
            flushes += 1

    m.hook_add(UC_HOOK_CODE, code)
    rows = []
    for foreground, flags, fade in itertools.product((0, 1), (0, 1, 4, 5, 8), (0, 29, 30, 59, 60)):
        initial = bytearray(300)
        saved = bytearray(300)
        struct.pack_into('<3f', initial, 0x30, -.5, .25, .75)
        struct.pack_into('<3f', saved, 0x30, -.75, .5, -.25)
        struct.pack_into('<2f', initial, 0xfc, 13, -7)
        m.mem_write(world, bytes(initial))
        m.mem_write(old+0x4274, bytes(saved))
        m.mem_write(old+0x4224, struct.pack('<I', flags))
        m.mem_write(old+0x422c, struct.pack('<i', fade))
        m.mem_write(stack, struct.pack('<I', base))
        m.reg_write(UC_X86_REG_ESP, stack)
        m.reg_write(UC_X86_REG_ECX, old)
        flushes = 0
        m.emu_start(0x40e790 if foreground else 0x40e2f0, base, count=200)
        pc = m.reg_read(UC_X86_REG_EIP)
        assert pc in stops
        published = pc in (0x40e365, 0x40e7f1)
        assert flushes == int(published)
        result = dict(foreground=foreground, flags=flags, fade=fade, stopPc=pc,
                      publishedBeforePerspective=published, rendererFlushBoundaryCalls=flushes)
        if published:
            assert bytes(m.mem_read(world+0xfc, 8)) == bytes(m.mem_read(old+0x4370, 8)) == initial[0xfc:0x104]
            main = m.context_save()
            m.mem_write(new+0x4274, bytes([0xcc])*300)
            m.reg_write(UC_X86_REG_EBX, new)
            m.emu_start(0x40d435, 0x40d447, count=100)
            assert m.reg_read(UC_X86_REG_EIP) == 0x40d447
            assert bytes(m.mem_read(new+0x4274, 300)) == bytes(m.mem_read(world, 300))
            result['workerCopiedRight'] = list(struct.unpack('<3I', m.mem_read(new+0x42a4, 12)))
            m.context_restore(main)
        rows.append(result)
    result = dict(executedOriginalDrawBranchesAndWorkerCopy=True, controlledCases=len(rows),
                  publicationCases=sum(row['publishedBeforePerspective'] for row in rows),
                  originalInstructionsModified=False, rendererFlushNotExecuted=True,
                  syntheticCamerasAndCpuSchedule=True, liveOriginalProcess=False,
                  oldRecordingOrderRecovered=False, oldCameraOrRngFailuresClosed=False,
                  completeGame=False, nativeEquivalent=False, rows=rows,
                  executableSha256=sha(img.data), toolSha256=sha(Path(__file__).read_bytes()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes((json.dumps(result, indent=2)+'\n').encode())
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}))


if __name__ == '__main__':
    main()
