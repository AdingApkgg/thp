"""Audit actual, repeated, UV-only counterfactual and restored GPU frames."""
from pathlib import Path
from collections import Counter
import hashlib,json
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-first-present-uv-repaint-nov12'
A=H/'current'
N=R/'artifacts/th14/current-startup-prefix-nov10/native'
bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
report=load(A/'report.json');receipt=load(H/'terminal-receipt.json')
assert receipt['reaped'] and receipt['exitCode']==0 and receipt['pid']==report['pid']
assert report['terminal'] and report['captureComplete'] and report['closed'] and report['platformRetired']
assert report['stoppedBy']=='declared-target' and report['callbacks']==1
assert not report['exception'] and not report['errors'] and not report['resourceLeaks']
assert report['gpuContextClosed'] and report['counterfactualUvRepaintAfterFirstFrame']
assert all(w['returned'] and not w['error'] for w in report['workers'])
assert all(w['closed'] and w['exitCode']==0 for w in report['physicalWorkers'])
clock=report['processClockResolution'];assert clock['beginCalls']==clock['endCalls']==1 and not clock['active']
build=load(H/'component/build.json');plan=load(A/'plan.json')
assert plan['wasmSha256']==build['wasmSha256']==hashlib.sha256(read(H/'component/candidate.wasm')).hexdigest()
assert build['gameObjectsReusedAndReverified']==141 and build['hostObjectsReusedAndReverified']==4
assert build['observationStride']==49 and build['frozenCurrentApplicationWithExistingReadObservers']
for name,digest in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
for name,digest in plan['bindings'].items():assert hashlib.sha256(read(R/name)).hexdigest()==digest,name
assert hashlib.sha256(read(A/'th14-run-first-present-uv-repaint-nov12.mjs')).hexdigest()==plan['bindings']['tools/th14-run-first-present-uv-repaint-nov12.mjs']
platform=load(A/'platform.json');assert not platform['audibleOutput']
assert not any(platform[k] for k in ['window','context','stream','pendingTimers','openFiles'])
assert not any(platform['actualNativeGles']['liveObjects'].values())
repaint=load(A/'uv-repaint.json')
assert repaint['idempotentControl'] and repaint['restoredPixelsExact'] and repaint['restoredStateExact']
assert repaint['counterfactualOnly'] and repaint['strictActualPixelsAcceptanceUnchanged']
assert [x['mode'] for x in repaint['repaints']]==[0,1,2]
for entry in repaint['repaints']:
 for i in [0,1,2,3,4,7,8,9,10]:assert entry['before'][i]==entry['after'][i]
