"""Verify event-ordinal diagnostics while preserving the twelve coarse failures."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode-perspective-window-diagnostic-nov04'
BASE=R/'artifacts/th14/unified-event-context-trace-nov04'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def verify():
 bindings={}
 def raw(path):
  data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def load(path):return json.loads(raw(path))
 def rows(path):return [json.loads(line)for line in raw(path).splitlines()]
 assert sys.byteorder=='little'
 base_proof=load(BASE/'expanded-modes-verified.json');assert base_proof['expandedFailures']==12 and base_proof['expandedPasses']==4
 assert base_proof['verifierSha256']==SHA(raw(R/'tools/th14-full-camera-mode-evidence-nov04.py'))
 for name,binding in base_proof['bindings'].items():
  data=raw(R/name);assert len(data)==binding['bytes'] and SHA(data)==binding['sha256']
 plan=load(H/'cases/plan.json');end=load(H/'cases/end.json');assert end['casesCompleted']==12 and end['diagnosticOnly'] and not end['legacyDefaultFailuresClosed']
 assert plan['basePlanSha256']==SHA(raw(BASE/'expanded-mode-regressions/plan.json')) and plan['baseEndSha256']==SHA(raw(BASE/'expanded-mode-regressions/end.json'))
 generator=R/'tools/th14-prepare-mode-perspective-window-driver-nov04.py';raw(generator)
 spec=importlib.util.spec_from_file_location('mode_driver',generator);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 driver=raw(R/'tools/th14-compare-native-mode-perspective-window-nov04.mjs');assert driver==module.driver_source() and SHA(driver)==plan['driverSha256']
 build_path=H/'build/observer-build.json';build=load(build_path);assert SHA(raw(build_path))==plan['buildSha256']
 assert build['hostClockOverridesAdded'] and not build['readOnlyObserver'] and build['engineObjectsReusedForThisLink']==141 and build['engineSourcesRecompiledForThisLink']==0
 assert SHA(raw(build_path.parent/'observer.wasm'))==build['wasmSha256']
 for item in build['objectBindings']:assert SHA(raw(Path(item['path'])))==item['sha256']
 for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
 raw(R/'tools/th14-build-mode-perspective-window-nov04.py');raw(R/'runtimes/th12/th12_web/tests/cpp/th14-mode-perspective-window-fixture-nov04.cpp');raw(H/'run-diagnostics.py')
 indices=[i for i in range(73)if i not in(22,23)];cases=[];total_callbacks=0;total_words=0;total_windows=0
 for case,done in zip(plan['cases'],end['cases']):
  key=case['key'];assert key==done['key'] and done['guardStop']is None
  native=R/case['native'];home=H/'cases'/key/'model';coarse=BASE/'expanded-mode-regressions'/key/'model'
  report=load(home/'report.json');old=load(coarse/'report.json');nr=load(native/'report.json')
  assert not nr['debugErrors'] and report['wasmSha256']==build['wasmSha256'] and report['comparisonToolSha256']==SHA(driver)
  assert report['observedPhaseInputs']==old['observedPhaseInputs']
  assert report['allRaw32ByteIdentical'] and raw(home/'selected-state.u32')==raw(native/'selected-state.u32')
  assert report['legacyWindowDiagnosticOnly'] and not report['strictSceneContractAccepted'] and not report['exactOriginalInstructionScheduleRecovered'] and not report['ordinaryIndependentThreadTimingAcceptance']
  names=['selected-state.u32','portable-camera.u32','portable-hud.u32','combat-snapshots.json']
  names+=sorted(p.name for p in home.glob('portable-live-*.json'));names+=sorted(p.name for p in home.glob('portable-allocations-*.json'))
  for name in names:assert raw(home/name)==raw(coarse/name),(key,name)
  copies=rows(native/'scene-camera-copy-events.jsonl');boundaries=rows(native/'camera-boundary-events.jsonl');expected=[]
  for event in copies:
   if event['event']!='scene-camera-copy-before' or event.get('mainPhaseAtObservation')!='draw':continue
   boundary=event.get('lastMainCameraBoundary')
   if not boundary or boundary['event']!='world-perspective-right-written':continue
   callback=event['precedingPlayerCallbacks'];frame=[x for x in boundaries if x['event']=='world-perspective-right-written' and x['precedingPlayerCallbacks']==callback]
   ordinal=next(i+1 for i,x in enumerate(frame)if x['hostMonotonicNs']==boundary['hostMonotonicNs'] and x['threadId']==boundary['threadId'] and x['pc']==boundary['pc'])
   if ordinal==len(frame):continue
   following=frame[ordinal];after=next(x for x in copies if x['stage']==event['stage'] and x['event']=='scene-camera-copy-after')
   assert boundary['pc']==0x4465a6 and event['pc']==0x40d435 and boundary['readOnly'] and event['readOnly']
   assert boundary['hostMonotonicNs']<event['hostMonotonicNs']<following['hostMonotonicNs']
   expected.append(dict(stage=event['stage'],callback=callback,ordinal=ordinal,readyNs=event['hostMonotonicNs'],previousNs=boundary['hostMonotonicNs'],followingNs=following['hostMonotonicNs'],copyAfterNs=after['hostMonotonicNs'],copyCompletedBeforeFollowing=after['hostMonotonicNs']<following['hostMonotonicNs'],fullSourceReadWitnessPresent=False,exactOriginalInstructionScheduleRecovered=False))
  assert expected==report['legacyPerspectiveWindows']==done['windows'] and expected
  assert report['legacyWindowStates']==done['states']
  for window,state in zip(expected,report['legacyWindowStates']):assert window['stage']==state['stage'] and state['delivered']==1 and state['failed']==0 and state['visits']>=window['ordinal']
  full=load(home/'full-camera-report.json');count=nr['callbacks'];portable_raw=raw(home/'full-camera.u32');portable=memoryview(portable_raw).cast('I');original=memoryview(raw(native/'world-camera.raw')).cast('I')
  assert count==done['callbacks']==report['callbacks'] and len(portable)==(count-1)*71 and len(original)==count*73 and full['nativeWordIndices']==indices
  assert SHA(portable_raw)==full['portableSha256']
  differences={};first=None
  for frame in range(1,count):
   for column,word in enumerate(indices):
    actual=portable[(frame-1)*71+column];value=original[frame*73+word]
    if actual!=value:
     differences[str(word)]=differences.get(str(word),0)+1
     if first is None:first=dict(callback=frame+1,nativeWord=word,actual=actual,expected=value)
  assert differences==full['counts']==done['counts'] and full['allExpandedCapturedWordsEqual']==done['expandedEqual']==(not differences)
  assert done['exitCode']==(0 if not differences else 1)
  words=(count-1)*71;total_callbacks+=count;total_words+=words;total_windows+=len(expected)
  cases.append(dict(key=key,callbacks=count,expandedWords=words,wrongWords=sum(differences.values()),first=first,windows=expected,unchangedLegacyPayloads=len(names)))
 rejection=load(H/'scene-rejection.json');assert rejection['expectedRejection'] and rejection['exitCode']!=0 and not rejection['whitelistChanged']
 assert SHA(raw(H/'scene-rejection.log'))==rejection['logSha256'] and rejection['verifierSha256']==SHA(raw(R/'tools/th14-verify-native-scene-boundaries-nov03.py'))
 assert not(H/'scene-rejection-output-must-not-exist.json').exists()
 assert not any(case['wrongWords']for case in cases) and end['expandedPasses']==12
 return dict(verifiedLegacyModeWindowDiagnostics=True,diagnosticRecords=12,callbacks=total_callbacks,expandedFields=71,expandedWords=total_words,wrongExpandedWords=0,windows=total_windows,cases=cases,
  legacyPayloadsByteIdentical=True,originalPhaseReadyTimestampsUnchanged=True,originalValuesProvidedToEngine=False,hostClockBoundaryReplayAdded=True,
  fullSourceReadWitnessPresent=False,exactOriginalInstructionScheduleRecovered=False,strictSceneContractRejectsDriver=True,
  coarseDefaultModePasses=4,coarseDefaultModeFailures=12,legacyDefaultFailuresClosed=False,independentSchedulingAccepted=False,
  productionCoreChanged=False,newOriginalProcessesLaunched=False,physicalAudioDevicesOpened=0,completeGame=False,nativeEquivalent=False,
  bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--check',type=Path);a=p.parse_args();assert bool(a.output)!=bool(a.check)
 result=verify()
 if a.output:
  out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode())
 else:assert json.loads(a.check.read_bytes())==result
 print(json.dumps({k:v for k,v in result.items()if k not in('bindings','cases')}))


if __name__=='__main__':main()
