"""Verify read-only restore order and keep a matching clock candidate unaccepted."""
from pathlib import Path
import argparse, hashlib, json, struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-rng-order-observer-nov04'
N=R/'artifacts/th14/replay-rng-store-trace-nov04';V=R/'artifacts/th14/replay-rng-store-vm-trace-nov04'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true')
    p.add_argument('--output',type=Path,default=R/'docs/porting/th14-replay-rng-order-nov04.json');a=p.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    core=load(R/'artifacts/th14/replay-rng-restore-nov04/step-candidate/core/observer-build.json')
    build=load(H/'build-v2/observer-build.json');assert core['wasmSha256']=='1e15bb751d12dac304d3d48ec5f70c4a222221c6f4ce444ebb3507773e0e239d'
    assert build['objectBindings']==core['objectBindings'] and len(build['objectBindings'])==141
    for row in build['objectBindings']:assert sha(Path(row['path']).read_bytes())==row['sha256']
    assert build['sourceHashes']==core['sourceHashes'] and build['headerHashes']==core['headerHashes']
    for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():assert sha((Path(core['sourceSnapshotRoot'])/name).read_bytes())==digest
    assert build['engineSourcesRecompiledForThisLink']==0 and build['engineObjectsReusedForThisLink']==141
    assert build['wasmSha256']==sha(read(H/'build-v2/observer.wasm'))
    assert build['buildToolSha256']==sha(read(R/'tools/th14-build-replay-rng-order-observer-nov04.py'))
    assert read(Path(build['fixtureGraphRoot']))==read(R/'runtimes/th12/th12_web/tests/cpp/th14-replay-rng-order-observer-fixture-nov04.cpp')
    for path,digest in build['fixtureDependencyHashes'].items():assert sha(Path(path).read_bytes())==digest
    prepared=load(H/'drivers-public/prepared.json')
    assert prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-order-drivers-nov04.py'))
    assert prepared['baseDriverSha256']==sha(read(R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs'))
    assert prepared['readOnlyDriverSha256']==sha(read(H/'drivers-public/driver.mjs'))==sha(read(H/'driver.mjs'))
    assert prepared['hypothesisDriverSha256']==sha(read(H/'drivers-public/hypothesis-driver.mjs'))
    control=H/'run/model';candidate=H/'public-hypothesis-run/model';baseline=N/'comparison/model'
    control_end=load(H/'run/end.json');candidate_end=load(H/'public-hypothesis-run/end.json')
    assert control_end['exitCode']==1 and control_end['guardStop']is None and control_end['allObservedPortablePayloadsUnchanged']
    assert candidate_end['exitCode']==0 and candidate_end['guardStop']is None
    control_report=load(control/'report.json');candidate_report=load(candidate/'report.json')
    assert control_report['wasmSha256']==candidate_report['wasmSha256']==build['wasmSha256']
    assert control_report['comparisonToolSha256']==prepared['readOnlyDriverSha256']
    assert candidate_report['comparisonToolSha256']==prepared['hypothesisDriverSha256']
    assert control_report['differenceCounts']=={'21':9228,'22':615,'26':77} and not candidate_report['differenceCounts']
    assert candidate_report['hostNormalBoundaryMode']=='proposed' and candidate_report['normalBoundaryTimestampAssumptionDeclared']
    assert not candidate_report['exactOriginalInstructionBoundaryAccepted'] and candidate_report['unacceptedInitializationBoundaryHypothesis']['originalExactVmIdentityNotProven']
    assert not candidate_report['unacceptedInitializationBoundaryHypothesis']['acceptedOriginalEquivalence']
    payloads=['selected-state.u32','portable-camera.u32','portable-hud.u32',*[f'portable-live-{n}.json'for n in [1,26000,30000,36000,38900]]]
    for name in payloads:assert read(control/name)==read(baseline/name)
    control_rows=load(control/'replay-rng-order.json');candidate_rows=load(candidate/'replay-rng-order.json')
    assert not control_rows['overflow'] and not candidate_rows['overflow'] and not control_rows['hostClockOverridesAdded'] and candidate_rows['hostClockOverridesAdded']
    left=[row for row in control_rows['rows']if row[0]==2];right=[row for row in candidate_rows['rows']if row[0]==2]
    assert len(left)==len(right)==3 and [row[1]for row in left]==[row[1]for row in right]==[0,2,3]
    assert all(row[2:4]==[30772,3]and row[13]==9 for row in left+right)
    assert all(row[5]==1579428 and row[8:13]==[0xffffffff]*5 for row in left)
    assert left[0][4]==61987 and left[1][4]==left[2][4]==44160
    assert all(row[5]==1579404 and row[8:13]==[2,16,2,17,84]for row in right)
    assert right[0][4]==15160 and right[1][4]==right[2][4]==44160
    assert left[-1][7]==right[-1][7]==0
    raw=load(H/'proposed-raw.json')
    assert raw['verifiedFiniteEvidence'] and raw['diagnosticPrefixOnly'] and raw['callbacks']==40000
    assert raw['proposedNormalBoundaryAssumption'] and not raw['exactOriginalInstructionBoundaryAccepted']
    assert raw['wasmSha256']==build['wasmSha256'] and raw['vm303Rows']==1665 and raw['combatCheckpoints']==411
    assert raw['verifierSha256']==sha(read(R/'tools/th14-verify-native-campaign.py'))
    for path,binding in raw['bindings'].items():assert len((R/path).read_bytes())==binding['bytes'] and sha((R/path).read_bytes())==binding['sha256']
    gate=load(H/'public-hypothesis-gate/end.json');log=read(H/'public-hypothesis-gate/gate.log')
    assert gate['exitCode']==1 and gate['expectedCustomDriverRejection'] and gate['unprovenClockPlacementNotPromoted']
    assert b'Unreviewed Scene scheduler driver'in log and not(H/'public-hypothesis-gate/raw.json').exists()
    read(R/'tools/th14-verify-native-scene-boundaries-nov03.py')
    # The second original record retains actual normal-VM edge observations;
    # their existence does not turn them into a template-copy observation.
    vp=load(V/'prepared.json');vr=load(V/'native/report.json');ve=load(V/'process-end.json')
    assert vp['preparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-store-vm-observer-nov04.py'))
    assert vp['observerSha256']==vr['sourceSha256']==sha(read(V/'observer.py'))==sha(read(V/'native/observer-source.py'))
    assert ve['exitCode']==1 and ve['guardStop']is None and vr['childExited'] and vr['callbacks']==35000 and not vr['error'] and not vr['debugErrors']
    assert vr['hardwareBreakpointsOnly'] and vr['instructionBytesPatched']==vr['rngOrCounterWrites']==0
    assert bytes.fromhex(vr['configHex'])[0x22:0x24]==bytes(2) and vr['gameStateWordWrites']==1 and vr['caseInitialization']['attractBitClearOnly']
    event_bytes=read(V/'native/normal-vm-window-events.jsonl');assert sha(event_bytes)==vr['normalVmWindowEventsSha256']
    edges=[json.loads(line)for line in event_bytes.splitlines()];assert len(edges)==vr['normalVmWindowEvents']==4244
    assert [row['ordinal']for row in edges]==list(range(1,4245))
    for first,last in zip(edges[::2],edges[1::2],strict=True):
        assert (first['pc'],last['pc'])==(0x47e65b,0x47e660) and first['vm']==last['vm'] and last['callEntryOrdinal']==first['ordinal']
    store_bytes=read(V/'native/replay-rng-store-events.jsonl');assert sha(store_bytes)==vr['replayRngStoreEventsSha256']
    stores=[json.loads(line)for line in store_bytes.splitlines()];assert len(stores)==vr['replayRngStoreEvents']==8
    assert all(row['mainThreadContextAtWorkerDebugEvent']['registers']['eip']in(0x47e65b,0x47e660)for row in stores)
    assert not any('mainTemplateCopy'in row for row in stores)
    observed=[]
    for row in stores:
        call=row['normalVmCallAtWorkerStore'];entry=call['observedCall']
        if entry is None:continue
        assert entry==edges[entry['ordinal']-1]
        snapshot=call['snapshot'];assert snapshot['callIdentityStillMatches']
        blob=bytes.fromhex(snapshot['rawVmHex']);assert len(blob)==0x5cc
        identity=dict(handle=struct.unpack_from('<I',blob,0x540)[0],file=struct.unpack_from('<H',blob,0x36)[0],script=struct.unpack_from('<H',blob,0x4aa)[0])
        assert identity==snapshot['identity'] and identity=={key:entry[key]for key in identity}
        observed.append(dict(stage=row['stage'],workerPc=row['pc'],mainPc=row['mainThreadContextAtWorkerDebugEvent']['registers']['eip'],**identity,mainAtReturnPc=True))
    assert len(observed)==3
    comparison=load(V/'comparison/end.json');vm=load(V/'comparison/model/report.json')
    assert not comparison['strictAndIndependentPassed'] and comparison['model']['exitCode']==comparison['verifier']['exitCode']==1
    native=read(V/'native/selected-state.u32');portable=read(V/'comparison/model/selected-state.u32');assert len(native)==len(portable)==35000*128
    counts=[0]*32
    for x,y in zip(struct.iter_unpack('<32I',native),struct.iter_unpack('<32I',portable),strict=True):
        for i in range(32):counts[i]+=x[i]!=y[i]
    assert counts[21:23]==[16663,5579] and counts[26]==6 and sum(counts)==22248
    assert vm['wasmSha256']==core['wasmSha256']
    result=dict(verifiedReadOnlyReplayRngOrder=True,productionCoreCommit='7babb540918c13f7d813eb14ea09db1da2112bcd',productionCoreWasmSha256=core['wasmSha256'],
        all141ProductionObjectsUnchanged=True,rootProductionSourcesModified=False,readOnlyControlCallbacks=40000,readOnlyControlRows=len(control_rows['rows']),
        allEightPortableControlPayloadsByteIdentical=True,observedRestoreScriptCalls=1579428,proposedRestoreScriptCalls=1579404,scriptDrawsBetweenRestorePositions=24,
        proposedRawFieldsRecomputed=True,proposedCallbacks=40000,proposedVm303Rows=1665,proposedCombatCheckpoints=411,
        proposedAllSelectedCameraHudVmCombatAndInitialPublicationsEqual=True,proposedOriginalVmIdentityAccepted=False,proposedV4Accepted=False,proposedV4Rejection='Unreviewed Scene scheduler driver',
        secondOriginalCallbacks=35000,secondOriginalDebugExceptions=0,secondOriginalVmEdgeEvents=4244,secondOriginalStoreEvents=8,secondOriginalTemplateCopySnapshots=0,
        secondOriginalCallIdentitiesAtWorkerEvents=observed,secondOriginalSelectedDifferenceCounts=counts,secondOriginalStrictAccepted=False,
        nativeRngOrStateValuesProvidedToEngine=False,newOrdinaryBrowserTimingAccepted=False,oldRngOrBulletFailuresClosed=False,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    output=a.output.resolve();assert output.is_relative_to(R/'docs/porting')or output.is_relative_to(H)
    data=(json.dumps(result,indent=2)+'\n').encode()
    if a.check:assert output.read_bytes()==data
    else:assert not output.exists();output.write_bytes(data)
    print(json.dumps({k:v for k,v in result.items()if k not in('bindings','secondOriginalCallIdentitiesAtWorkerEvents','secondOriginalSelectedDifferenceCounts')}))


if __name__=='__main__':main()
