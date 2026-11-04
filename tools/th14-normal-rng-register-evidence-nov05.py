"""Recompute the finite Normal RNG instruction/read-order episode.

Only counts, addresses, paths and hashes are emitted. Native register values,
seeds, raw observations, game assets and binaries are never public output.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil, struct, subprocess, sys, tempfile

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
N=H/'prefix-pending-status/native'
F=H/'portable-audit-native-prefix-v3'
M=F/'model'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def verify():
    bindings={}
    def raw(path):
        path=Path(path).resolve();assert path.is_relative_to(R)
        value=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(value),sha256=SHA(value));return value
    def load(path):return json.loads(raw(path))
    def module(path,name):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
    manifest=load(H/'tool-sources-final/manifest.json')
    for name,item in manifest.items():
        value=raw(R/name);assert len(value)==item['bytes']and SHA(value)==item['sha256']
        assert raw(H/'tool-sources-final'/Path(name).name)==value
    component=load(H/'component/report.json')
    regenerated=module(R/'tools/th14-rng-register-generation-component-nov05.py','rng_component').verify()
    assert regenerated==component
    assert component['cases']==210 and component['laterGlobalSnapshotWrong']==189
    negative=load(H/'pending-status-negative-retry1/report.json')
    positive=load(H/'pending-status-positive-retry1/report.json')
    fixture=load(H/'pending-status-fixture/build.json')
    assert fixture['executableSha256']==SHA(raw(H/'pending-status-fixture/fixture.exe'))
    assert fixture['sourceSha256']==SHA(raw(H/'pending-status-fixture/fixture.c'))
    for item in [negative,positive]:
        assert not item['error']and item['toolSha256']==manifest['tools/th14-pending-debug-status-component-nov05.py']['sha256']
        assert item['executableSha256']==fixture['executableSha256']and item['ownSourceOnly']and not item['originalProcessAccessed']
    assert negative['exitCode']==0x4000001e and negative['pendingOtherHardwareStatuses']==3 and negative['unknownOrLostStatusEvents']==4
    assert positive['exitCode']==0 and positive['all256MarkerEventsAccepted']and positive['hardwareEvents']==256
    assert positive['deferredUpdates']==sum(x['updateDeferred']for x in positive['crossThreadObservations'])==91
    assert all(x['knownMarkerAfterStore']and x['ownWatchBitSet']for x in positive['events'])
    for case in ['pending-status-negative','pending-status-positive']:
        failed=load(H/case/'report.json');assert failed['error'].startswith('AttributeError')and failed['hardwareEvents']==0
    failures=[]
    for case,expected_exceptions in [('preflight',0),('preflight-original-context',2)]:
        report=load(H/case/'native/report.json');end=load(H/case/'process-end.json')
        assert end['exitCode']==1 and report['callbacks']==0 and len(report['debugErrors'])==expected_exceptions
        assert not report['scriptRngAccessWatchArmed']
        failures.append(dict(case=case,callbacks=0,debugExceptions=expected_exceptions,accepted=False))
    preflight=load(H/'preflight-pending-status/verified.json')
    assert preflight['verifiedNativePreflight']and preflight['callbacks']==1200 and preflight['pendingDebugContextDeferrals']==0
    assert preflight['checkerSha256']==manifest['tools/th14-check-rng-register-preflight-nov05.py']['sha256']
    native_register=load(N.parent/'register-evidence.json')
    reader=module(R/'tools/th14-rng-register-trace-evidence-nov05.py','native_register_verifier')
    assert reader.verify(N)==native_register
    # The register verifier independently checks the terminated prefix, source
    # hashes, each decoded instruction and every same-thread arithmetic pair.
    for name,item in native_register['bindings'].items():
        value=raw(R/name);assert len(value)==item['bytes']and SHA(value)==item['sha256']
    assert native_register['accessEvents']==native_register['decodedRegisterValues']==64
    assert native_register['arithmeticPairsEqual']==32 and not native_register['globalSnapshotMismatchCounts']
    assert native_register['pendingContextUpdatesDeferred']==0
    # Re-run the existing independent32/camera25/HUD/VM303/combat verifier.
    # Cleanup is restricted to this invocation's newly created task directory.
    temp_parent=(H/'aggregate-rechecks').resolve();temp_parent.mkdir(exist_ok=True)
    assert temp_parent.is_relative_to(H.resolve())
    temporary=Path(tempfile.mkdtemp(prefix='raw-',dir=temp_parent)).resolve()
    assert temporary.is_relative_to(temp_parent)
    try:
        output=temporary/'raw.json'
        subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign.py'),
            '--native',str(N),'--model',str(M),'--build',str(H/'portable-audit-build/observer-build.json'),
            '--prefix','35000','--output',str(output)],cwd=R,check=True,capture_output=True)
        checked=json.loads(output.read_bytes());assert checked==load(F/'raw-verified.json')
    finally:
        assert temporary.resolve().is_relative_to(temp_parent)and temp_parent.is_relative_to(H.resolve())
        shutil.rmtree(temporary)
    for name,item in checked['bindings'].items():
        value=raw(R/name);assert len(value)==item['bytes']and SHA(value)==item['sha256']
    assert checked['callbacks']==35000 and checked['vm303Rows']==774 and checked['combatCheckpoints']==373
    assert checked['nonemptyCombatCheckpoints']==49
    model=load(M/'report.json');assert model['allRaw32ByteIdentical']and not model['differenceCounts']
    assert load(F/'process-end.json')['exitCode']==0
    driver=R/'tools/th14-compare-native-rng-register-audit-frame-anchor-nov05.mjs'
    assert model['comparisonToolSha256']==SHA(raw(driver))=='049fe6f33104256fe382ee14fc149f8954b4726784dd91cdc083826fb0830b9c'
    assert raw(N/'selected-state.u32')==raw(M/'selected-state.u32')
    camera=raw(N/'world-camera.raw');tail=raw(N/'world-camera-tail.u32');actual=raw(M/'full-camera.u32')
    assert len(actual)==34999*300
    for i in range(1,35000):assert actual[(i-1)*300:i*300]==camera[i*292:(i+1)*292]+tail[i*8:(i+1)*8]
    cursor=raw(N/'replay-cursor.u32');actual=raw(M/'replay-cursor.u32');assert len(actual)==34999*16
    for i in range(1,35000):assert struct.unpack_from('<4I',actual,(i-1)*16)==tuple(struct.unpack_from('<I',cursor,i*56+j*4)[0]for j in [3,7,8,9])
    assert raw(N/'hud-score.u32')==raw(M/'portable-hud.u32')
    audit=raw(M/'rng-register-audit.u32');rows=list(struct.iter_unpack('<16I',audit))
    assert len(rows)==68 and model['rngRegisterAudit']['meta']==[30759,30762,68,0,1]
    assert model['rngRegisterAudit']['outputSha256']==SHA(audit)
    # Select only the actual script-RNG identity. Flags4000 occur on live VMs
    # too and must never be used to remove these real records.
    script=[row for row in rows if row[3]==0]
    native_access=[json.loads(line)for line in raw(N/'script-rng-access-events.jsonl').splitlines()]
    assert len(script)==68 and len(native_access)==64
    for actual,original in zip(script,native_access):
        kind=original['instructionContract']['kind'];assert kind in ['mix32','store32']
        expected=(original['precedingPlayerCallbacks'],1 if kind=='mix32'else 4,
                  original['valueRetainedByTrappedInstruction'],struct.unpack_from('<I',bytes.fromhex(original['rngHexAtObservation']),4)[0])
        assert (actual[0],actual[2],actual[4],actual[5])==expected
    comparison=load(F/'register-comparison-verified.json')
    assert comparison['nativeInstructionAccesses']==comparison['portableInstructionAccessesCompared']==64
    assert comparison['extraPortableWindowRowsNotCompared']==4 and not comparison['vmFlags4000UsedAsFilter']
    controls=load(H/'portable-audit-preflight-controls/verified.json')
    assert controls['sameBinaryAuditEnabledAndDisabledPayloadsEqual']and len(controls['payloads'])==9
    for item in controls['payloads']:
        name=item['name'];a=raw(H/'portable-audit-preflight-controls/disabled/model'/name)
        assert a==raw(H/'portable-audit-preflight-controls/enabled/model'/name)==raw(H/'preflight-pending-status/comparison/model'/name)
        assert SHA(a)==item['sha256']and len(a)==item['bytes']
    rejected_filter=load(M/'rng-instruction-comparison-private.json')
    assert rejected_filter['portableMainScriptRows']==0 and rejected_filter['nativeRows']==64
    assert not rejected_filter['differences'] # Zero pairs is explicitly NOT a passed comparison.
    build=load(H/'portable-audit-build/observer-build.json')
    assert build['engineObjectsReusedForThisLink']==141 and build['engineSourcesRecompiledForThisLink']==0
    assert build['wasmSha256']==SHA(raw(H/'portable-audit-build/observer.wasm'))==model['wasmSha256']
    assert raw(H/'portable-audit-build/fixture-source.cpp')==raw(R/'runtimes/th12/th12_web/tests/cpp/th14-script-rng-register-audit-fixture-nov05.cpp')
    assert load(H/'portable-audit-native-prefix/process-end.json')['exitCode']==1
    raw(H/'portable-audit-native-prefix/process.log')
    assert load(H/'portable-audit-native-prefix-v2/process-end.json')['exitCode']==1
    failure=load(H/'portable-audit-native-prefix-v2-failure-state/model/tick-failure.json')
    assert load(H/'portable-audit-native-prefix-v2-failure-state/process-end.json')['exitCode']==1
    state=next(x['state']for x in failure['firstReadStates']if x['stage']==3)
    assert failure['requestedPlayer']==30760 and state[2:4]==[0,1]
    overshoot=(state[8]|state[9]<<32)-(state[10]|state[11]<<32);assert overshoot==702566500
    windows=model['firstScriptReadWindows'];anchors=model['inferredFrameEntryClocks']
    assert len(windows)==len(anchors)==1
    assert windows[0]['inferredClockLowerAnchor']and windows[0]['nativeRegisterValuesOnlyClassifyReadGeneration']
    assert windows[0]['nativeRegisterGenerationProofSha256']==SHA(raw(N.parent/'register-evidence.json'))
    assert anchors[0]['player']==30760 and anchors[0]['lowerSource']=='precedingPlayerReceipt'
    assert not anchors[0]['mainPumpEventInvented']and not anchors[0]['exactOriginalFrameEntryRecovered']
    assert not model['ordinaryIndependentThreadTimingAcceptance']and not model['completeGame']
    strict=load(H/'strict-v3/report.json')
    assert [(x['gate'],x['passed'])for x in strict['results']]==[('exceptions',True),('initialize',True),('scene',False)]
    assert not strict['overallStrictAccepted']and not strict['strictWhitelistModified']
    for item in strict['results']:
        assert SHA(raw(R/item['tool']))==item['verifierSha256']
        assert SHA(raw(H/'strict-v3'/(item['gate']+'.log')))==item['logSha256']
    for name,digest in {
        'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp':'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45',
        'artifacts/th14/vm-return-worker-oct29/work-state.json':'2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}.items():assert SHA(raw(R/name))==digest
    return dict(schema='th14/normal-rng-register-read/1',verifiedFiniteReadOrderEvidence=True,selection=[0,1,1,1],
        callbacks=35000,nativeDebugExceptions=0,nativeInstructionAccesses=64,nativeReadStorePairs=32,
        portableInstructionValuesEqual=64,sampledCounterWordsEqual=True,callbackAndPointOrderEqual=True,
        portableAuditRows=68,extraPortableRowsNotCompared=4,flags4000NotUsedToFilter=True,
        allState32Equal=True,all75CameraWordsEqual=True,comparedCameraWords=2624925,firstComparedCameraCallback=2,
        allCursor4Equal=True,firstComparedCursorCallback=2,allHud2Equal=True,vm303Rows=774,
        combatCheckpoints=373,nonemptyCombatCheckpoints=49,initialPublications=checked['orderedPublications'],
        sameBinaryAuditControlPayloadsEqual=9,preflightCallbacks=1200,preflightVm303Rows=230,
        syntheticRegisterRecoveryCases=210,syntheticLaterGlobalSnapshotWrong=189,
        ownPendingStatusNegativeUnidentifiedExceptionObservations=4,ownPendingStatusPositiveEvents=256,ownPendingStatusPositiveDeferrals=91,
        originalPendingDeferralBranchHits=0,originalStartupCauseProven=False,failedNativePreflights=failures,
        diagnosticClockOvershootNs=overshoot,inferredFrameEntryAnchors=anchors,
        originalValuesProvidedToEngine=False,nativeReadGenerationConstrainsInferredSchedule=True,
        exactOriginalFrameEntryRecovered=False,ordinaryIndependentTimingAccepted=False,
        diagnosticPrefixOnly=True,naturalReplayEndAccepted=False,productionGameplayChanged=False,
        oldDefaultFailureClosed=False,browserAcceptance=False,wholeOriginalFramebufferOrPcmAccepted=False,
        strictInitializeAccepted=True,strictSceneAccepted=False,strictWhitelistModified=False,
        limits=['Only a35000-callback prefix and64 seed read/store values of next32, with four additional portable rows unobserved.',
            'Counter words are observed memory samples; they are not claimed to be additional values decoded from the stopped instruction.',
            'Native register generation constrains an explicit inferred frame-entry clock; it does not recover exact independent scheduling.',
            'The pending-status mechanism is exercised by an owned fixture; the successful original runs had zero deferred updates.',
            'Earlier startup failures, original normal default-clock failures and the rejected unanchored comparison remain separate.',
            'No whole objects, full mode matrix, ordinary original GUI, browser persistence or full GPU/PCM acceptance.'],
        completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'docs/porting')or out.is_relative_to(R/'artifacts/th14')
    value=verify()
    if a.check:assert json.loads(out.read_bytes())==value
    else:
        assert not out.exists();out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:value[k]for k in ['verifiedFiniteReadOrderEvidence','callbacks','portableInstructionValuesEqual','comparedCameraWords','vm303Rows','combatCheckpoints','ordinaryIndependentTimingAccepted']}))
