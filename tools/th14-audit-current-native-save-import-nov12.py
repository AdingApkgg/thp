"""Check two bounded current/native score-file interoperability directions."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-native-save-import-nov12'
A=H/'run'
N=R/'artifacts/th14/native-natural-title-exit-nov12-v2'
P=R/'artifacts/th14/current-title-quit-nov12'
bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
report=load(A/'report.json');receipt=load(H/'terminal-receipt.json')
assert receipt['reaped'] and receipt['exitCode']==0 and receipt['pid']==report['pid']
assert report['terminal'] and report['closed'] and report['stage']=='finished' and report['exitSaveExecuted']
assert report['ordinaryInputOnly'] and report['quiet'] and report['nativeSaveImportedAtStartup']
assert not report['exception'] and not report['errors']
assert all(w['returned'] and not w['error'] for w in report['workers'])
assert all(w['closed'] and w['exitCode']==0 for w in report['physicalWorkers'])
platform=load(A/'platform.json');assert platform['gpuContextClosed'] and not platform['audibleOutput']
assert not any(platform[k] for k in ['stream','window','context','pendingTimers','openFiles'])
assert not any(platform['actualNativeGles']['liveObjects'].values())
clock=report['processClockResolution'];assert clock['beginCalls']==clock['endCalls']==1 and not clock['active']
build=load(P/'component/build.json')
assert report['wasmSha256']==build['wasmSha256']==hashlib.sha256(read(P/'component/candidate.wasm')).hexdigest()
assert report['driverSha256']==hashlib.sha256(read(A/'run-host.mjs')).hexdigest()
for name,digest in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():
 assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
plan=load(A/'plan.json');assert plan['nativeFilesImportedAsStartupInputs']
actions=load(A/'actions.json');states=load(A/'states.json')
assert [x['held'] for x in actions]==[2,0,2,0]
assert actions[0]['state'][:5]==[0,1,1,2,0] and actions[2]['state'][:5]==[0,1,1,2,9]
assert states[-1]['words'][0]==4 and all(x['words'][8]==0 for x in states)
native=load(N/'report.json');native_ui=load(N/'ui-observed.json')
assert native['reaped'] and native['naturalOsExitObserved'] and not native_ui['ordinaryTitleQuitObserved']
files={}
for name,key in [('scoreth14.dat','initialScoreSha256'),('th14.cfg','initialConfigSha256')]:
 left=read(N/'work/appdata/ShanghaiAlice/th14'/name);right=read(A/'save'/name)
 digest=hashlib.sha256(left).hexdigest();assert digest==plan[key]==native['finalFiles'][name]['sha256']
 files[name]=dict(inputBytes=len(left),outputBytes=len(right),inputSha256=digest,
  outputSha256=hashlib.sha256(right).hexdigest(),wholeFileExact=left==right,
  differentBytes=abs(len(left)-len(right))+sum(a!=b for a,b in zip(left,right)))
# Opposite direction: the freshly written C++ file was already executed through
# retail code, not merely decoded by a port mirror.
codec=P/'native-codec';proof=load(codec/'native.json');codec_plan=load(codec/'plan.json')
tool=R/'tools/th14-browser-score-native.py'
assert hashlib.sha256(read(tool)).hexdigest()==codec_plan['toolSha256']==hashlib.sha256(read(codec/'native-codec-source-used.py')).hexdigest()
fresh=read(P/'run/save/scoreth14.dat');plain=read(codec/'expected-decoded.bin')
assert proof['passed'] and proof['nativeExecutableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert hashlib.sha256(fresh).hexdigest()==proof['inputSha256']==proof['rewrittenSha256']==codec_plan['inputSha256']
assert plain==read(codec/'retail-loaded.raw') and fresh==read(codec/'retail-rewritten.dat')
assert len(plain)==149076 and hashlib.sha256(plain).hexdigest()==proof['decodedSha256']==codec_plan['decodedSha256']
read(Path(__file__));read(R/'tools/th14-run-current-native-save-import-nov12.mjs')
out=dict(productionGameSource=build['productionGameSource'],currentWasmSha256=build['wasmSha256'],
 currentActualApplicationImportedNativeFiles=True,ordinaryTitleQuitUsedToSave=True,
 nativeFilesPreservedByteExactly=all(x['wholeFileExact'] for x in files.values()),files=files,
 freshCppScoreDecodedByActualRetailCode=True,retailDecodedBytes=len(plain),retailReencodedFileExact=True,
 retailCodecServices=['allocation','free','memcpy','memset'],
 inheritedRetailReportLauncherLabelDoesNotDescribeThisStandaloneInput=True,
 currentApplicationGameplayCallbacks=0,currentHostFrames=report['frames'],
 allOwnedResourcesRetired=True,audibleOutput=False,productionChanged=False,
 nativeOrdinaryTitleQuitAccepted=False,sameUiTriggerPairAccepted=False,
 allSavePathsAccepted=False,browserReloadPersistenceAccepted=False,completeGame=False,bindings=bindings)
p=H/'qualified.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}))
if not out['nativeFilesPreservedByteExactly']:raise SystemExit(1)
