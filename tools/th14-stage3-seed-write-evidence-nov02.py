"""Verify finite native RNG writes, keeping debugger delivery separate from execution."""
from pathlib import Path
import argparse
import ast
import collections
import hashlib
import importlib
import json
import struct
import sys

R = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
EXE = 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'


def step(seed):
    mixed = ((seed ^ 0x9630) - 0x6553) & 0xffff
    return ((mixed << 2) | (mixed >> 14)) & 0xffff


def evidence(home):
    home = home.resolve(strict=True)
    assert home.is_relative_to(R / 'artifacts/th14')
    native = home / 'native'
    bindings = {}

    def raw(path):
        path = path.resolve(strict=True)
        assert path.is_relative_to(R)
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    report = load(native / 'report.json')
    end = load(home / 'process-end.json')
    plan = load(home / 'plan.json')
    preflight = load(home / 'preflight.json')
    arm = load(native / 'script-seed-watch-arm.json')
    quiet = load(home / 'native-silence-verified.json')
    assert end['observerExitCode'] == end['expectedDiagnosticExitCode'] == 1
    assert end['guardStop'] is None and end['actualMastersZero']
    assert report['childExited'] and not report['error'] and not report['debugErrors']
    assert report['callbacks'] == 26000 and report['diagnosticPrefixOnly']
    assert not report['observedForcedReplayEndMenu'] and not report['inputInjected']
    assert report['hardwareBreakpointsOnly'] and report['instructionBytesPatched'] == 0
    assert report['rngOrCounterWrites'] == 0 and report['gameStateWordWrites'] == 1
    assert report['caseInitialization']['attractBitClearOnly']
    assert report['executableSha256'] == EXE
    assert report['sourceFullReplaySha256'] == '1d1b7da60739afc9b6d1ee5eb143e2a59e6a29b712096871874fa7bd72391a5d'
    assert not report['observerOptions']['normal_vm_window_events']
    assert not report['observerOptions']['worker_active_vm_snapshot']
    assert report['scriptSeedAdditionalGameOrSuspendWrites'] == 0
    assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativeExecutableSha256'] == EXE
    assert quiet['nativePid'] == report['pid']
    assert quiet['processStartSha256'] == SHA(raw(native / 'process-start.json'))
    assert len(quiet['samples']) == 2
    for sample in quiet['samples']:
        assert [sample[k] for k in ['musicConfig', 'effectsConfig', 'musicMaster', 'effectsMaster']] == [0, 0, 0, 0]
    source = raw(R / 'tools/th14-stage3-seed-write-trace-observer-nov02.py')
    base = raw(R / 'tools/th14-stage3-seed-store-minimal-observer-nov01.py')
    assert SHA(source) == report['sourceSha256'] == plan['sourceSha256'] == preflight['sourceSha256']
    assert SHA(base) == preflight['baseSourceSha256']

    def mutation_calls(code):
        names = {'WriteProcessMemory', 'SuspendThread', 'ResumeThread', 'Wow64SetThreadContext'}
        return [ast.dump(x, include_attributes=False) for x in ast.walk(ast.parse(code))
                if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr in names]

    assert mutation_calls(source) == mutation_calls(base)
    assert preflight['additionalHardwareContextInstallationsDeclared']
    assert preflight['additionalGameOrSuspendWriteCalls'] == 0
    assert plan['maximumCallbacks'] == 26000 and plan['maximumSeconds'] == 1200
    assert plan['maximumObservationMiB'] == 128 and plan['minimumFreeGiB'] == 100
    assert arm['mainSlot'] == 3 and arm['workerSlot'] == 0
    assert arm['watchAddress'] == 0x4db508 and arm['watchBytes'] == 2
    assert arm['maximumEvents'] == 512 and arm['desiredPostRestoreWrites'] == 64
    assert report['scriptSeedWriteWatchArmed']
    content = raw(native / 'script-seed-write-events.jsonl')
    assert SHA(content) == report['scriptSeedWriteEventsSha256']
    rows = [json.loads(line) for line in content.decode().splitlines()]
    assert 0 < len(rows) <= 512 and len(rows) == report['scriptSeedWriteEvents']
    assert [x['ordinal'] for x in rows] == list(range(1, len(rows) + 1))
    assert all(a['hostMonotonicNs'] < b['hostMonotonicNs'] for a, b in zip(rows, rows[1:]))
    assert sorted({x['threadId'] for x in rows}) == report['scriptSeedWritingThreadIds']
    assert {x['threadId'] for x in rows} <= set(arm['registeredThreads'])
    assert sum(x['isMainThread'] for x in rows) == report['scriptSeedMainWrites']
    assert sum(not x['isMainThread'] for x in rows) == report['scriptSeedWorkerWrites']
    assert max(x['postRestoreWriteOrdinal'] for x in rows) == report['scriptSeedPostRestoreWrites'] == 64
    boundaries_raw = raw(native / 'seed-store-instruction-events.jsonl')
    assert SHA(boundaries_raw) == report['seedStoreInstructionEventsSha256']
    boundaries = [json.loads(line) for line in boundaries_raw.decode().splitlines()]
    assert report['seedStoreInstructionEvents'] == len(boundaries) == 2
    assert [x['pc'] for x in boundaries] == [0x456123, 0x456129]
    for event, prefix in zip(boundaries, ['66a308b54d00', 'c70514b54d0000000000'], strict=True):
        assert event['originalInstructionBytes'].startswith(prefix)
        assert event['readOnly'] and not event['providedToEngine']
        assert not event['threadSchedulingControlled'] and event['debuggerPausesAffectTiming']
        assert not event['normalVmEdgeBreakpointsEnabled']
    assert boundaries[0]['threadId'] == boundaries[1]['threadId']
    assert boundaries[0]['registers']['eax'] == boundaries[1]['registers']['eax']
    restored = boundaries[1]['registers']['eax'] & 0xffff

    # Execute the unchanged original instructions independently of the inverse
    # register equation. No emulated value is ever supplied to the game model.
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
                                  UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI,
                                  UC_X86_REG_ESP, UC_X86_REG_EBP)
    image, *_ = importlib.import_module('th-anm-handlers').handlers(14)
    executable = native / 'work/th14.exe'
    assert SHA(executable.read_bytes()) == EXE
    # handlers() uses the same verified original revision. Bind the bytes that
    # are actually executed as well as checking every captured store encoding.
    code = image.read(0x403310, 0x8b)
    assert code[0x63:0x66] == bytes.fromhex('66890e')
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x400000, 0x100000)
    uc.mem_map(0x100000, 0x10000)
    uc.mem_write(0x403310, code)
    registers = {'eax': UC_X86_REG_EAX, 'ebx': UC_X86_REG_EBX, 'ecx': UC_X86_REG_ECX,
                 'edx': UC_X86_REG_EDX, 'esi': UC_X86_REG_ESI, 'edi': UC_X86_REG_EDI}
    prior = None
    mismatches = []
    discontinuities = []
    writers = collections.Counter()
    paths = collections.Counter()
    main = []
    workers = []
    for row in rows:
        assert row['stage'] == 3 and row['watchAddress'] == 0x4db508 and row['watchBytes'] == 2
        assert row['readOnly'] and row['dataWriteHardwareTrap'] and not row['gameValuesProvidedToEngine']
        for name in ['onlyRegisteredOriginalCodeStartThreadsWatched',
                     'globalMemoryAtObservationNotNecessarilyValueWrittenByTrappedInstruction',
                     'crossThreadInstructionOrderNotAsserted', 'vmIdentityNotInferredFromRegisterAlone']:
            assert row[name]
        regs = row['registers']
        assert row['pc'] == regs['eip']
        slot = 3 if row['isMainThread'] else 0
        assert row['debugAddresses'][slot] == 0x4db508 and row['debugStatus'] & (1 << slot)
        assert ((row['debugControl'] >> (16 + 4 * slot)) & 15) == 5
        assert row['debugControl'] & (1 << (2 * slot))
        original = bytes.fromhex(row['originalCodeHex'])
        expected_pc, store = (0x403376, bytes.fromhex('66890e')) if row['isMainThread'] else (0x456129, bytes.fromhex('66a308b54d00'))
        assert row['pc'] == expected_pc
        offset = expected_pc - len(store) - row['originalCodeStart']
        assert offset >= 0 and original[offset:offset + len(store)] == store
        assert image.read(row['originalCodeStart'], len(original)) == original
        observed = struct.unpack_from('<H', bytes.fromhex(row['rngHexAtObservation']))[0]
        writers[(row['threadId'], row['pc'], row['isMainThread'])] += 1
        paths[tuple(x['returnPc'] for x in row['frameChain'][:5])] += 1
        if not row['isMainThread']:
            assert row['threadId'] == boundaries[1]['threadId']
            assert (regs['eax'] & 0xffff) == restored
            workers.append(dict(ordinal=row['ordinal'], storeValue=restored, observedMemory=observed))
            continue
        assert regs['esi'] == 0x4db508 and regs['edx'] == 0x6553
        # EDI is the zero-extended first mixed word, retained through the store.
        seed_read = ((regs['edi'] + 0x6553) & 0xffff) ^ 0x9630
        seed_written = regs['ecx'] & 0xffff
        assert step(step(seed_read)) == seed_written
        uc.mem_write(0x4db508, struct.pack('<2I', seed_read, 0))
        uc.reg_write(UC_X86_REG_ESP, 0x108000)
        uc.reg_write(UC_X86_REG_EBP, 0x108100)
        for register in registers.values():
            uc.reg_write(register, 0)
        uc.reg_write(UC_X86_REG_ECX, 0x4db508)
        uc.emu_start(0x403310, 0x403376, count=100)
        for name, register in registers.items():
            actual = uc.reg_read(register)
            assert (actual & 0xffff if name == 'ecx' else actual) == (regs[name] & 0xffff if name == 'ecx' else regs[name]), (row['ordinal'], name)
        assert bytes(uc.mem_read(0x4db508, 8)) == struct.pack('<2I', seed_written, 2)
        item = dict(ordinal=row['ordinal'], callback=row['precedingPlayerCallbacks'],
                    seedRead=seed_read, seedWritten=seed_written, observedMemory=observed)
        if prior is not None and seed_read != prior['seedWritten']:
            discontinuities.append(dict(**item, previousMainOrdinal=prior['ordinal'], previousMainSeedWritten=prior['seedWritten']))
        if observed != seed_written:
            mismatches.append(item)
        main.append(item)
        prior = item
    assert len(main) == 342 and len(workers) == 1
    assert len(mismatches) == len(discontinuities) == 1
    assert mismatches[0]['observedMemory'] == discontinuities[0]['seedRead'] == restored
    assert discontinuities[0]['previousMainOrdinal'] == mismatches[0]['ordinal']
    # The delivery order is explicitly NOT the write order in this witness.
    assert workers[0]['ordinal'] < mismatches[0]['ordinal']
    assert mismatches[0]['seedRead'] != restored
    assert len(raw(native / 'selected-state.u32')) == 26000 * 128
    assert len(raw(native / 'world-camera.raw')) == 26000 * 0x124
    assert len(raw(native / 'hud-score.u32')) == 26000 * 8
    sys.path.insert(0, str(R / 'tools'))
    storage = importlib.import_module('th14-test-storage')
    # The helper excludes only the case's immediate /work input aliases.
    # Apply it to native, then account for the small outer wrapper metadata.
    observation_bytes = storage.check_budget(native, 100 * 1024**3, 128 * 1024**2)
    observation_bytes += sum(p.stat().st_size for p in home.iterdir() if p.is_file())
    assert observation_bytes <= 128 * 1024**2
    return dict(verifiedFiniteNativeSeedWriteOperands=True, callbacks=26000,
                mainWriteOperandsIndependentlyEmulated=len(main), workerWriteOperands=len(workers),
                codeExecutedSha256=SHA(code), nativeExecutableSha256=EXE,
                writers=[dict(threadId=k[0], pc=k[1], mainThread=k[2], events=v) for k, v in writers.items()],
                callPaths=[dict(returnPcs=list(k), events=v) for k, v in paths.items()],
                memorySnapshotsDifferentFromStoreOperands=mismatches,
                mainThreadSeedReadDiscontinuities=discontinuities, workerStoreOperand=restored,
                debuggerDeliveryOrderIsNotWriteOrder=True,
                exactCrossThreadInstructionTotalOrderAccepted=False,
                onlyRegisteredOriginalCodeStartThreadsWatched=True,
                mainResourcePumpWatchReplacedDuringSeedWatch=True,
                normalVmLivenessOrIdentityAccepted=False,
                additionalHardwareContextInstallationsDeclared=True,
                additionalGameOrSuspendWriteCallSites=0, retainedAttractBitClearWrites=1,
                debuggerPausesAffectTiming=True, nativeValuesProvidedToEngine=False,
                productionCodeChanged=False, modelEquivalenceAccepted=False,
                originalNaturalReplayEndAccepted=False, ordinaryOriginalGuiAccepted=False,
                independentSchedulingAccepted=False, completeGame=False, nativeEquivalent=False,
                bindings=bindings, verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') or output.is_relative_to(R / 'docs/porting')
    result = evidence(args.case)
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k not in ['bindings', 'callPaths']}, ensure_ascii=False))
