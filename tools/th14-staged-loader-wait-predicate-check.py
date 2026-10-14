"""Execute original loader wait predicates, stopping before every host call.

Declared guard/config values test signed branch semantics. No Sleep is executed
or simulated and no native thread duration or completion event is fabricated.
"""
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EBX, UC_X86_REG_EIP, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'tools/th14-loading-lifecycle-evidence-check.py'
OUTPUT = ROOT / 'docs/porting/th14-staged-loader-wait-predicate-verified-oct14.json'
SHA = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('retail_wait_image', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    image = helper.Image()
    assert image.imports()[0x4b10a4] == dict(library='KERNEL32.dll', function='Sleep')
    cases = []

    def observe(entry, guard, flags, initial_stage):
        machine = image.machine()
        for address, value in ((0x4db558, 0x600000), (0x4f56cc, 0x620000),
                               (0x620020, guard & 0xffffffff), (0x4d9684, flags),
                               (0x4d9658, initial_stage), (0x7ff000, 0x710000)):
            helper.word(machine, address, value)
        helper.word(machine, 0x600080, 0 if entry == 0x435ab0 else 4)
        machine.mem_write(0x4db510, struct.pack('<HHI', 49408, 0, 66446))
        machine.reg_write(UC_X86_REG_ESP, 0x7ff000)
        machine.reg_write(UC_X86_REG_EBX, 0x600000)
        observed = {}
        stop_at = {0x435af2: 'requestSleep1ms', 0x435b0f: 'requestSleep60ms',
                   0x435b11: 'continueWithoutMinimumSleep', 0x435f6f: 'abortBranch'}

        def stop_before_host_or_next_phase(uc, address, size, user):
            if address not in stop_at:
                return
            observed.update(stop=hex(address), branch=stop_at[address])
            if address in (0x435af2, 0x435b0f):
                stack = uc.reg_read(UC_X86_REG_ESP)
                observed['requestedSleepMilliseconds'] = struct.unpack('<I', uc.mem_read(stack, 4))[0]
                observed['hostCallInstructionBytes'] = image.bytes(address, 2).hex()
            uc.emu_stop()

        machine.hook_add(UC_HOOK_CODE, stop_before_host_or_next_phase)
        machine.emu_start(entry, 0x710000, count=500)
        assert observed and hex(machine.reg_read(UC_X86_REG_EIP)) == observed['stop']
        expected = ('requestSleep1ms' if guard >= 0 else
                    ('requestSleep60ms' if initial_stage == 0 else 'continueWithoutMinimumSleep'))
        if guard >= 0 and flags & 0x180:
            expected = 'abortBranch'
        assert observed['branch'] == expected
        if observed['branch'] == 'requestSleep1ms':
            assert observed['requestedSleepMilliseconds'] == 1
        if observed['branch'] == 'requestSleep60ms':
            assert observed['requestedSleepMilliseconds'] == 60
        rng = list(struct.unpack('<HHI', machine.mem_read(0x4db510, 8)))
        assert rng == [49408, 0, 66446]
        assert struct.unpack('<i', machine.mem_read(0x620020, 4))[0] == guard
        assert struct.unpack('<I', machine.mem_read(0x600080, 4))[0] == 4
        row = dict(entry=hex(entry), entryKind='workerEntry' if entry == 0x435ab0 else 'independentRecheckBranch',
                   declaredSignedGuard=guard, declaredGuardWord=guard & 0xffffffff,
                   supervisorFlags=flags, initialStageFlag=initial_stage,
                   **observed, gameplayRngUnchanged=rng, sleepCallsExecuted=0,
                   simulatedGameCalls=0, threadTimeGenerated=False)
        cases.append(row)
        return row

    guards = [-2147483648, -2, -1, 0, 1, 2147483647]
    for entry in (0x435ab0, 0x435af4):
        for guard in guards:
            for flags in (0, 0x80, 0x100, 0x180):
                for initial_stage in (0, 1):
                    observe(entry, guard, flags, initial_stage)
    assert len(cases) == 96
    # These are two separately initialized branch tests, not a simulated
    # Sleep completion or a guessed native scheduler timeline.
    comparisons = []
    for before, after in ((0, -1), (1, 0), (1, -1), (0, 1)):
        first = next(r for r in cases if r['entry'] == '0x435ab0' and r['declaredSignedGuard'] == before
                     and r['supervisorFlags'] == 0 and r['initialStageFlag'] == 0)
        second = next(r for r in cases if r['entry'] == '0x435af4' and r['declaredSignedGuard'] == after
                      and r['supervisorFlags'] == 0 and r['initialStageFlag'] == 0)
        comparisons.append(dict(independentBeforeGuard=before, independentRecheckGuard=after,
                                beforeBranch=first['branch'], recheckBranch=second['branch'],
                                timeOrSleepReturnNotSimulated=True))
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    addresses = [0x435aca, 0x435acf, 0x435ad3, 0x435ad8, 0x435ae0, 0x435aea,
                 0x435af0, 0x435af2, 0x435af4, 0x435af9, 0x435b02, 0x435b04,
                 0x435b0b, 0x435b0d, 0x435b0f]
    instructions = []
    for address in addresses:
        instruction = next(md.disasm(image.bytes(address, 15), address, count=1))
        instructions.append(dict(address=hex(address), bytes=bytes(instruction.bytes).hex(),
                                 mnemonic=instruction.mnemonic, operands=instruction.op_str))
    assert next(i for i in instructions if i['address'] == '0x435ad8')['mnemonic'] == 'jl'
    assert next(i for i in instructions if i['address'] == '0x435b02')['mnemonic'] == 'jge'
    engine_path = ROOT / 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'
    engine = json.loads(engine_path.read_text())
    assert len(engine['sourceHashes']) == 265
    for name, digest in engine['sourceHashes'].items():
        assert SHA(ROOT / 'runtimes/th12/th12_web' / name) == digest, name
    result = dict(diagnosticOnly=True, predicateEvidencePassed=True, completeGame=False,
                  nativeEquivalent=False, productionChanged=False, actualRetailProcessesStarted=0,
                  caseCount=96, instructionBudgetPerCase=500, cases=cases,
                  independentBranchComparisons=comparisons, originalInstructions=instructions,
                  sleepImport=dict(iat='0x4b10a4', library='KERNEL32.dll', function='Sleep'),
                  provenPredicate='The signed32 word at [*(4f56cc)+20] must be negative to leave the wait loop. Zero and all positive values remain waiting. While waiting, supervisor flags0x180 choose the abort branch. The subsequent minimum Sleep60 request happens only for initialStageFlag4d9658==0.',
                  guardMeaningProven=False,
                  guardMappingLimitation='This proves the actual signed branch predicate, not whether the word means a rendering phase, resource ownership fence or another ANM operation. Its production meaning requires original writers/callers to be traced; renderer.flush or references()==0 cannot be substituted without that evidence.',
                  sleepCallsExecuted=0, simulatedGameCalls=0, nativeThreadTimeGenerated=False,
                  sourceFilesVerified=265, sourceHashes=engine['sourceHashes'],
                  bindings=[dict(path=HELPER.relative_to(ROOT).as_posix(), sha256=SHA(HELPER)),
                            dict(path=engine_path.relative_to(ROOT).as_posix(), sha256=SHA(engine_path))],
                  executableSha256=hashlib.sha256(image.data).hexdigest(), verifierSha256=SHA(Path(__file__)),
                  scope='Unchanged original loader branches executed under declared synthetic guard/config values and stopped before every Sleep/abort/next-phase call. Independent worker-entry and recheck tests are not joined by fake Sleep returns or scheduler durations. Signed predicate and conditional1/60ms requests are proven; host wait completion, field ownership meaning, actual thread times, ordinary menus/rendering or whole-game equivalence are not. Current265 source hashes bind implementation-design context only; no production behavior was modified.')
    OUTPUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(predicateEvidencePassed=True, cases=96, sleepCallsExecuted=0,
                         nativeThreadTimeGenerated=False, signedNegativeGuardRequired=True,
                         sourceFilesVerified=265, output=OUTPUT.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
