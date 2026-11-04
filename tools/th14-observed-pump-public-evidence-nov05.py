"""Export finite counts and sealed evidence paths/hashes, never raw observations."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/script-rng-read-generation-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()
bindings={}
def read(path):
    raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return json.loads(raw)
rotating=read(H/'rotating-pump-summary-nov05.json');ready=read(H/'player-pump-ready-summary-nov05.json')
assert rotating['nativeCallbacks']==ready['callbacks']==35000
assert rotating['nativeDebugExceptions']==ready['nativeDebugExceptions']==0
assert rotating['comparison']['verifiedFiniteUnanchoredComparison']and ready['comparison']['verifiedFiniteUnanchoredComparison']
assert ready['timeline']['sameMainThreadInstructionOrderObserved']and not ready['timeline']['nativePhysicalFrameEntryRecovered']
assert ready['strictInitializeAccepted']and not ready['strictSceneAccepted']and not ready['strictWhitelistModified']
assert not ready['oldContentionTraceClosed']and not rotating['oldNormalDefaultFailureClosed']
for summary in [rotating,ready]:
    for name,row in summary.get('bindings',{}).items():
        path=(R/name).resolve();assert path.is_relative_to(R/'artifacts/th14')
        raw=path.read_bytes();assert len(raw)==row['bytes']and SHA(raw)==row['sha256'],name
        bindings[name]=row
out=dict(schema='th14/observed-pump-public-evidence/1',
    rotating=dict(callbacks=35000,debugExceptions=0,stage2Pumps=rotating['actualStage2PumpEvents'],stage3Pumps=rotating['actualStage3PumpEvents'],
        pairedVmEdges=rotating['actualStageVmCallPairs'],instructionAccesses=rotating['nativeRngInstructionAccesses'],comparison=rotating['comparison']),
    playerPump=dict(callbacks=35000,debugExceptions=0,muxEvents=ready['muxBoundaryEvents'],observerSha256=ready['observerSha256'],
        comparison=ready['comparison'],timeline=ready['timeline'],readyAtObservedPump=ready['readyAtObservedPump'],
        firstReadWaitInstalled=ready['firstReadWaitInstalled'],previousPlayerClockSubstituted=ready['previousPlayerClockSubstituted']),
    strictInitializeAccepted=True,strictSceneAccepted=False,strictWhitelistModified=False,oldDefaultFailureClosed=False,
    originalDispatchOrderAssumed=True,allPlayerOrPumpCallsProvenObserved=False,scenePublisherInterleavingStillInferred=True,
    originalStateValuesProvidedToEngine=False,ordinaryIndependentTimingAccepted=False,productionGameplayChanged=False,
    assetsRawRegistersSeedsMemoryReplaysAndBinariesIncluded=False,sourceSummaryBindings=bindings,
    toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False)
target=R/'docs/porting/th14-observed-pump-ready-nov05.json';target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,path=target.relative_to(R).as_posix(),bytes=target.stat().st_size,completeGame=False)))
