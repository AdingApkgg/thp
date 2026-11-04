"""Independently check the new camera coverage failure and measured-window replay.

This is finite, instrumented host-boundary evidence, not acceptance of independent
thread scheduling or the unresolved older recording.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, struct, sys

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/unified-event-context-trace-nov04'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def verify():
 bindings={}
 def raw(path):
  data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def load(path):return json.loads(raw(path))
 def rows(path):return [json.loads(line) for line in raw(path).splitlines()]
 def generator(name):
  path=R/'tools'/name;raw(path)
  spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
 assert sys.byteorder=='little'
 native=H/'native';baseline=H/'comparison-current/model';coarse=H/'comparison-full-camera/model';fine=H/'comparison-perspective-window/model'
 clock=load(H/'verified.json');assert clock['verifiedUnifiedOriginalDebugEventClock'] and clock['callbacks']==35000
 for name,binding in clock['bindings'].items():
  data=raw(R/name);assert len(data)==binding['bytes'] and SHA(data)==binding['sha256']
 assert load(H/'comparison-full-camera/end.json')['exitCode']==1
 assert load(H/'comparison-perspective-window/end.json')['exitCode']==0
 plain_generator=generator('th14-prepare-full-camera-drivers-nov04.py')
 window_generator=generator('th14-prepare-observed-perspective-window-driver-nov04.py')
 plain_driver=raw(R/'tools/th14-compare-native-full-camera-nov04.mjs')
 window_driver=raw(R/'tools/th14-compare-native-observed-perspective-window-nov04.mjs')
 assert plain_driver==plain_generator.driver_source() and window_driver==window_generator.driver_source()
 for extra,name in [(False,'th14-compare-native-campaign-retained-camera-nov01.mjs'),(True,'th14-compare-native-extra-campaign-nov01.mjs')]:
  assert SHA(raw(R/'tools'/name))==plain_generator.PARENTS[name]
  if extra:assert raw(R/'tools/th14-compare-native-extra-full-camera-nov04.mjs')==plain_generator.driver_source(True)
 for directory,build_path,driver in [(coarse,R/'artifacts/th14/full-camera-observer-nov04/build/observer-build.json',plain_driver),(fine,H/'perspective-window-build/observer-build.json',window_driver)]:
  build=load(build_path);assert SHA(raw(build_path.parent/'observer.wasm'))==build['wasmSha256']
  report=load(directory/'report.json');assert report['comparisonToolSha256']==SHA(driver) and report['wasmSha256']==build['wasmSha256']
  assert build['engineObjectsReusedForThisLink']==141 and build['engineSourcesRecompiledForThisLink']==0
  for item in build['objectBindings']:assert SHA(raw(Path(item['path'])))==item['sha256']
  for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
  assert SHA(raw(Path(build['fixtureGraphRoot'])))==build['expandedFixtureSha256']
  assert report['allRaw32ByteIdentical'] and not report['completeGame'] and not report['nativeEquivalent']
  for name in ['selected-state.u32','portable-camera.u32','portable-hud.u32','portable-live-1.json','portable-live-26000.json','portable-live-30000.json','portable-live-33000.json']:
   assert raw(directory/name)==raw(baseline/name),name
 source=raw(R/'runtimes/th12/th12_web/tests/cpp/th14-full-camera-observer-fixture-nov04.cpp')
 assert b'#include "th14-initialization-clock-fixture-nov01.cpp"' in source
 assert b'probe_clock_ns=' not in source and b'probe_clock_ns =' not in source
 raw(R/'runtimes/th12/th12_web/tests/cpp/th14-observed-perspective-window-fixture-nov04.cpp')
 for name in ['th14-build-full-camera-observer-nov04.py','th14-build-observed-perspective-window-nov04.py']:raw(R/'tools'/name)
 native_words=memoryview(raw(native/'world-camera.raw')).cast('I');assert len(native_words)==35000*73
 indices=[i for i in range(73) if i not in (22,23)];recomputed=[]
 for directory in (coarse,fine):
  words=memoryview(raw(directory/'full-camera.u32')).cast('I');assert len(words)==34999*71
  counts={};first=None
  for frame in range(1,35000):
   for column,index in enumerate(indices):
    value=words[(frame-1)*71+column];expected=native_words[frame*73+index]
    if value!=expected:
     counts[str(index)]=counts.get(str(index),0)+1
     if first is None:first=dict(callback=frame+1,nativeWord=index,actual=value,expected=expected)
  declared=load(directory/'full-camera-report.json');assert declared['nativeWordIndices']==indices and declared['counts']==counts
  assert declared['portableSha256']==SHA(raw(directory/'full-camera.u32'))
  assert declared['allExpandedCapturedWordsEqual']==(not counts)
  recomputed.append(dict(counts=counts,wrongWords=sum(counts.values()),first=first))
 assert recomputed[0]['wrongWords']==41010 and recomputed[0]['first']['callback']==30900 and not recomputed[1]['counts']
 copies=rows(native/'scene-camera-copy-events.jsonl');reads=rows(native/'worker-camera-source-read-events.jsonl');boundaries=rows(native/'camera-boundary-events.jsonl')
 journal={x['debugEventSequence']:x for x in rows(native/'debug-event-clock.jsonl')}
 model=load(fine/'report.json');windows=model['measuredPerspectiveWindows'];assert len(windows)==1
 assert model['addedMeasuredHostClockBoundary'] and not model['exactOriginalInstructionScheduleRecovered'] and not model['ordinaryIndependentThreadTimingAcceptance']
 for window in windows:
  stage=window['stage'];before=next(x for x in copies if x['stage']==stage and x['event']=='scene-camera-copy-before')
  after=next(x for x in copies if x['stage']==stage and x['event']=='scene-camera-copy-after');read=next(x for x in reads if x['stage']==stage)
  assert before['worldCameraHexAtWorkerEvent']==read['worldCameraHex']==after['copiedCameraHex']
  frame=[x for x in boundaries if x['event']=='world-perspective-right-written' and x['precedingPlayerCallbacks']==window['callback']]
  ordinal=window['ordinal'];previous=frame[ordinal-1];following=frame[ordinal]
  assert ordinal==2 and window['callback']==30787 and window['readyNs']==before['hostMonotonicNs']
  assert previous['debugEventSequence']==before['lastMainCameraBoundary']['debugEventSequence']
  assert previous['hostMonotonicNs']==window['previousBoundaryNs']<before['hostMonotonicNs']<=read['hostMonotonicNs']<=after['hostMonotonicNs']<window['followingBoundaryNs']==following['hostMonotonicNs']
  assert window['sourceReadMainPc']==read['mainThreadRegisters']['eip']==0x4352b0
  for event in (previous,before,read,after,following):
   stop=journal[event['debugEventSequence']];assert stop['hostMonotonicNs']==event['hostMonotonicNs'] and stop['threadId']==event['threadId'] and stop['pc']==event['pc']
 raw_proof=load(H/'comparison-perspective-window/raw-verified.json');assert raw_proof['verifiedFiniteEvidence'] and raw_proof['callbacks']==35000
 assert raw_proof['vm303Rows']==1011 and raw_proof['combatCheckpoints']==364
 for name,binding in raw_proof['bindings'].items():
  data=raw(R/name);assert len(data)==binding['bytes'] and SHA(data)==binding['sha256']
 protected={
  'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp':'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45',
  'artifacts/th14/vm-return-worker-oct29/work-state.json':'2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}
 for name,digest in protected.items():assert SHA(raw(R/name))==digest
 return dict(verifiedFiniteCameraWindowEvidence=True,callbacks=35000,expandedFields=71,expandedCallbacks=34999,expandedWords=34999*71,
  unchangedLegacyPayloads=7,coarse=recomputed[0],measuredWindow=recomputed[1],windows=windows,vm303Rows=1011,combatCheckpoints=364,
  readOnlyObserverDoesNotAdvanceHostClock=True,measuredWindowHostClockReplayAdded=True,nativeGameplayValuesInjected=False,
  productionCoreChanged=False,ordinaryCoreWasmSha256='fc24f408b1ea2bf5c0a054dd7b06d2e1e542d0145a2df7faacbed250b2288949',
  oldRecordingFailureClosed=False,exactOriginalInstructionScheduleRecovered=False,independentSchedulingAccepted=False,
  opaqueNativeWordsNotMapped=[22,23],nativeTailWordsNotCaptured=[73,74],physicalAudioDevicesOpenedByModel=0,
  originalPcmNotMeasured=True,completeGame=False,nativeEquivalent=False,bindings=bindings,protectedFiles=protected,
  verifierSha256=SHA(Path(__file__).read_bytes()))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--check',type=Path);a=p.parse_args();assert bool(a.output)!=bool(a.check)
 result=verify();data=(json.dumps(result,indent=2)+'\n').encode()
 if a.output:
  out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.write_bytes(data)
 else:assert json.loads(a.check.read_bytes())==result
 print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','protectedFiles')}))


if __name__=='__main__':main()
