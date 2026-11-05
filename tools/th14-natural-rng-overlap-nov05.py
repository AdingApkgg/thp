"""Seal a naturally observed seed-load/replay-restore/stale-store episode.

Public metadata records only identities, time boundaries, counts and hashes.
Debugger receipt order is not claimed to recover cross-thread instruction time.
"""
from pathlib import Path
import hashlib
import json
import struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-native-nov05'
N = H / 'prefix-slots-v2/native'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    output = H / 'natural-overlap.json'
    assert not output.exists()
    bindings = {}

    def raw(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    def rows(name):
        return [json.loads(line) for line in raw(N / name).splitlines()]

    proof = load(H / 'native-register-proof.json')
    report = load(N / 'report.json')
    assert proof['verifiedFiniteOriginalRegisterReadEvidence']
    assert proof['accessEvents'] == proof['decodedRegisterValues'] == report['scriptRngRegisterAccessEvents'] == 66
    assert proof['arithmeticPairsEqual'] == 33
    assert proof['globalSnapshotMismatchCounts'] == {'mix32': 1}
    for name, row in proof['bindings'].items():
        data = raw(R / name)
        assert SHA(data) == row['sha256'] and len(data) == row['bytes']
    access = rows('script-rng-access-events.jsonl')
    read, write, next_read = access[:3]
    assert [row['instructionContract']['kind'] for row in [read, write, next_read]] == ['mix32','store32','mix32']
    assert [row['pc'] for row in [read, write]] == [0x403339, 0x403376]
    assert read['threadId'] == write['threadId'] == next_read['threadId']
    stage, callback = read['stage'], read['precedingPlayerCallbacks']
    assert stage == 3 and callback == 30744
    assert all(row['stage'] == stage and row['precedingPlayerCallbacks'] == callback for row in [write, next_read])
    restore = [row for row in rows('replay-rng-store-events.jsonl') if row['stage'] == stage]
    assert [row['pc'] for row in restore] == [0x456115,0x456129,0x456133,0x456135]
    assert all(row['precedingPlayerCallbacks'] == callback for row in restore)
    assert restore[0]['threadId'] != read['threadId']
    assert len({row['threadId'] for row in restore}) == 1
    ordered = [restore[0], read, restore[1], write, restore[2], restore[3], next_read]
    assert all(a['debugEventSequence'] < b['debugEventSequence'] and a['hostMonotonicNs'] < b['hostMonotonicNs']
               for a, b in zip(ordered, ordered[1:]))
    rng = [struct.unpack('<4I', bytes.fromhex(row['rngHex'])) for row in restore]
    before = read['valueRetainedByTrappedInstruction']
    stale = write['valueRetainedByTrappedInstruction']
    replay_seed = restore[1]['replaySeedWord']
    assert restore[1]['registers']['eax']&0xffff == replay_seed
    assert restore[1]['completedWritePc'] == 0x456123
    import sys
    sys.path.insert(0, str(R / 'tools'))
    image = __import__('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data) == report['executableSha256']
    assert image.read(0x456123, 6).hex() == '66a308b54d00'
    assert before == rng[0][0]&0xffff
    assert before != replay_seed and stale != replay_seed
    # The first mix has already retained the old input in AX, while memory
    # holds the worker's replacement. The later worker breakpoint snapshot
    # already sees the main store: it must not stand in for the worker's AX.
    assert struct.unpack_from('<H', bytes.fromhex(read['rngHexAtObservation']))[0] == replay_seed
    assert rng[1][0]&0xffff == stale
    step = lambda value: ((((value^0x9630)-0x6553)&0xffff)<<2 | (((value^0x9630)-0x6553)&0xffff)>>14)&0xffff
    assert step(step(before)) == stale
    assert struct.unpack_from('<H', bytes.fromhex(write['rngHexAtObservation']))[0] == stale
    assert rng[2][0]&0xffff == rng[3][0]&0xffff == stale
    assert next_read['valueRetainedByTrappedInstruction'] == stale
    assert rng[2][3] == 0 and rng[2] == rng[3]
    pumps = [row for row in rows('rotating-watch-pump-events.jsonl')
             if row['stage'] == stage and row['precedingPlayerCallbacks'] == callback
             and row['pc'] == 0x47d720 and row['hostMonotonicNs'] < restore[0]['hostMonotonicNs']]
    assert len(pumps) == 1
    failed = load(H / 'comparison-off/result.json')
    model = load(H / 'comparison-off/model/report.json')
    assert failed['strictDriverExitCode'] == failed['rawVerifierExitCode'] == 1
    assert model['differenceCounts'] == {'21':4256,'22':344,'26':2}
    assert model['firstDifference']['index'] == callback and model['firstDifference']['stage'] == 3
    assert model['firstDifference']['stageFrame'] == 0 and model['firstDifference']['word'] == 21
    result = dict(schema='th14/natural-seed-overlap/1', verifiedNaturalSeedReadSpansReplayStore=True,
        stage=stage, precedingPlayerCallbacks=callback, accessEvents=66, pairedNext32Calls=33,
        mainLoadPc='0x403336', mainStorePc='0x403373', workerScriptSeedAfterPc='0x456129',
        mainReadsOldSeed=True, workerPublishesDifferentReplaySeed=True,
        mainStoreUsesOwnEarlierRead=True, mainStoreOverwritesWorkerPublishedSeed=True,
        nextReadLoadsThatMainStore=True, globalSnapshotMismatchCounts=proof['globalSnapshotMismatchCounts'],
        workerScriptStoreValueRecoveredFromAx=True,
        laterWorkerMemorySnapshotAlreadyContainsMainStore=True,
        observedPumpNs=pumps[0]['hostMonotonicNs'], firstReadReceiptNs=read['hostMonotonicNs'],
        scriptSeedStoreReceiptNs=restore[1]['hostMonotonicNs'], firstMainStoreReceiptNs=write['hostMonotonicNs'],
        initializeReadyReceiptNs=restore[2]['hostMonotonicNs'], globalsCopyReceiptNs=restore[3]['hostMonotonicNs'],
        nextReadReceiptNs=next_read['hostMonotonicNs'],
        failedAtomicDeliveryDifferenceCounts=model['differenceCounts'],
        exactCrossThreadExecutionTimesRecovered=False, ordinaryOriginalGuiAccepted=False,
        observationIsOneActualUnforcedDebuggedRun=True, controlledSuspendOrResumeAdded=False,
        additionalGameMemoryWrites=0, productionChanged=False,
        seedsProvidedToPortableEngine=False, proposedDeliveryIsFiniteLogicalOrderDiagnostic=True,
        gameplayCounterClearAndGlobalsCopyNotPlacedAtTheirExactOriginalMainInstruction=True,
        independentTimingAccepted=False, oldNineDifferencesClosed=False,
        completeGame=False, nativeEquivalent=False, evidenceBindings=bindings,
        verifierSha256=SHA(Path(__file__).read_bytes()))
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ['verifiedNaturalSeedReadSpansReplayStore',
        'stage','precedingPlayerCallbacks','accessEvents','pairedNext32Calls',
        'mainStoreOverwritesWorkerPublishedSeed','independentTimingAccepted']}))


if __name__ == '__main__':
    main()
