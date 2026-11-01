"""Execute retail stage completion with the real option-recall function intact."""
from pathlib import Path
import argparse, hashlib, importlib, itertools, json, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

R = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()


def evidence():
    image, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, count in image.sections:
        start = base & ~4095
        machine.mem_map(start, ((base + size + 4095) & ~4095) - start)
        machine.mem_write(base, image.data[raw:raw + count])
    base = 0x70000000
    machine.mem_map(base, 0x100000)
    score, control, hud, callback_owner, resource, vm, player, stack = [
        base + n for n in (0x1000, 0x30000, 0x31000, 0x32000, 0x33000, 0x34000, 0x40000, 0xff000)]

    def put(address, value):
        machine.mem_write(address, struct.pack('<I', value & 0xffffffff))

    def get(address):
        return struct.unpack('<I', machine.mem_read(address, 4))[0]

    events = []
    controlled = {0x47fcb0, 0x40af00, 0x46fe50, 0x47e890, 0x448ef0, 0x449f20, 0x47f140}

    def hook(uc, address, size, unused):
        sp = uc.reg_read(UC_X86_REG_ESP)
        if address == 0x4358e0:
            assert uc.reg_read(UC_X86_REG_ECX) == player
            events.append(dict(kind='real-recall-entry', returnPc=get(sp)))
        if address not in controlled:
            return
        cleanup = 0
        if address == 0x47fcb0:
            uc.reg_write(UC_X86_REG_EAX, vm)
        elif address == 0x40af00:
            cleanup = 8
        elif address == 0x47e890:
            put(get(sp + 4), 1234)
            uc.reg_write(UC_X86_REG_EAX, get(sp + 4))
            cleanup = 8
        elif address == 0x47f140:
            events.append(dict(kind='interrupt-boundary', returnPc=get(sp), handle=get(sp + 4), label=get(sp + 8)))
            cleanup = 8
        uc.reg_write(UC_X86_REG_EIP, get(sp))
        uc.reg_write(UC_X86_REG_ESP, sp + 4 + cleanup)

    machine.hook_add(UC_HOOK_CODE, hook)
    rows = []
    for stage, practice, replay, flags in itertools.product(range(1, 8), range(2), range(2), (0, 0x10, 0xfffffffd)):
        machine.mem_write(base, bytes(0x60000))
        for address, value in ((0x4db68c, score), (0x4db558, control), (0x4db550, hud),
                               (0x4db52c, callback_owner), (0x4db67c, player), (hud + 0x2a4, resource),
                               (control + 0x94, replay), (0x4f5828, 0), (0x4f582c, 0),
                               (0x4f5834, 1), (0x4f5838, 0), (0x4f58a4, stage),
                               (0x4f5864, 2), (0x4f5870, 3), (0x4f5830, 0),
                               (0x4f58b8, practice << 4), (0x4d964c, 0), (0x4db69c, 0),
                               (player + 0x182d4, flags), (player + 0x1830c, 77)):
            put(address, value)
        machine.mem_write(0x4f5815, b'\0')
        for index in range(8):
            put(player + 0xd79c + index * 0xe4, 2 * index + 1)
            put(player + 0xd7a0 + index * 0xe4, 2 * index + 2)
        events.clear()
        put(stack, base)
        machine.reg_write(UC_X86_REG_ESP, stack)
        machine.emu_start(0x436f90, base, count=10000)
        assert machine.reg_read(UC_X86_REG_EIP) == base
        recalls = [event for event in events if event['kind'] == 'real-recall-entry']
        interrupts = [event for event in events if event['kind'] == 'interrupt-boundary']
        assert recalls == [dict(kind='real-recall-entry', returnPc=0x436fb8)]
        assert [(event['handle'], event['label']) for event in interrupts] == [(index + 1, 3) for index in range(16)]
        assert [event['returnPc'] for event in interrupts] == [0x43590a, 0x435913] * 8
        assert get(player + 0x182d4) == flags | 2 and get(player + 0x1830c) == 0
        rows.append(dict(stage=stage, practice=practice, replay=replay, initialFlags=flags,
                         finalFlags=get(player + 0x182d4), recalls=len(recalls), interrupts=len(interrupts)))
    # Exact relative-call matches, each decoded as a CALL instruction. This is
    # a static direct-reference inventory; no indirect-call completeness claim.
    disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
    references = []
    for name, address, size, raw, count in image.sections:
        if name != '.text':
            continue
        data = image.data[raw:raw + count]
        for offset in range(len(data) - 4):
            if data[offset] != 0xe8:
                continue
            pc = address + offset
            if pc + 5 + struct.unpack_from('<i', data, offset + 1)[0] != 0x4358e0:
                continue
            instruction = next(disassembler.disasm(data[offset:offset + 5], pc))
            assert instruction.mnemonic == 'call' and instruction.op_str == '0x4358e0'
            references.append(dict(pc=pc, instructionHex=instruction.bytes.hex()))
    assert [event['pc'] for event in references] == [0x436fb3, 0x450503]
    return dict(realRetailCompletionAndRecallExecuted=True, nativeExecutableSha256=SHA(image.data),
                cases=len(rows), rows=rows, directCallReferences=references, actualCompletionRecallReturnPc=0x436fb8,
                flagsChangedInSameRecallCall=True, unconditionalSixteenLabel3InterruptBoundaries=True,
                servicesAndFamilyInterruptDispatchControlled=True, actualWholeWorkerOrFamilyDispatchNotExecuted=True,
                indirectCallCompletenessNotClaimed=True, ordinaryIndependentThreadTimingAccepted=False,
                completeGame=False, nativeEquivalent=False, toolSha256=SHA(Path(__file__).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') and not output.exists()
    result = evidence()
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}))
