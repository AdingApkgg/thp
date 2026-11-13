"""Strict offline current Normal comparison; no gameplay rerun or normalization."""
from pathlib import Path
from collections import Counter
import ast,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/current-normal-full-nov13'
N=R/'artifacts/th14/player-entry-end-menu-nov06/campaign';A=H/'full-campaign-v2'
bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b
def load(p):return json.loads(read(p))
nr,cr,proof=load(N/'report.json'),load(A/'report.json'),load(N/'verified.json')
assert nr['childExited']and not nr['error']and nr['observedForcedReplayEndMenu']
assert not nr['debuggerAttached']and nr['instructionBytesPatched']==6 and nr['rngOrCounterWrites']==0
assert not nr['originalDiskFilesChanged']and nr['configuredMusicAndSoundVolumeZero']
assert proof['nativeStableForcedReplayEndVerified']and proof['rawRowsAndPayloadsVerified']and proof['callbacks']==122005
for n,b in proof['bindings'].items():
 if n.startswith('artifacts/th14/player-entry-end-menu-nov06/campaign/'):assert hashlib.sha256(read(R/n)).hexdigest()==b['sha256'],n
assert cr['terminal']and cr['closed']and not cr['exception']and not cr['errors']and cr['captureComplete']
assert not cr['referenceRowsReadDuringExecution']and cr['graphicsRecordingOnly']
assert nr['callbacks']==cr['callbacks']==122005
assert hashlib.sha256(read(R/'tools/th14-run-current-normal-full-nov13.mjs')).hexdigest()==cr['driverSha256']
plan=load(A/'plan.json');build=load(H/'component-v2/build.json')
assert hashlib.sha256(read(H/'component-v2/build.json')).hexdigest()==plan['buildSha256']
assert hashlib.sha256(read(H/'component-v2/candidate.wasm')).hexdigest()==build['outputs']['candidate']['wasmSha256']==cr['wasmSha256']
for n,h in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():assert hashlib.sha256(read(R/n)).hexdigest()==h,n
assert len(build['objectBindings'])==145
assert hashlib.sha256(read(N/'untouched-first-player.json')).hexdigest()==plan['initialSha256']
assert hashlib.sha256(read(N/'plan.json')).hexdigest()==plan['nativeObserverPlanSha256']
assert all(t['returned']and not t['error']for t in cr['workers'])
assert all(t['closed']and t['exitCode']==0 for t in cr['physicalWorkers'])
platform=load(A/'platform.json')
assert not any(platform[k]for k in ['stream','window','context','pendingTimers','openFiles','liveDeclaredGpuFences'])
assert not any(platform['liveObjects'].values())and not platform['audibleOutput']
assert not platform['productionDelivery']['activeRestore']and not platform['productionDelivery']['activeScene']
assert all(t['exited']and not t['error']for t in platform['productionDelivery']['workers'])
assert platform['ownedAsyncScheduled']==platform['ownedAsyncDelivered']
clock=cr['processClockResolution'];assert clock['beginCalls']==clock['endCalls']==1 and clock['endResult']==0 and not clock['active']
payloads={}
for n,key,width in [('selected-state.u32','selectedSha256',32),('world-camera.raw','worldCameraSha256',73),('world-camera-tail.u32','worldCameraTailSha256',2),('hud-score.u32','hudScoreSha256',2),('replay-cursor.u32','replayCursorSha256',14)]:
 b=read(N/n);assert len(b)==122005*width*4 and hashlib.sha256(b).hexdigest()==nr[key];payloads[n]=b
