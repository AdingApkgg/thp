"""Audit one real first-Present GPU run and retain every strict failure."""
from pathlib import Path
import hashlib,json,os,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/first-present-alpha-localization-nov12';B=H/'batch-state';A=B/'application/current';bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
q=load(B/'qualified.json');assert q['sourceAdopted']and q['candidateFailedCases']==0 and q['baselineFailedCases']==135
source=R/'runtimes/th12/th12_web/cpp/game/AnmRenderer.cpp';assert hashlib.sha256(read(source)).hexdigest()==q['sourceAfterSha256']
report=load(A/'report.json');receipt=load(B/'application/terminal-receipt.json');assert receipt['reaped']and receipt['exitCode']==0 and receipt['pid']==report['pid']==45844
assert report['terminal']and report['closed']and report['captureComplete']and report['callbacks']==1 and report['frames']==507 and report['stoppedBy']=='declared-target'
assert not report['exception']and not report['errors']and report['platformRetired']and not report['resourceLeaks']and report['gpuContextClosed']
assert all(w['returned']and not w['error']for w in report['workers']);assert all(w['closed']and w['exitCode']==0 for w in report['physicalWorkers']);clock=report['processClockResolution'];assert not clock['active']and clock['beginCalls']==clock['endCalls']==1
build=load(B/'application/component/build.json');plan=load(A/'plan.json');assert hashlib.sha256(read(B/'application/component/candidate.wasm')).hexdigest()==plan['wasmSha256']==build['wasmSha256']
for p,d in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():assert hashlib.sha256(read(R/p)).hexdigest()==d,p
for p,d in plan['bindings'].items():assert hashlib.sha256(read(R/p)).hexdigest()==d,p
platform=load(A/'platform.json');assert not platform['audibleOutput']and not any(platform['actualNativeGles']['liveObjects'].values())
uv=load(A/'uv-repaint.json');assert uv['idempotentControl']and uv['restoredPixelsExact']and uv['restoredStateExact']and uv['counterfactualOnly'];assert [r['mode']for r in uv['repaints']]==[0,1,2]
actual=read(A/'application-first-present.bgra');repeat=read(A/'control-repeat.bgra');counterfactual=read(A/'counterfactual-native-uv.bgra');restored=read(A/'restored-original-uv.bgra');assert actual==repeat==restored
N=R/'artifacts/th14/current-startup-prefix-nov10/native';nr=load(N/'report.json');assert nr['childExited']and nr['readback']['surfaceDescription'][0]==21;native=read(N/nr['readback']['file']);assert hashlib.sha256(native).hexdigest()==nr['readback']['pixelSha256'];assert len(native)==len(actual)==len(counterfactual)==640*480*4
count=lambda a,b:sum(a[i:i+4]!=b[i:i+4]for i in range(0,len(a),4));alpha=lambda a,b:sum(a[i]!=b[i]for i in range(3,len(a),4));actual_count=count(native,actual);cf_count=count(native,counterfactual);alpha_count=alpha(native,actual);assert (actual_count,cf_count,alpha_count)==(281902,4460,3036);assert actual[3::4]==counterfactual[3::4]
for entry in uv['repaints']:
 for i in [0,1,2,3,4,7,8,9,10]:assert entry['before'][i]==entry['after'][i]