assert repaint['actualState'][0:3]==[1,1,1]
native_report=load(N/'report.json')
assert native_report['childExited'] and native_report['frameReadbackCompleted'] and not native_report['error']
assert native_report['readback']['surfaceDescription'][0]==21
assert native_report['readback']['surfaceDescription'][6:8]==[640,480]
n=read(N/native_report['readback']['file'])
assert hashlib.sha256(n).hexdigest()==native_report['readback']['pixelSha256']
actual=read(A/'application-first-present.bgra');control=read(A/'control-repeat.bgra')
patched=read(A/'counterfactual-native-uv.bgra');restored=read(A/'restored-original-uv.bgra')
assert len(n)==len(actual)==len(patched)==640*480*4 and actual==control==restored
def differences(a,b):
 pixels=set();channels=Counter()
 for i in range(0,len(a),4):
  if a[i:i+4]!=b[i:i+4]:
   pixels.add(i//4)
   for j in range(4):channels['BGRA'[j]]+=a[i+j]!=b[i+j]
 return pixels,dict(channels)
actual_diff,actual_channels=differences(actual,n)
patched_diff,patched_channels=differences(patched,n)
changed,changed_channels=differences(actual,patched)
assert len(actual_diff)==report['comparison']['differentPixels']
assert len(changed)==repaint['repaints'][1]['differentPixelsFromActual']
for entry,raw in zip(repaint['repaints'],[control,patched,restored]):assert hashlib.sha256(raw).hexdigest()==entry['pixelSha256']
old=R/'artifacts/th14/current-first-present-vm303-nov12'
registered=load(old/'qualified.json');private=load(old/'private-vms-qualified.json')
oracle=load(old/'embedded195-native-v2/qualified.json')
assert [len(x['differences']) for x in private['embedded']]==[0,0,0,0,6]
assert [x['differentWords'] for x in private['compositorCopies']]==[0,0,0,0]
assert oracle['actualRetailInterpreter'] and oracle['threeActualUpdatesMatchAll303NativeWords']
assert [(x['steps'],x['declaredRate']) for x in oracle['cases'] if x['differentCanonicalWords']==0]==[(3,1.0)]
assert private['nativeTransitionCounter']-private['cppTransitionCounter']==3
new_counter_gap=private['nativeTransitionCounter']-repaint['actualState'][3]
native_private=load(old/'private-embedded-canonical.json')
current_private=load(A/'transition-after-draw.json')['words']
embedded_differences=[sum(a!=b for a,b in zip(row['native'],current_private[7+(i+1)*303:7+(i+2)*303])) for i,row in enumerate(native_private)]
assert embedded_differences==[0,0,0,0,6]
old_copies=load(R/'artifacts/th14/control-main-stop-nov12/first-present/candidate-owner-replay/compositor-after-draw.json')['words']
current_copies=load(A/'compositor-after-draw.json')['words'];assert current_copies==old_copies

read(Path(__file__))
out=dict(productionGameSource=build['productionGameSource'],currentWasmSha256=build['wasmSha256'],
 actualFrame=dict(hostFrames=report['frames'],playerCallbacks=1,transitionCounter=repaint['actualState'][3],
  embedded195Age=repaint['actualState'][4],differentPixels=len(actual_diff),differentChannels=actual_channels),
 repeatWithoutUpdatesPixelExact=True,onlyTwoUvFieldsReplacedInDiagnostic=True,
 counterfactual=dict(differentPixelsFromNative=len(patched_diff),differentChannelsFromNative=patched_channels,
  changedPixelsFromActual=len(changed),changedChannelsFromActual=changed_channels,
  previouslyDifferentNowEqual=len(actual_diff-patched_diff),previouslyEqualNowDifferent=len(patched_diff-actual_diff),
  stillDifferent=len(actual_diff&patched_diff),acceptanceResult=False),
 restoredAllPixelsAndMeasuredStateExact=True,measuredRngAndCountersUnchangedDuringRepaints=True,
 previousRetainedCase=dict(nativeVms=registered['nativeVms'],cppVms=registered['cppVms'],
  sameLiteralHandlesWithDifferentScripts=len(registered['commonHandlesWithDifferentFileOrScript']),
  firstFourEmbeddedVmsAll303Exact=True,fifthEmbeddedDifferentWords=6,compositorCopiesMeasuredWordsExact=204,
  transitionCounterGap=3,actualOriginalUpdatesMatchingAll303=3),
 newCaseTransitionCounterGap=new_counter_gap,differentCaseGapsNotMerged=True,
 actualCaseEmbeddedDifferentWords=embedded_differences,actualCaseCompositor204MeasuredWordsExact=True,
 capturedNativeUvWords=repaint['capturedUv'],actualUvWords=repaint['actualState'][5:7],
 noProductionSourceChanged=True,noEngineUpdatesResumedAfterDiagnostic=True,noPaddingAddedToEngine=True,
 strictActualWholeFrameStillFails=bool(actual_diff),counterfactualNotAProductionFix=True,
 allOwnedResourcesRetired=True,newOriginalGameProcesses=0,newCppRuns=1,audibleOutput=False,
 completeGame=False,bindings=bindings)
p=H/'qualified.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','previousRetainedCase']}))