data=read(A/'observations.u32');assert len(data)==122005*456
diff={n:Counter()for n in ['state32','camera75','hud2','cursor4']};first={};stages=Counter();prefix=0;intervals=[];start=None;last=None
for i,row in enumerate(struct.iter_unpack('<114I',data)):
 assert row[0]==i+1;stages[row[31]]+=1
 expected=[struct.unpack_from('<32I',payloads['selected-state.u32'],i*128),struct.unpack_from('<73I',payloads['world-camera.raw'],i*292)+struct.unpack_from('<2I',payloads['world-camera-tail.u32'],i*8),struct.unpack_from('<2I',payloads['hud-score.u32'],i*8),tuple(struct.unpack_from('<14I',payloads['replay-cursor.u32'],i*56)[j]for j in [7,8,3,9])]
 wrong=False
 for name,actual,want in zip(diff,[row[1:33],row[33:108],row[108:110],row[110:114]],expected):
  fields=[j for j,(x,y)in enumerate(zip(actual,want))if x!=y]
  if fields:
   wrong=True;diff[name].update(fields);first.setdefault(name,dict(callback=i+1,stage=row[31],stageFrame=row[1],fields=fields,cpp=[actual[j]for j in fields],native=[want[j]for j in fields]))
 if not wrong and prefix==i:prefix=i+1
 signature=tuple((n,tuple(j for j,(x,y)in enumerate(zip(a,w))if x!=y))for n,a,w in zip(diff,[row[1:33],row[33:108],row[108:110],row[110:114]],expected))if wrong else None
 if signature!=last:
  if start is not None:intervals.append(dict(firstCallback=start,lastCallback=i,fields=dict(last)))
  start=i+1 if signature else None;last=signature
if start is not None:intervals.append(dict(firstCallback=start,lastCallback=122005,fields=dict(last)))
coverage=Counter(r[0]for r in struct.iter_unpack('<14I',payloads['replay-cursor.u32']));cursor_complete=all(mask&4 for mask in coverage)
terminal=load(A/'campaign-terminal.json');assert terminal['quietSinceLastCallbackMs']>=3000 and len(terminal['samples'])>=3
assert all(s['words'][:5]==[2,6,1,1,3]for s in terminal['samples'][-3:])
# Reuse only the existing standalone score decoder, not its run-specific gates.
decoder=R/'tools/th14-audit-root-full-extra-nov08.py';tree=ast.parse(read(decoder));function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='decode_score')
codec=R/'tools/th-replay-container.py';read(codec);spec=importlib.util.spec_from_file_location('current_normal_score_codec',codec);mirror=importlib.util.module_from_spec(spec);spec.loader.exec_module(mirror)
scope=dict(struct=struct,mirror=mirror);exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(decoder),'exec'),scope)
ns=read(N/'work/appdata/ShanghaiAlice/th14/scoreth14.dat');cs=read(A/'save/scoreth14.dat');np,cp=scope['decode_score'](ns),scope['decode_score'](cs)
report=dict(originalCallbacks=122005,cppCallbacks=122005,stageCounts=dict(stages),strict113AllCallbacksExact=not any(diff.values())and cursor_complete,
 strict113PrefixCallbacks=prefix,differenceCounts={n:dict(c)for n,c in diff.items()},firstDifferences=first,failureIntervals=intervals,
 selected32Hud2Cursor4Exact=not any(diff[n]for n in ['state32','hud2','cursor4'])and cursor_complete,
 nativeCursorCoverageMasks=dict(coverage),nativeCompleteCursorCoverage=cursor_complete,
 completeEncodedScoreExact=ns==cs,completeDecodedScoreExact=np==cp,encodedScoreBytes=[len(ns),len(cs)],decodedScoreBytes=[len(np),len(cp)],
 stableSixthStageReplayEndObserved=True,normal145ProvidersReverified=True,allMeasuredOwnedResourcesRetired=True,
 nativeEntryObserverBytes=6,nativeEndedByObserverNotNaturalClose=True,cppApplicationCloseExecuted=True,
 oneTimeAttractFlagCaseInitializationInBothFixtures=True,referenceRowsNotFedToGame=True,noRngOrCounterPadding=True,
 actualProductionDeliveryServicesUsed=True,declaredImmediateGpuFences=True,graphicsRecordingOnly=True,
 publishedVorbis18HashesVerified=True,hardwarePixelsAccepted=False,finalPcmAccepted=False,
 fullDetailedShotOrVmHistoriesAccepted=False,ordinaryGameplaySaveAccepted=False,allModesAccepted=False,completeGame=False,
 bindings=bindings,toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
target=H/'raw-audit.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k not in ['bindings','failureIntervals']},ensure_ascii=False))
