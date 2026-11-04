"""Recompute controlled RNG/perspective diagnostics; do not accept original timing."""
from pathlib import Path
import argparse,array,hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/perspective-publication-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();bindings={}
 def raw(path):
  b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def load(path):return json.loads(raw(path))
 core=load(H/'build/ordinary/observer-build.json')
 def build(directory):
  br=load(H/directory/'observer-build.json');assert br['objectBindings']==core['objectBindings']and br['sourceHashes']==core['sourceHashes']and br['headerHashes']==core['headerHashes']
  assert br['controlledTimingExperimentOnly']and br['hostClockOverridesAdded']and not br['originalScheduleRecovered']
  assert SHA(raw(H/directory/'observer.wasm'))==br['wasmSha256']
  assert br['buildToolSha256']==SHA(raw(R/'tools'/('th14-build-rng-perspective-clock-experiment-nov04.py'if directory=='clock-component'else'th14-build-rng-perspective-full-camera-nov04.py')))
  for path,digest in br['fixtureDependencyHashes'].items():assert SHA(raw(Path(path)))==digest
  return br
 cb=build('clock-component');fb=build('full-camera-component-v2')
 for obj in core['objectBindings']:assert SHA(raw(Path(obj['path'])))==obj['sha256']
 raw(R/'tools/th14-rng-perspective-clock-experiment-nov04.mjs');raw(R/'tools/th14-rng-perspective-full-camera-nov04.mjs')
 old=H/'old-rng-comparison/model';baseline=H/'clock-experiments/unchanged-clocks/model';names=['selected-state.u32','portable-camera.u32','portable-hud.u32',*[f'portable-live-{n}.json'for n in(1,26000,30000,33000)]]
 for name in names:assert raw(old/name)==raw(baseline/name)
 controls=[]
 for point in [3,4,5]:
  home=H/f'clock-experiments/perspective-{point}';report=load(home/'model/report.json');camera=load(home/'model/camera-report.json');end=load(home/'model-end.json')
  rng=load(home/'model/stage-rng-clock.json');persp=load(home/'model/perspective-clock.json')
  assert rng['values'][:5]==[30837,8,0,1,0]and persp['values'][:4]==[14182,point,1,0]
  assert report['controlledStageRngClockExperiment']and report['controlledPerspectiveClockExperiment']and not report['originalScheduleRecovered']
  assert report['differenceCounts']=={}and load(home/'model/live-report.json')['allLiveValuesEqual']
  assert report['wasmSha256']==cb['wasmSha256']and end['guardStop']is None
  if point<5:assert camera['counts']=={'12':16701}and end['exitCode']==1;controls.append(dict(point=point,retainedCameraDifferences=16701))
  else:assert camera['counts']=={}and end['exitCode']==0
 end=load(H/'clock-experiments/end.json');assert len(end['cases'])==4 and not end['originalScheduleRecovered']
 rejection=load(H/'clock-experiments/strict-scene-contract-control.json');assert rejection['expectedRejection']and rejection['strictGateNotWeakened'];log=raw(H/'clock-experiments/strict-scene-contract-control.log');assert b'Unreviewed Scene scheduler driver'in log
 raw(R/'tools/th14-verify-native-scene-boundaries-nov03.py')
 positive=[]
 for directory,b in [('clock-experiments/perspective-5',cb),('full-camera-experiment/perspective-5',fb)]:
  home=H/directory;proof=load(home/'raw-payload-verified.json');assert proof['verifiedFiniteEvidence']and proof['callbacks']==35000 and proof['wasmSha256']==b['wasmSha256']and proof['combatCheckpoints']==480 and len(proof['vm303Snapshots'])==4
  for path,binding in proof['bindings'].items():
   data=raw(R/path);assert len(data)==binding['bytes']and SHA(data)==binding['sha256']
  assert load(home/'model-end.json')['exitCode']==load(home/'raw-verifier-end.json')['exitCode']==0
  positive.append(dict(case=directory,callbacks=35000,vm303Rows=proof['vm303Rows'],combatCheckpoints=480))
 full=H/'full-camera-experiment/perspective-5/model';expanded=load(full/'full-camera-report.json');indices=[i for i in range(73)if i not in (22,23)]
 assert expanded['nativeWordIndices']==indices and expanded['callbacksCompared']==34999 and expanded['allExpandedCapturedWordsEqual']and expanded['counts']=={}
 original=raw(R/'artifacts/th14/replay-rng-template-trace-nov04/native/world-camera.raw');assert len(original)==35000*292
 expected=array.array('I',(struct.unpack_from('<I',original,callback*292+word*4)[0]for callback in range(1,35000)for word in indices))
 assert expected.tobytes()==raw(full/'full-camera.u32')and SHA(expected.tobytes())==expanded['portableSha256']
 result=dict(verifiedControlledCombinedClockExperiment=True,productionCoreWasmSha256=core['wasmSha256'],engineSourcesChangedForExperiment=0,engineObjectsReused=141,baselineSevenPayloadsByteIdentical=True,matchingRawPayloadCases=positive,negativePerspectiveControls=controls,expandedCameraFields=71,expandedCameraCallbacks=34999,expandedCameraWords=34999*71,allExpandedCapturedCameraWordsEqual=True,excludedOpaqueNativeWords=[22,23],uncapturedNativeTrailingWords=[73,74],hostClocksExplicitlyOverridden=True,originalStateValuesProvidedToEngine=False,actualOriginalAnimationIdentityObserved=False,originalScheduleRecovered=False,strictSceneContractRejectedControlledDriver=True,strictNativeCampaignAccepted=False,defaultOriginalRngFailureClosed=False,defaultOriginalCameraFailureClosed=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
