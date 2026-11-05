"""Bind native stopped main contexts to separate worker acknowledgement edges."""
from pathlib import Path
import hashlib
import json

R = Path(__file__).resolve().parents[1]
OLD = R / 'artifacts/th14/original-nine-shot-native-nov05'
H = R / 'artifacts/th14/natural-store-boundaries-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    H.mkdir(exist_ok=True)
    output = H / 'native-boundaries.json'
    assert not output.exists()
    bindings = {}

    def raw(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    race = load(OLD / 'natural-overlap.json')
    assert race['verifiedNaturalSeedReadSpansReplayStore']
    assert race['workerScriptStoreValueRecoveredFromAx']
    for name, row in race['evidenceBindings'].items():
        data = raw(R / name)
        assert len(data) == row['bytes'] and SHA(data) == row['sha256']
    native = OLD / 'prefix-slots-v2/native'
    stores = [json.loads(line) for line in raw(native / 'replay-rng-store-events.jsonl').splitlines()
              if json.loads(line)['stage'] == 3]
    edges = [json.loads(line) for line in raw(native / 'stage-object-vm-window-events.jsonl').splitlines()]
    assert [row['pc'] for row in stores] == [0x456115,0x456129,0x456133,0x456135]
    assert all(row['precedingPlayerCallbacks'] == race['precedingPlayerCallbacks'] for row in stores)
    call = stores[1]['stageObjectVmCallAtWorkerStore']['observedCall']
    assert call['pc'] == 0x40f2a2 and call['file'] == 3 and call['script'] == 7
    ctx = call['stageObjectContext']
    assert ctx['actualVmArrayAndPrimitiveIndexAgree'] and ctx['currentExecutingObjectIdentityObserved']
    assert [ctx[key] for key in ['objectIndex','primitiveIndex','animationIndex']] == [6,0,8]
    import struct
    assert struct.unpack_from('<I', bytes.fromhex(ctx['rawOwnerPrefixHex']))[0] == 2
    returned = next(row for row in edges if row['pc'] == 0x40f2a7 and row['callEntryOrdinal'] == call['ordinal'])
    next_call = next(row for row in edges if row['pc'] == 0x40f2a2 and row['debugEventSequence'] > stores[3]['debugEventSequence'])
    assert returned['vm'] == call['vm'] and returned['file'] == call['file'] and returned['script'] == call['script']
    assert next_call['precedingPlayerCallbacks'] == call['precedingPlayerCallbacks']
    nctx = next_call['stageObjectContext']
    assert nctx['objectIndex'] == 6 and nctx['primitiveIndex'] == 1 and nctx['animationIndex'] == 9
    assert next_call['file'] == 3 and next_call['script'] == 7
    pending = [row['mainThreadContextAtWorkerDebugEvent'] for row in stores]
    assert [row['registers']['eip'] for row in pending] == [0x40f2a2,0x403376,0x40f2a7,0x40f2a2]
    assert all(row['debugStatus'] & mask for row, mask in zip(pending,[4,8,4,4]))
    assert pending[0]['registers']['ecx'] == call['vm']
    assert pending[3]['registers']['ecx'] == next_call['vm']
    assert stores[0]['stageObjectVmCallAtWorkerStore']['mainCallEdgePending']
    assert stores[2]['stageObjectVmCallAtWorkerStore']['mainReturnEdgePending']
    assert stores[3]['stageObjectVmCallAtWorkerStore']['mainCallEdgePending']
    assert stores[2]['stageObjectVmCallAtWorkerStore']['observedCall']['ordinal'] == call['ordinal']
    sequence = [stores[0],call,stores[1],stores[2],returned,stores[3],next_call]
    assert all(a['debugEventSequence'] < b['debugEventSequence'] for a,b in zip(sequence,sequence[1:]))
    result = dict(schema='th14/natural-worker-store-boundaries/1', verifiedNativeAcknowledgementEdges=True,
        stage=3, callback=race['precedingPlayerCallbacks'], ownerStage=2,
        objectIndex=6, firstPrimitive=0, firstAnimation=8, nextPrimitive=1, nextAnimation=9,
        file=3, script=7, firstCallEntryOrdinal=call['ordinal'], nextCallEntryOrdinal=next_call['ordinal'],
        storeReceiptNs=[row['hostMonotonicNs'] for row in stores],
        acknowledgementEdges=['first-object-VM-before-call','first-script-seed-read',
                              'first-object-VM-after-return','next-object-VM-before-call'],
        allWorkerContextsHavePendingMainHardwareEvents=True,
        workerContextAddressesAndPrimitiveVmIndicesAgree=True,
        firstScriptReadSpansWorkerReplaySeedWrite=True,
        noNativeRngOrVmValuesProvidedToEngine=True,
        logicalAcknowledgementBoundariesOnly=True,
        exactMainInstructionAtEarlierWorkerStoreProven=False,
        crossThreadInstructionExecutionTimesRecovered=False,
        independentTimingAccepted=False, productionChanged=False, completeGame=False,
        evidenceBindings=bindings, verifierSha256=SHA(Path(__file__).read_bytes()))
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['verifiedNativeAcknowledgementEdges','callback',
        'ownerStage','objectIndex','firstAnimation','nextAnimation','logicalAcknowledgementBoundariesOnly']}))


if __name__ == '__main__':
    main()
