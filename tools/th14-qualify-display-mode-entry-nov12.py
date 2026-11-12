"""Qualify the executed candidate and adopt exactly eight reviewed source files."""
from pathlib import Path
import hashlib,json,os,difflib
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-mode-entry-nov12';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
P=load(H/'prepared.json');S=Path(P['sourceRoot']);assert len(P['changes'])==8
for name,d in P['sourceBindings'].items():assert sha(S/name)==d,name
core=load(H/'candidate/build.json');assert core['sourceBindings']==P['sourceBindings'];assert len(core['objects'])==141
for row in core['objects']:assert sha(R/row['object'])==row['objectSha256'] and sha(S/row['source'])==row['sourceSha256']
app=load(H/'application/component/build.json');assert app['normalProviders']==145 and app['observedNativeRenderTargetResizeAndUvApplied']
for name,d in {**app['sourceBindings'],**app['objectBindings']}.items():assert sha(R/name)==d,name
assert sha(H/'application/component/candidate.wasm')==app['wasmSha256']
native=load(H/'native.json');assert native['cases']==216 and native['originalCodeUnmodified'] and not native['nativeGameStarted'];assert native['toolSha256']==sha(R/'tools/th14-display-mode-native-nov12.py')
context=load(H/'context-native-v2/report.json');assert context['cases']==12 and context['nativeInstructionBytesUnmodified'];assert context['toolSha256']==sha(R/'tools/th14-display-context-native-nov12.py')
context_checked=load(H/'context-component/checked.json');assert context_checked['comparedWords']==1332 and not context_checked['differentWords']
targets=load(H/'targets-native-v2/native.json');derived=load(H/'targets-native-v2/derivation.json')
assert sha(H/'targets-native-v2/run-native.py')==targets['toolSha256']==derived['derivedSha256'];assert targets['textureHostSha256']==sha(R/'tools/th14-native-physical-texture-host.py')
assert derived['parentSha256']==sha(R/'tools/th14-anm-physical-resource-loader-native.py') and len(targets['rows'])==6
bindings={};runs=[]
def bound(p):bindings[p.relative_to(R).as_posix()]=sha(p)
for mode in [3,4,5]:
 h=H/f'application/run-v2-mode{mode}';r=load(h/'report.json');t=load(h/'terminal-receipt.json');d=load(h/'display.json');uv=load(h/'targets.json');platform=load(h/'platform.json')
 assert r['terminal'] and r['closed'] and not r['exception'] and not r['errors'] and r['exitSaveExecuted'] and r['displayCaptured'] and r['frames']==400 and r['stage']=='finished'
 assert t['reaped'] and t['exitCode']==0 and t['pid']==r['pid'] and r['wasmSha256']==app['wasmSha256']
 assert all(w['returned'] and not w['error'] for w in r['workers']) and all(w['closed'] and w['exitCode']==0 for w in r['physicalWorkers'])
 assert platform['gpuContextClosed'] and not platform['audibleOutput'] and not platform['pendingTimers'] and not platform['openFiles']
 assert not any(platform['actualNativeGles']['liveObjects'].values()) and not any(platform['liveObjects'].values())
 assert not any(platform[k] for k in ['window','context','stream'])
 assert r['processClockResolution']['beginCalls']==r['processClockResolution']['endCalls']==1 and not r['processClockResolution']['active']
 n=next(x for x in native['rows'] if x['mode']==mode);assert (d['width'],d['height'])==(n['width'],n['height'])
 assert sha(h/'title.bgra')==d['pixelsSha256'] and (h/'title.bgra').stat().st_size==n['width']*n['height']*4
 assert uv['targetCount']==10 and uv['comparedNativeWords']==140
 assert bytes.fromhex('0000')==(h/'save/th14.cfg').read_bytes()[0x22:0x24]
 assert (h/'save/th14.cfg').read_bytes()[0x1f]==mode
 for filename in ['report.json','terminal-receipt.json','display.json','targets.json','platform.json','plan.json','actions.json','states.json','title.bgra','save/th14.cfg','save/scoreth14.dat']:bound(h/filename)
 runs.append(dict(mode=mode,width=d['width'],height=d['height'],hostFrames=r['frames'],playerCallbacks=0,normalTitleQuit=True,saved=True,nativeTargetSpriteWords=140,nativeTargetSpriteDifferences=0,quiet=True,allResourcesRetired=True,scoreSha256=sha(h/'save/scoreth14.dat')))
