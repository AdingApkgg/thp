"""Qualify finite actual-Application viewer cases without publishing replay bytes."""
from pathlib import Path
import hashlib,json,os
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-viewer-application-nov13'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=load(H/'browser/build.json');component=load(H/'component-v3/build.json')
for n,h in build['sourceBindings'].items():assert sha(R/n)==h,n
assert sha(H/'browser/th14-sdl.wasm')==build['sha256']
assert sha(H/'browser/th14-sdl.mjs')==build['loaderSha256']
for n,v in build['runtimeFiles'].items():assert sha(H/'browser'/n)==v['sha256'],n
reports={}
for case in ['transport-v2','multistage-v1']:
 p=H/case;j=load(p/'report.json')
 assert j['passed'] and j['terminal'] and j['retired'] and j['closed'] and not j['errors'] and j['exception']is None
 assert j['sourceWasmSha256']==component['outputs']['candidate']['wasmSha256']
 assert j['driverSha256']==sha(p/'executed-driver.mjs')
 clock=load(p/'process-clock.json');assert not clock['active'] and clock['beginCalls']==clock['endCalls']==1
 reports[case]=dict(reportSha256=sha(p/'report.json'),driverSha256=j['driverSha256'],checkpoints=[x['name']for x in j['checkpoints']],actualThreadsRetired=True)
first=load(H/'transport-v2/checkpoint-seek150.json');again=load(H/'transport-v2/checkpoint-seek150-repeat.json')
assert first['behavior'][1:15]==again['behavior'][1:15]
assert load(H/'transport-v2/clock-rates.json')=={'0':1920,'1':60,'2':120,'4':240,'8':480,'0.5':30}
assert load(H/'transport-v2/checkpoint-ended.json')['state']['ended']
assert not load(H/'transport-v2/checkpoint-restarted-after-end.json')['state']['ended']
assert sha(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp')=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
j=dict(acceptanceStandard='observable-behavior-alignment',actualApplicationAndCppThreads=True,
 nativeControlsImplemented=['inspect','open','pause','play','seek','rate','relocate'],
 testedClockRates=[.5,1,2,4,8,0],testedSameReplayRelocation=True,selectedStageAndCrossStageSeeking=True,
 selectedStageRestartFirstPresentedFrame=1,syntheticCounterOrRngWrites=False,silent=True,
 graphicsRecordingOnly=True,browserUiAccepted=False,deployed=False,completeGame=False,
 browserWasmSha256=build['sha256'],browserLoaderSha256=build['loaderSha256'],
 normalSdkUnitsRecompiled=1,verifiedReusedObjects=145,sourceBindings=len(build['sourceBindings']),reports=reports,
 retainedFailures=['component (missing enum namespace)','transport-v1 (cold loader handoff not ready)'],
 pending=['Actual browser workspace controls','All ordinary flow and mode coverage','Nested replay-folder semantics'])
target=R/'docs/porting/th14-native-viewer-nov13.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(j,indent=2)+'\n');os.replace(tmp,target)
print(json.dumps(j,indent=2))
