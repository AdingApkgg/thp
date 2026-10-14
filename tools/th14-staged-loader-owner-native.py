"""Bounded original EnemyManager retirement, with one owned CRT-free boundary.

Synthetic empty/detached manager preconditions are declared. Original gameplay
instructions run unchanged; no game-call shim, actual game child or timing model.
"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'tools/th14-loading-lifecycle-evidence-check.py'
SHA = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    assert output.is_relative_to(ROOT / 'artifacts/th14')
    spec = importlib.util.spec_from_file_location('retail_image_helper', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    image = helper.Image()
    machine = image.machine()
    machine.mem_map(0x2000000, 0x1000000)
    for address, value in ((0x4db544, 0x600000), (0x4f56cc, 0x2000000),
                           (0x6000cc, 0x610000), (0x6000dc, 299), (0x7ff000, 0x710000)):
        helper.word(machine, address, value)
    machine.mem_write(0x4db510, struct.pack('<HHI', 49408, 0, 66446))
    machine.reg_write(UC_X86_REG_ECX, 0x600000)
    machine.reg_write(UC_X86_REG_ESP, 0x7ff000)
    writes, frees = [], []

    def free_owned_block(uc, address, size, user):
        stack = uc.reg_read(UC_X86_REG_ESP)
        return_address, block = struct.unpack('<II', uc.mem_read(stack, 8))
        assert block == 0x610000 and not frees and return_address == 0x4227c4
        frees.append(dict(boundary=hex(address), ownedSyntheticBlock=hex(block),
                          nativeReturnAddress=hex(return_address)))
        # This sole external allocation service releases the explicitly owned
        # synthetic ECL block. It cannot produce any gameplay result or delay.
        uc.reg_write(UC_X86_REG_ESP, stack + 4)
        uc.reg_write(UC_X86_REG_EIP, return_address)

    def on_write(uc, access, address, size, value, user):
        if address in (0x4db544, 0x4db514):
            writes.append(dict(instruction=hex(uc.reg_read(UC_X86_REG_EIP)),
                               address=hex(address), bytes=size,
                               before=int.from_bytes(uc.mem_read(address, size), 'little'), value=value))

    machine.hook_add(UC_HOOK_CODE, free_owned_block, begin=0x4854fe, end=0x4854fe)
    machine.hook_add(UC_HOOK_MEM_WRITE, on_write)
    machine.emu_start(0x4226c0, 0x710000, count=10000)
    assert machine.reg_read(UC_X86_REG_EIP) == 0x710000
    assert writes == [dict(instruction='0x422821', address='0x4db544', bytes=4,
                           before=0x600000, value=0)]
    assert len(frees) == 1
    rng = list(struct.unpack('<HHI', machine.mem_read(0x4db510, 8)))
    assert rng == [49408, 0, 66446]
    result = dict(diagnosticOnly=True, instructionExecutionPassed=True, completeGame=False,
                  nativeEquivalent=False, actualRetailProcessesStarted=0,
                  entry='0x4226c0', genuineHarnessReturn='0x710000', instructionBudget=10000,
                  preconditions=dict(emptyManager='0x600000', previousNextId=299,
                                     callbackNodesDetached=True, syntheticEclBlock='0x610000',
                                     animationSupervisor='0x2000000', referencedTexturesAndVmsAbsent=True,
                                     gameplayRngBefore=[49408, 0, 66446]),
                  memoryWrites=writes, controlledCrtFreeBoundaries=frees, simulatedGameCalls=0,
                  ownerPresentAfter=False, observableNextIdAfter=0, gameplayRngAfter=rng,
                  retirementInstructionBytes=image.bytes(0x422821, 10).hex(),
                  executableSha256=image.data and hashlib.sha256(image.data).hexdigest(),
                  imageHelperSha256=SHA(HELPER), nativeToolSha256=SHA(Path(__file__)),
                  scope='Original4226c0 retirement executes unchanged under synthetic empty/detached owner preconditions. Original41da20 game cleanup also executes; one declared owned CRT-free allocation boundary returns to its actual caller. No fake game callback or thread time. Confirms owner pointer clears while global gameplay RNG remains; does not certify live enemies, registered callbacks, actual heap allocator, fresh menus, resources, thread scheduling or whole-game behavior.')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(instructionExecutionPassed=True, ownerPresentAfter=False,
                         observableNextIdAfter=0, gameplayCallsAfter=66446, controlledCrtFreeBoundaries=1)))


if __name__ == '__main__':
    main()