P=R/'artifacts/th14/current-first-present-vm303-nov12';embedded=load(P/'private-embedded-canonical.json');current=load(A/'transition-after-draw.json')['words'];differences=[sum(a!=b for a,b in zip(row['native'],current[7+(i+1)*303:7+(i+2)*303]))for i,row in enumerate(embedded)];assert differences==[0,0,0,0,6]
quad=load(H/'embedded-quads/checked.json');assert quad['cppAllOriginalGeometryExact']and quad['cppAllNativeCapturedCachesExact']
footprints=load(H/'geometry-loading-family/qualified.json');assert footprints['strictWholeFrameStillFails'];assert [r['alphaOutsideUnion']for r in footprints['footprints']]==[9,9]
raw=read(A/'target-live-vms.u32');w=struct.unpack('<'+'I'*(len(raw)//4),raw);assert w[:6]==(1,1,1,76,1,303);fields=load(P/'native-canonical.json')['fields'];cpp=[w[i:i+303]for i in range(6,len(w),303)];nrows=load(P/'native-canonical.json')['rows'];words=[]
for script in [14,15]:
 n=next(r for r in nrows if r[1:3]==[2,script]);c=next(r for r in cpp if r[1:3]==(2,script));idx=fields.index('nativeVmWord0x534');words.append(dict(script=script,nativeAge=n[fields.index('ageCurrent')],cppAge=c[fields.index('ageCurrent')],nativeAlpha=n[idx]>>24,cppAlpha=c[idx]>>24))
assert words==[dict(script=14,nativeAge=84,cppAge=79,nativeAlpha=244,cppAlpha=254),dict(script=15,nativeAge=84,cppAge=79,nativeAlpha=183,cppAlpha=220)]
browser=load(B/'browser/build.json');assert browser['freshlyCompiledUnits']==1 and browser['reusedAndHashVerifiedUnits']==145
assert hashlib.sha256(read(B/'browser/th14-sdl.wasm')).hexdigest()==browser['sha256'];assert hashlib.sha256(read(B/'browser/th14-sdl.mjs')).hexdigest()==browser['loaderSha256']
for p,d in browser['sourceBindings'].items():assert hashlib.sha256(read(R/p)).hexdigest()==d,p
for row in browser['objects']:assert hashlib.sha256(read(R/row['object'])).hexdigest()==row['sha256']
old=R/'artifacts/th14/current-first-present-uv-repaint-nov12/current';old_pixels=read(old/'counterfactual-native-uv.bgra');points=[]
for x,y in [(0,0),(4,0),(10,0),(0,240),(0,445),(620,225)]:
 i=(y*640+x)*4+3;points.append(dict(x=x,y=y,nativeAlpha=native[i],parentDiagnosticAlpha=old_pixels[i],currentDiagnosticAlpha=counterfactual[i]));assert native[i]==counterfactual[i]and old_pixels[i]!=native[i]
protected=R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp';assert hashlib.sha256(read(protected)).hexdigest()=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
read(Path(__file__));out=dict(sourceBeforeSha256=q['sourceBeforeSha256'],sourceAfterSha256=q['sourceAfterSha256'],actualApplicationRuns=1,newOriginalGameProcesses=0,playerCallbacks=1,hostFrames=507,pid=45844,reaped=True,allOwnedResourcesRetired=True,currentActualDifferentPixels=actual_count,currentActualDifferentAlphaPixels=alpha_count,uvDiagnosticDifferentPixels=cf_count,uvDiagnosticNotAcceptedAsFix=True,actualAndUvDiagnosticAlphaIdentical=True,repeatAndRestoredAllPixelsExact=True,scriptCallDifference=24,cppRng=report['comparison']['cppAfterFrameRng'],transitionCounterNative=84,transitionCounterCpp=79,firstFourEmbeddedAll303Exact=True,fifthEmbeddedDifferentWords=6,retainedNativeFourQuadCacheWordsExact=48,loadingWords=words,spatialFootprintOnly=footprints['footprints'],nineAlphaDifferencesOutsideLoadingFootprintsRetained=True,parentAndCurrentDifferentLoadingTimingNotComparedAsWholeFrameImprovement=True,selectedCornerAlphaDiagnostics=points,browserWasmSha256=browser['sha256'],freshBrowserUnits=1,hashVerifiedReusedBrowserUnits=145,browserUiAcceptance=False,productionRuntimeUpdated=False,audibleOutput=False,completeGame=False,bindings=bindings)
p=B/'gpu-qualified.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['bindings','spatialFootprintOnly','selectedCornerAlphaDiagnostics']}))
wpath=R/'artifacts/th14/option-recall-once-nov02/work-state.json';state=load(wpath);state['type0BatchStateNov12']={k:v for k,v in out.items()if k not in ['bindings','spatialFootprintOnly']};state['previousGoalTurnClass']='progress: original delayed batch submission exposed type0 alpha-state bug; source fix adopted,360 CPU cases exact and one real silent GPU run retired; publication pending.';t=wpath.with_suffix('.pending.json');t.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8');os.replace(t,wpath)
