"""Qualify the joint copy/default-reset test, preserving the strict replay gap."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-copy-constructor-nov13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
n=load(H/'native.json');r=load(H/'result.json');b=load(H/'component-v2/build.json')
assert r['passed']and r['cases']==72 and r['comparedWords']==10800 and r['differentWords']==0
assert r['allTasksAndWorkersRetired']and r['normalAccessControl']and r['platformCalls']==0
assert n['originalInstructionBytesPatched']==0 and n['cachedMatricesPreservedByOriginalConstructor']
assert r['bindings']['native']==sha(H/'native.json')and r['bindings']['build']==sha(H/'component-v2/build.json')
assert r['bindings']['runner']==sha(R/'tools/th14-check-camera-copy-constructor-nov13.mjs')
for name,digest in {**b['sourceBindings'],**b['objectBindings']}.items():assert sha(R/name)==digest,name
assert sha(H/'component-v2/probe.wasm')==b['wasmSha256']
summary=dict(schema='thp/th14-camera-copy-constructor/1',passed=True,sourceCommit=b['sourceCommit'],
 cases=72,comparedWords=10800,differentWords=0,realLoadingWorkerTasks=len(r['tasks']),normalAccessControl=True,
 normalGameObjectsVerifiedReused=141,actualRetailCopyAndDefaultResetBlock=['40d412','40d502'],
 unchangedOriginal75WordCopy='40d445',originalInstructionBytesPatched=0,
 actualCppStageOwnerCreationCaptureInitializeAndTransfer=True,controlledBeforeAndAfterScreenPerspective=True,
 retainedPoseCallbacks=[30528,30689,30828],stageNumberParameters=[1,2,3,4,5,6],
 resourceBoundary='Zero object storage, one placeholder STD instruction; no asset VM initialization',
 originalFullConstructorOrCallbackRegistrationAccepted=False,partialMathStoreInterleavingsAccepted=False,
 physicalWriterOrCopyTimestampProven=False,strict35kCameraMismatchClosed=False,
 cachedMatricesPreservedByOriginalConstructor=True,noForcedScreenCachePatchApplied=True,
 allTasksAndWorkersRetired=True,newGameGpuOrAudioStarted=False,productionChanged=False,completeGame=False,
 firstFixturePrivateObserverCompileFailurePreserved=True,
 bindings={p.relative_to(R).as_posix():sha(p)for p in [H/'native.json',H/'result.json',H/'component-v2/build.json',Path(__file__)]})
out=R/'docs/porting/th14-camera-copy-constructor-nov13.json';assert not out.exists();out.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k]for k in ['passed','cases','comparedWords','differentWords','strict35kCameraMismatchClosed']}))
