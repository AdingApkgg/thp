"""Verify controlled Stage-clock diagnostics without accepting an original schedule."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/stage-rng-clock-experiment-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();bindings={}
 def raw(path):
  b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def load(path):return json.loads(raw(path))
 build=load(H/'build-v3/observer-build.json');core=load(R/'artifacts/th14/camera-native-order-nov04/build/ordinary/observer-build.json')
 assert build['objectBindings']==core['objectBindings']and build['sourceHashes']==core['sourceHashes']and build['headerHashes']==core['headerHashes']
 assert build['controlledTimingExperimentOnly']and build['hostClockOverridesAdded']and not build['originalScheduleRecovered']
 assert SHA(raw(H/'build-v3/observer.wasm'))==build['wasmSha256']
 assert build['buildToolSha256']==SHA(raw(R/'tools/th14-build-stage-rng-clock-experiment-nov04.py'))
 for row in core['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
 for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
 raw(R/'tools/th14-stage-rng-clock-experiment-nov04.mjs');raw(H/'end.json');raw(H/'round2/end.json')
 baseline=R/'artifacts/th14/camera-native-order-nov04/old-rng-comparison/model'
 payloads=['selected-state.u32','portable-camera.u32','portable-hud.u32',*[f'portable-live-{n}.json'for n in(1,26000,30000,33000)]]
 for name in payloads:assert raw(baseline/name)==raw(H/'unchanged-clock/model'/name)
 N=R/'artifacts/th14/replay-rng-template-trace-nov04/native'
 stores=[json.loads(x)for x in raw(N/'replay-rng-store-events.jsonl').splitlines()]
 transition=[json.loads(x)for x in raw(N/'transition-events.jsonl').splitlines()]
 early=next(x for x in stores if x['stage']==3 and x['pc']==0x456133);late=next(x for x in transition if x['stage']==3 and x['event']=='replay-seeds-restored-before-globals-copy')
 assert late['hostMonotonicNs']-early['hostMonotonicNs']==724700
 assert early['workerInstructionStillPending']and early['precedingPlayerCallbacks']==late['precedingPlayerCallbacks']==30837
 base_camera=raw(baseline/'portable-camera.u32');accepted=[];controls=[]
 for round_name,indices in [('',[7,8,9]),('round2',[7,8,9])]:
  for index in indices:
   case=H/round_name/f'before-animation-{index}';end=load(case/'model-end.json');report=load(case/'model/report.json');state=load(case/'model/stage-rng-clock.json');v=state['values']
   assert end['exitCode']==1 and end['guardStop']is None and report['controlledStageRngClockExperiment']and not report['originalScheduleRecovered']
   assert v[:5]==[30837,index,0,1,0]and v[7]==2 and state['input']['diagnosticOnly']and not state['input']['observedOriginalIdentityClaimed']
   camera=load(case/'model/camera-report.json');assert camera['counts']=={'12':16701}and camera['first']['12']['index']==14315
   assert raw(case/'model/portable-camera.u32')==base_camera
   if round_name=='':
    assert state['input']['hostMonotonicNs']==early['hostMonotonicNs']and report['differenceCounts']=={'21':4137,'22':283,'26':1}
    controls.append(dict(round='earlier-than-gate',animation=index,differences=report['differenceCounts']))
   elif index==9:
    assert report['differenceCounts']=={'21':4163,'22':304,'26':2};controls.append(dict(round='at-gate',animation=index,differences=report['differenceCounts']))
   else:
    assert state['input']['hostMonotonicNs']==late['hostMonotonicNs']and report['allRaw32ByteIdentical']and report['differenceCounts']=={}
    original=raw(N/'selected-state.u32');assert raw(case/'model/selected-state.u32')==original[:35000*128]
    hud=load(case/'model/hud-report.json');live=load(case/'model/live-report.json');combat=load(case/'model/combat-snapshots.json')
    assert hud['allHudWordsEqual']and live['allLiveValuesEqual']and all(x['differenceCount']==0 for x in live['snapshots'])
    assert combat['allCapturedCombatWordsEqual']and not combat['differences']and len(combat['snapshots'])==480
    for name in payloads:raw(case/'model'/name)
    accepted.append(dict(animation=index,object=v[5],primitive=v[6],selected32WordsEqual=True,vm303Snapshots=len(live['snapshots']),combatCheckpoints=480))
 result=dict(verifiedControlledStageClockExperiment=True,coreWasmSha256=core['wasmSha256'],fixtureWasmSha256=build['wasmSha256'],engineObjectsReused=141,engineSourcesChanged=0,baselineSevenPayloadsByteIdentical=True,callbacks=35000,experimentalMatchingCases=accepted,negativeTimingControls=controls,earlierLogTimestampDiffersFromInitializeGateNs=724700,remainingCameraDifferences=16701,remainingCameraFirstCallback=14315,physicalAudioDevicesOpened=0,nativeGameStateValuesProvidedToEngine=False,hostClockExplicitlyOverridden=True,actualOriginalAnimationIdentityObserved=False,originalScheduleRecovered=False,strictNativeCampaignAccepted=False,oldFailureClosed=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
