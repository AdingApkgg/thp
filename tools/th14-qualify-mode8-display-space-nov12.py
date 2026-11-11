"""Qualify the adopted source fix, clean builds and bounded default regression."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/mode8-display-space-nov12'
bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
def verify(path,digest):assert hashlib.sha256(read(path)).hexdigest()==digest,path
native=load(H/'native.json');assert native['cases']==4608 and native['allRotationsZero']
assert native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
verify(H/'inputs.bin',native['inputSha256']);verify(H/'outputs.u32',native['outputSha256'])
verify(R/'tools/th14-mode8-display-native-nov12.py',native['toolSha256'])
for name,digest in native['sourceBaseline'].items():verify(H/'baseline-source'/name,digest)
old=load(H/'baseline/checked.json');rejected=load(H/'candidate/checked.json')
matrix=load(H/'candidate-v2/checked.json');draw_old=load(H/'baseline-draw/checked.json');draw=load(H/'candidate-draw/checked.json')
assert old['failedCases']==draw_old['failedCases']==3520 and old['differentWords']==8480
assert rejected['failedCases']==1280
for report in [matrix,draw]:
 assert report['failedCases']==report['differentWords']==0 and report['wordsCompared']==152064
 assert report['actualOutputSha256']==report['nativeOutputSha256']==native['outputSha256']
assert all(r['byWidth']['640']['failed']==0 for r in [old,draw_old,matrix,draw])
shared=load(H/'other-titles/qualified.json');assert shared['allFourObjectsByteIdentical']
for row in shared['rows']:
 assert row['byteIdentical'] and row['objectSha256']['baseline']==row['objectSha256']['candidate']
 for mode in ['baseline','candidate']:verify(H/'other-titles'/(f"th{row['title']}-"+mode+'-'+row['source']+'.o'),row['objectSha256'][mode])
adopt=load(H/'source-adoption.json');assert adopt['adopted'] and adopt['classLayoutsUnchanged']
for row in adopt['files']:
 verify(R/row['path'],row['afterSha256']);verify(H/'candidate-source-v2'/Path(row['path']).name,row['afterSha256'])
core=load(H/'current-core/build.json');assert core['normalEngineAccessControl'] and core['gameUnitsCompiled']==141 and not core['priorArtifactObjectsUsed']
assert load(H/'current-core/terminal-receipt.json')['reaped']
candidate=load(H/'candidate-v2/build.json');candidate_objects={Path(p).name:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in candidate['objects']}
for row in core['currentProviders']:
 p=Path(row['object']);verify(p,row['objectSha256']);assert candidate_objects[p.name]==row['objectSha256']
for p,d in core['sourceBindings'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==d,p
browser=load(H/'browser/build.json');assert browser['cleanBuild'] and browser['units']==146 and browser['reusedObjects']==0
assert load(H/'browser/terminal-receipt.json')['reaped']
verify(H/'browser/th14-sdl.wasm',browser['sha256']);verify(H/'browser/th14-sdl.mjs',browser['loaderSha256'])
for p,d in browser['sourceBindings'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==d,p
for row in browser['compileResults']:verify(R/row['object'],row['sha256'])
assert set(browser['changedSourceInputs'])=={x['path'] for x in adopt['files']}
A=H/'application/current';report=load(A/'report.json');receipt=load(A/'terminal-receipt.json')
assert receipt['reaped'] and receipt['exitCode']==0 and receipt['pid']==report['pid']
assert report['captureComplete'] and report['terminal'] and report['closed'] and report['callbacks']==1
assert not report['exception'] and not report['errors'] and report['platformRetired'] and not report['resourceLeaks'] and report['gpuContextClosed']
assert all(w['returned'] and not w['error'] for w in report['workers'])
assert all(w['closed'] and w['exitCode']==0 for w in report['physicalWorkers'])
platform=load(A/'platform.json');assert not platform['audibleOutput'] and not any(platform['actualNativeGles']['liveObjects'].values())
app=load(H/'application/component/build.json');plan=load(A/'plan.json')
verify(H/'application/component/candidate.wasm',app['wasmSha256']);assert app['wasmSha256']==plan['wasmSha256']
for p,d in app['sourceBindingsByMode']['candidate'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==d,p
for p,d in app['objectBindings'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==d,p
previous=R/'artifacts/th14/current-first-present-uv-repaint-nov12/current'
old_vm=read(previous/'target-live-vms.u32');new_vm=read(A/'target-live-vms.u32');assert old_vm==new_vm
words=struct.unpack_from('<6I',new_vm);assert words==(1,1,1,76,1,303)
old_pixels=read(previous/'application-first-present.bgra');new_pixels=read(A/'application-first-present.bgra')
different=[i//4 for i in range(0,len(old_pixels),4) if old_pixels[i:i+4]!=new_pixels[i:i+4]]
bounds=[min(p%640 for p in different),min(p//640 for p in different),max(p%640 for p in different),max(p//640 for p in different)]
assert len(different)==37 and bounds==[607,470,612,477]
interface=load(H/'browser/browser-interface-failure.json');assert not interface['browserUiAcceptance']
protected=R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp'
verify(protected,'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45')
for p in [Path(__file__),R/'tools/th14-mode8-display-component-nov12.cpp',R/'tools/th14-mode8-display-renderer-component-nov12.cpp',R/'tools/th14-check-mode8-display-nov12.mjs']:read(p)
out=dict(adoptedSourceFiles=adopt['files'],actualNativeProducerCases=4608,matrixWordsPerCase=33,
 baselineFailedCases=3520,baselineDifferentWords=8480,firstCandidateOriginSwapFailuresPreserved=1280,
 candidateMatrixFailedCases=0,candidateRendererFailedCases=0,wordsComparedEachRoute=152064,
 displayModes=[[480,360],[640,480],[800,600],[801,623],[960,720],[1280,960]],
 resolutionModes=list(range(8)),allThreeOriginBranches=True,dirtyAndFreezeControls=True,parentControls=True,
 allNewControlRotationsZero=True,matricesExactNotFloatTolerance=True,nondefaultGpuPixelsNotAccepted=True,
 th13AndTh16FourObjectsByteIdentical=True,cleanCurrentGameProviders=141,
 cleanProvidersAllByteIdenticalToQualifiedCandidate=True,cleanBrowserUnits=146,browserWasmSha256=browser['sha256'],
 actualDefaultApplication=dict(playerCallbacks=1,hostFrames=report['frames'],liveVm303WordsByteExactToParent=True,
  liveVmCount=76,liveVmBytesCompared=len(new_vm),differentWholeFramePixelsToParent=len(different),differentPixelBoundsToParent=bounds,
  differentPixelsFromOriginal=report['comparison']['differentPixels'],strictWholeFramePassed=False),
 allOwnedResourcesRetired=True,protectedResourceCryptUnchanged=True,audibleOutput=False,
 browserUiAcceptance=False,browserInterfaceTimedOutTwice=True,productionRuntimeUpdated=False,
 loadingRngAndCameraGapsNotClosed=True,completeGame=False,bindings=bindings)
p=H/'qualified.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','adoptedSourceFiles']}))
