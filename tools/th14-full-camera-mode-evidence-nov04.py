"""Recompute expanded camera differences without broadening legacy mode acceptance."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
H=R/'artifacts/th14/unified-event-context-trace-nov04/expanded-mode-regressions'
OLD=R/'artifacts/th14/perspective-publication-nov04/current-modes'


def verify():
 bindings={}
 def raw(path):
  data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def load(path):return json.loads(raw(path))
 assert sys.byteorder=='little'
 plan=load(H/'plan.json');old_plan=raw(OLD/'plan.json');assert plan['previousPlanSha256']==SHA(old_plan)
 end=load(H/'end.json');old_end=load(OLD/'end.json');assert end['casesCompleted']==old_end['casesCompleted']==17
 assert old_end['strictV4Passes']==16 and not end['completeGame'] and not end['independentTimingAccepted']
 path=R/'tools/th14-prepare-full-camera-drivers-nov04.py';raw(path)
 spec=importlib.util.spec_from_file_location('drivers',path);drivers=importlib.util.module_from_spec(spec);spec.loader.exec_module(drivers)
 for extra,name in [(False,'th14-compare-native-full-camera-nov04.mjs'),(True,'th14-compare-native-extra-full-camera-nov04.mjs')]:
  assert raw(R/'tools'/name)==drivers.driver_source(extra)
 build_path=R/'artifacts/th14/full-camera-observer-nov04/build/observer-build.json';build=load(build_path)
 assert SHA(raw(build_path))==plan['buildSha256'] and build['readOnlyObserver'] and not build['hostClockOverridesAdded']
 assert SHA(raw(build_path.parent/'observer.wasm'))==build['wasmSha256'] and build['engineObjectsReusedForThisLink']==141
 for item in build['objectBindings']:assert SHA(raw(Path(item['path'])))==item['sha256']
 for path,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(path)))==digest
 raw(R/'tools/th14-full-camera-mode-regressions-nov04.py')
 raw(H.parent/'run-expanded-modes.py')
 indices=[i for i in range(73)if i not in(22,23)];cases=[];total=0;total_words=0
 for case,record,legacy in zip(plan['cases'],end['cases'],old_end['cases']):
  key=case['key'];assert key==record['key']==legacy['key']
  native=R/case['native'];native_report=load(native/'report.json');assert SHA(raw(native/'report.json'))==record['nativeReportSha256']
  if native_report['debugErrors']:
   assert key=='reimub-easy' and len(native_report['debugErrors'])==12 and record['notRun']
   cases.append(dict(key=key,rejectedNativeExceptions=12,newModelRun=False));continue
  assert legacy['strictV4Passed'] and record['guardStop'] is None
  home=H/key/'model';baseline=OLD/key/'model';report=load(home/'report.json')
  assert report['wasmSha256']==build['wasmSha256'] and report['comparisonToolSha256']==record['driverSha256']
  assert report['allRaw32ByteIdentical'] and report['readOnlyExpandedCameraObservation']
  assert not report.get('addedMeasuredHostClockBoundary')
  names=['selected-state.u32','portable-camera.u32','portable-hud.u32','combat-snapshots.json']
  names += sorted(path.name for path in home.glob('portable-live-*.json'))
  names += sorted(path.name for path in home.glob('portable-allocations-*.json'))
  assert len(names)>=6
  for name in names:assert raw(home/name)==raw(baseline/name),(key,name)
  declared=load(home/'full-camera-report.json');assert declared['nativeWordIndices']==indices and not declared['hostClockOverridesAdded']
  count=native_report['callbacks'];assert count==record['callbacks']==report['callbacks'] and declared['callbacksCompared']==count-1
  portable_raw=raw(home/'full-camera.u32');assert SHA(portable_raw)==declared['portableSha256']
  portable=memoryview(portable_raw).cast('I');expected=memoryview(raw(native/'world-camera.raw')).cast('I')
  assert len(portable)==(count-1)*71 and len(expected)==count*73
  differences={};first=None
  for frame in range(1,count):
   for column,word in enumerate(indices):
    actual=portable[(frame-1)*71+column];value=expected[frame*73+word]
    if actual!=value:
     differences[str(word)]=differences.get(str(word),0)+1
     if first is None:first=dict(callback=frame+1,nativeWord=word,actual=actual,expected=value)
  assert differences==declared['counts']==record['counts']
  equal=not differences;assert declared['allExpandedCapturedWordsEqual']==record['expandedEqual']==equal
  assert record['exitCode']==(0 if equal else 1)
  if first:assert declared['first'][0]==first==record['first'][0]
  words=(count-1)*71;total+=count;total_words+=words
  cases.append(dict(key=key,callbacks=count,expandedWords=words,expandedPassed=equal,wrongWords=sum(differences.values()),counts=differences,first=first,unchangedLegacyPayloads=len(names)))
 assert total==1379760 and len([x for x in cases if x.get('newModelRun') is not False])==16
 passes=sum(x.get('expandedPassed',False)for x in cases);assert passes==end['expandedPasses']
 return dict(verifiedExpandedCameraModeAudit=True,validRecords=16,rejectedNativeRecords=1,rejectedNativeExceptions=12,callbacks=total,
  expandedFields=71,expandedWords=total_words,expandedPasses=passes,expandedFailures=16-passes,cases=cases,
  legacyPayloadsByteIdentical=True,legacy16PassesDoNotAcceptExpandedFields=True,hostClockOverridesAdded=False,
  productionCoreChanged=False,independentSchedulingAccepted=False,oldRecordingFailureClosed=False,
  opaqueNativeWordsNotMapped=[22,23],nativeTailWordsNotCaptured=[73,74],completeGame=False,nativeEquivalent=False,
  bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--check',type=Path);a=p.parse_args();assert bool(a.output)!=bool(a.check)
 result=verify()
 if a.output:
  out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode())
 else:assert json.loads(a.check.read_bytes())==result
 print(json.dumps({k:v for k,v in result.items()if k not in('bindings','cases')}))


if __name__=='__main__':main()