assert len({r['scoreSha256'] for r in runs})==1
failure=load(H/'application/run-mode4/report.json');failed_receipt=load(H/'application/run-mode4/terminal-receipt.json');assert failure['frames']==43 and '1286' in failure['exception'] and failed_receipt['reaped'] and failed_receipt['exitCode']==1
legacy=[]
for title in [12,13,16]:
 p=H/f'legacy-th{title}/checked.json';j=load(p);assert j['allByteIdentical'] and len(j['objectPairs'])==4
 for row in j['objectPairs']:
  for obj in row['objects']:assert sha(R/obj['object'])==obj['objectSha256']
 bound(p);legacy.append(dict(title=title,byteIdenticalObjectPairs=4))
for p in [H/'native.json',H/'context-native-v2/report.json',H/'context-component/checked.json',H/'targets-native-v2/native.json',H/'targets-native-v2/derivation.json',H/'prepared.json',H/'candidate/build.json',H/'application/component/build.json']:bound(p)
protected=R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp';assert sha(protected)=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
assert not (H/'qualified.json').exists()
# Verify the complete whitelist before any canonical source replacement.
for row in P['changes']:assert sha(R/row['path'])==row['beforeSha256'] and sha(S/row['path'])==row['afterSha256']
diff=[]
for row in P['changes']:
 p=R/row['path'];before=p.read_bytes();after=(S/row['path']).read_bytes()
 diff.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile=row['path'],tofile=row['path']))
 tmp=p.with_suffix(p.suffix+'.th14-display-tmp');tmp.write_bytes(after);os.replace(tmp,p);assert sha(p)==row['afterSha256']
(H/'reviewed-source.diff').write_text(''.join(diff),encoding='utf8')
for name,d in P['sourceBindings'].items():assert sha(R/name)==d,name
result=dict(schema='thp/th14-display-mode-entry/1',sourceAdopted=True,changedFiles=P['changes'],currentSourceBindings=P['sourceBindings'],
 nativeModeSelectionCases=216,nativeContextCases=12,nativeContextComparedWords=1332,nativeContextDifferentWords=0,
 nativeLoaderResourcesAtThreeSizes=6,actualNativeRenderTargetRequests=6,currentApplicationRuns=runs,
 currentApplicationWasmSha256=app['wasmSha256'],normalGameProviders=141,normalHostProviders=4,fixtureOnlyRelaxedAccess=True,
 strictNativeTargetSpriteWords=420,strictNativeTargetSpriteDifferentWords=0,legacyObjectControls=legacy,
 firstLargerModeFramebufferFailureRetained=True,newOriginalGameRuns=0,newActualApplicationRuns=5,currentAcceptedRuns=3,
 originalD3dAndFileServicesDeclared=True,nativeMatrixAndWholePixelsNotAccepted=True,browserUiAccepted=False,browserRuntimeBuilt=False,runtimeDeployed=False,
 knownRngAndWholeFrameFailuresRemain=True,physicalWindowsFullscreenNotClaimed=True,publicRawAssetsOrPixelsAuthorizedForUpload=False,
 protectedResourceCryptUnchanged=True,completeGame=False,nativeEquivalent=False,bindings=bindings,qualifierSha256=sha(Path(__file__)))
(H/'qualified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','currentSourceBindings','changedFiles','currentApplicationRuns']}))
