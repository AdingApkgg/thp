"""Qualify and atomically adopt the original-width right-vector publications."""
from pathlib import Path
import datetime,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-right-pair-nov12';OUT=H/'qualified.json';assert not OUT.exists()
bindings={}
def read(p):
    raw=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(raw).hexdigest();return raw
load=lambda p:json.loads(read(p));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=load(H/'prepared.json');S=Path(p['sourceRoot']);core=load(H/'candidate/build.json');audit=load(H/'object-audit/checked.json');math=load(H/'component/verified.json');observed=load(H/'candidate-component/checked.json');baseline=load(H/'baseline-component/checked.json');appbuild=load(H/'application/component/build.json');app=load(H/'application/current/report.json');exit_event=load(H/'application/current/exit-event.json')
assert core['freshlyCompiledGameUnits']==141 and core['normalAccess']
assert audit['allEightControlPairsByteIdentical'] and len(audit['controls'])==8 and len(audit['backends'])==4
for backend in audit['backends']:assert sha(R/backend['disassemblyPath'])==backend['disassemblySha256']
for path,d in core['sourceBindings'].items():assert sha(S/path)==d,path
for row in core['objects']:assert sha(R/row['object'])==row['objectSha256']
for path,d in p['parentSourceBindings'].items():assert sha(R/path)==d,path
assert len(core['sourceBindings'])==368
assert math['cases']==math['fovMatrixPositiveControls']==40 and math['all75WordsEqual']
for path,row in math['bindings'].items():assert sha(R/path)==row['sha256'],path
assert observed['cases']==baseline['cases']==80 and observed['all75WordsEqual'] and baseline['all75WordsEqual']
assert observed['sharedOwnerLayout'][0:2]==[300,4] and observed['sharedOwnerLayout'][3]==8 and observed['sharedOwnerLayout'][5:7]==[0,0]
assert baseline['sharedOwnerLayout'][3]==4 and observed['sharedOwnerLayout'][2]==baseline['sharedOwnerLayout'][2]
assert [r['sha256'] for r in baseline['rows']]==[r['sha256'] for r in observed['rows']]
assert app['captureComplete'] and app['sharedWorldRightQwordAlignedAtRealApplicationStart'] and app['frames']==508 and app['callbacks']==1
assert app['exception'] is None and not app['errors'] and app['closed'] and app['gpuContextClosed'] and app['platformRetired'] and not app['resourceLeaks']
assert all(w['returned'] and not w['error'] for w in app['workers']) and all(w['closed'] and w['exitCode']==0 for w in app['physicalWorkers'])
assert exit_event['code']==0 and exit_event['phase']=='finished' and exit_event['gpuContextClosed']
assert app['comparison']['selectedBeforePlayerDifferences']==[] and not app['comparison']['pixelsExact']
assert app['comparison']['differentPixels']==194896 and app['comparison']['byChannel'][3]==3092 and app['comparison']['cppAfterFrameRng']==[39319,2588,4607,0]
assert sha(H/'application/component/candidate.wasm')==appbuild['wasmSha256']
for path,d in {**appbuild['sourceBindingsByMode']['candidate'],**appbuild['objectBindings']}.items():assert sha(R/path)==d,path
protected=R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp';assert sha(protected)=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
changes=[]
for path in ['runtimes/th12/th12_web/cpp/game/SceneCamera.cpp','runtimes/th12/th12_web/cpp/game/SceneCompositor.hpp',p['addedHeader']]:
    dest=R/path;source=S/path;before=sha(dest) if dest.exists() else None
    if before is None:assert path==p['addedHeader']
    else:assert before==p['parentSourceBindings'][path]
    temp=dest.with_suffix(dest.suffix+'.camera-right.tmp');temp.write_bytes(source.read_bytes());temp.replace(dest);assert sha(dest)==core['sourceBindings'][path]
    changes.append(dict(path=path,beforeSha256=before,afterSha256=sha(dest)))
for path,d in core['sourceBindings'].items():assert sha(R/path)==d,path
receipt=dict(execSession=88369,pid=app['pid'],reaped=True,exitCode=0,allWorkersReturnedAndJoined=True,gpuRetired=True,processClockRetired=True,completeGame=False)
(H/'application/terminal-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
result=dict(schema='thp/th14-camera-right-publication/1',sourceAdopted=True,changes=changes,currentSourceBindings=core['sourceBindings'],
    originalRightPublication=[dict(offset=48,bytes=8),dict(offset=56,bytes=4),dict(offset=48,bytes=4),dict(offset=52,bytes=4),dict(offset=56,bytes=4)],
    oldOptimizedRawRightYThenXWasTwoStores=True,newSharedRightPairAtomic64=True,sharedWorldCameraAlignment=8,sceneCameraBytes=300,sceneCompositorBytesUnchanged=True,
    candidateNormalGameUnitsFresh=141,optimizedSdkAndBrowserProviderObjectsChecked=True,otherTitleAndNoWorkerControlPairs=8,allControlPairsByteIdentical=True,
    actualOriginalMathCases=40,fovPositiveControls=40,phaseObservedAlignedAndUnalignedCases=80,all75FinalWordsEqual=True,normalEngineAccess=True,
    realCppApplication=dict(frames=508,playerCallbacks=1,sharedWorldRightAligned=True,allOwnedResourcesRetired=True,wasmSha256=appbuild['wasmSha256'],strictPixelsDifferent=194896,strictAlphaBytesDifferent=3092,scriptCallOffsetStill24=True,comparisonMustNotBeAttributedToThisFixAlone=True),
    unalignedOtherPrivateCameraFallbackHasNoAtomicityClaim=True,noWholeCameraAtomicityClaim=True,oldWholeCameraFailureCauseProved=False,loadingPhysicalScheduleAccepted=False,browserUiAcceptance=False,completeGame=False,
    atomicityReference='https://www.intel.com/content/dam/support/us/en/documents/processors/pentium4/sb/25366821.pdf',
    wasmAlignmentReference='https://github.com/WebAssembly/threads/blob/main/proposals/threads/Overview.md',
    protectedResourceCryptUnchanged=True,newOriginalGameRuns=0,newCppApplicationGpuRuns=1,bindings=bindings)
OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','currentSourceBindings']}))
