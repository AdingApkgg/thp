"""Publish finite Supervisor/pump counts and hashes; retain raw data locally."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/supervisor-pass-rng-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def bind(path):
    path=path.resolve();assert path.is_relative_to(R)
    raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
def read(path):return json.loads(bind(path))
def verify_bindings(rows):
    for name,row in rows.items():
        raw=bind(R/name);assert len(raw)==row['bytes'] and SHA(raw)==row['sha256'],name
enabled=H/'comparison-pump-enabled';disabled=H/'comparison-pump-disabled'
proof=read(enabled/'native-register-proof.json');timeline=read(enabled/'native-register-proof-timeline.json')
raw=read(enabled/'raw-verified.json');result=read(enabled/'comparison-result.json');model=read(enabled/'model/report.json')
camera=read(enabled/'model/full-camera-report.json');build=read(H/'resource-clock-build-retry1/observer-build.json')
failure=read(disabled/'model/checkpoint-failure.json');old_failure=read(H/'comparison-prefix-v5/model/checkpoint-failure.json')
verify_bindings(proof['bindings']);verify_bindings(timeline['evidenceBindings']);verify_bindings(raw['bindings'])
assert proof['verifiedFiniteOriginalRegisterReadEvidence'] and proof['instructionAccesses']==64 and proof['pairedNext32ReadsAndStores']==32
assert proof['allNewSupervisorExceptionsHaveMatchingHardwareStatus'] and proof['nativeDebugExceptions']==0
assert timeline['entries']==timeline['pumps']==timeline['players']==34000 and timeline['passShapes']=={'pump1-player1':34000}
assert not timeline['physicalFrameIdentityProven'] and raw['callbacks']==35000
assert result['allExistingComparisonGatesPassed'] and result['all32StateFieldsEqual'] and result['matchedObservedInstructionSequence']
assert result['nativeInstructionAccesses']==64 and result['portableScriptRows']==68 and result['extraPortableRowsNotAccepted']==4
assert not any(result['instructionDifferenceCounts'].values())
assert raw['allVm303AndRegistryOrderEqual'] and raw['vm303Rows']==885 and raw['allCapturedCombatWordsEqual'] and raw['combatCheckpoints']==502
assert camera['allExpandedCapturedWordsEqual'] and camera['callbacksCompared']==34999 and camera['comparedFieldsPerCallback']==75
assert model['supervisorResourceClockMeta']==[34000,453,33547,0,0,35000] and not model['firstScriptReadWindows']
assert not model['sourceReadWindows'] and not model['sceneCopyWordHandoffs'] and not model['sceneUpdateHandoffs']
assert failure['callback']==old_failure['callback']==31009 and failure['native']==old_failure['native'] and failure['portable']==old_failure['portable']
assert failure['native']['stageFrame']==1 and failure['portable']['stageFrame']==0 and failure['stateDifferenceCountsBeforeThisCheckpoint']=={'21':171}
negative_hash=SHA(bind(disabled/'model/rng-register-audit-at-failure.u32'))
assert negative_hash==SHA(bind(H/'comparison-prefix-v5/model/rng-register-audit-at-failure.u32'))
assert failure['supervisorResourceClockMeta']==[0]*6 and failure['comparisonGateUnchanged']
assert build['engineSourcesRecompiledForThisLink']==1 and build['engineObjectsReusedForThisLink']==140 and not build['rootProductionSourcesModified']
assert SHA(bind(H/'resource-clock-build-retry1/observer.wasm'))==model['wasmSha256']==build['wasmSha256']
preflight=read(H/'preflight-fixed/verified.json');component=read(R/'artifacts/th14/frame-entry-audit-retry1-nov05/component/stable/report.json')
assert component['passed'] and component['counts']==dict(entry=256,pump=256,player=224,store=224)
failed=read(H/'prefix-fixed/native/report.json');failed_end=read(H/'prefix-fixed/process-end.json')
assert failed['callbacks']==0 and not failed['debugErrors'] and failed_end['exitCode']!=0
for name in ['tools/th14-inspect-supervisor-entry-nov05.py','tools/th14-fixed-frame-watch-component-nov05.py',
 'tools/th14-prepare-supervisor-rng-observer-nov05.py','tools/th14-run-supervisor-rng-observer-nov05.py',
 'tools/th14-check-supervisor-rng-preflight-nov05.py','tools/th14-supervisor-pass-timeline-nov05.py',
 'tools/th14-supervisor-rng-read-evidence-nov05.py','tools/th14-build-supervisor-resource-clock-nov05.py',
 'tools/th14-prepare-supervisor-comparison-nov05.py','tools/th14-compare-supervisor-prefix-nov05.py',
 'runtimes/th12/th12_web/tests/cpp/th14-supervisor-resource-clock-fixture-nov05.cpp']:
    bind(R/name)
out=dict(schema='th14/supervisor-pump-public-evidence/1',callbacks=35000,stagesObserved=raw['stagesObserved'],selection=[0,1,1,1],
    native=dict(debugExceptions=0,observedPasses=34000,entries=34000,pumps=34000,players=34000,
        entryPc='0x444890',pumpPc='0x47d720',playerPc='0x44dbd0',fixedHardwareSlots=True,multiplexing=False,
        sameMainThreadPassAssociationObserved=True,allNewEntryExceptionsHardwareValidated=True,physicalFrameIdentityProven=False,
        instructionAccesses=64,pairedNext32ReadsAndStores=32),
    enabled=dict(allExistingComparisonGatesPassed=True,all32StateFieldsEqual=True,all75CameraFieldsEqual=True,
        expandedCameraCallbacks=34999,expandedCameraWords=34999*75,allHudAndCursorEqual=True,orderedPublications=raw['orderedPublications'],
        vm303Rows=885,combatCheckpoints=502,nonemptyCombatCheckpoints=raw['nonemptyCombatCheckpoints'],combatRows=raw['combatRows'],
        nativeInstructionAccesses=64,matchedObservedInstructionSequence=True,portableScriptRows=68,extraPortableRowsNotAccepted=4,
        instructionDifferenceCounts=result['instructionDifferenceCounts'],scheduledPumpClocks=34000,deliveredAtPendingLoaderPump=453,
        noPendingLoaderAtCallSite=33547,clockDeliveryFailures=0,firstReadWaitInstalled=False,sceneCopyHandoffsInstalled=False),
    disabled=dict(failureCallback=31009,nativeStage=3,nativeStageFrame=1,portableStageFrame=0,
        scriptSeedDifferenceCallbacksBeforeFailure=171,rngAuditPayloadIdenticalToOldNegative=True,rngAuditPayloadSha256=negative_hash),
    build=dict(wasmSha256=build['wasmSha256'],engineObjectsRecompiled=1,engineObjectsReused=140,
        diagnosticGameSessionOnly=True,productionGameplayChanged=False),
    ownConcurrentWatchComponent=dict(counts=component['counts'],omittedPlayerPassesStillObserved=32,passed=True),
    failedStartupRetained=dict(callbacks=0,newWatchProfileActivated=False,startupTimeoutSeconds=90,causeProven=False),
    timestampsAreDebuggerReceiptTimes=True,crossThreadExactOrderAccepted=False,originalStateValuesProvidedToEngine=False,
    allFinalComparisonGatesUnchanged=True,strictSceneWhitelistChanged=False,oldDefaultFailureClosed=False,
    ordinaryIndependentTimingAccepted=False,originalWholePixelsOrPcmAccepted=False,completeGame=False,
    assetsRawRegistersSeedsMemorySavesReplaysImagesPcmAndBinariesIncluded=False,sourceSummaryBindings=bindings,
    toolSha256=SHA(Path(__file__).read_bytes()))
target=R/'docs/porting/th14-supervisor-pump-clock-nov05.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,path=target.relative_to(R).as_posix(),bytes=target.stat().st_size,callbacks=35000,completeGame=False)))
