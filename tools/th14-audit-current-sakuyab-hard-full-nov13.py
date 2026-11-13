"""Offline finite Hard behavior comparison; run only after Application exits."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/current-sakuyab-hard-full-nov13'
A=H/'full-campaign';N=R/'artifacts/th14/retail-sakuyab-hard-exit-boundary-hardware-oct26'
bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b
load=lambda p:json.loads(read(p))
cr=load(A/'report.json')
assert cr['terminal'] and cr['closed'] and cr['captureComplete'] and not cr['exception'] and not cr['errors']
assert not cr['referenceRowsReadDuringExecution'] and cr['graphicsRecordingOnly']
nr=load(N/'report.json')
assert nr['childExited'] and not nr['error'] and nr['observedForcedReplayEndMenu']
assert nr['instructionBytesPatched']==0 and nr['rngOrCounterWrites']==0 and nr['configuredMusicAndSoundVolumeZero']
assert nr['sourceFullReplaySha256']=='866bf6bac02e1c2b9067dacce6705dc71a512eeb2755106474be492a2d23dcdc'
count=nr['callbacks'];actual_count=cr['callbacks'];assert count==122811 and actual_count==122796
build=load(R/'artifacts/th14/native-viewer-application-nov13/component-v4/build.json')
assert hashlib.sha256(read(R/'artifacts/th14/native-viewer-application-nov13/component-v4/candidate.wasm')).hexdigest()==cr['wasmSha256']==build['outputs']['candidate']['wasmSha256']
for n,h in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():assert hashlib.sha256(read(R/n)).hexdigest()==h,n
assert len(build['objectBindings'])==145
assert hashlib.sha256(read(R/'tools/th14-run-current-sakuyab-hard-full-nov13.mjs')).hexdigest()==cr['driverSha256']
for key in ['workers','physicalWorkers']:
 for w in cr[key]:
  if key=='workers':assert w['returned'] and not w['error']
  else:assert w['closed'] and w['exitCode']==0
platform=load(A/'platform.json')
assert not any(platform[k]for k in ['stream','window','context','pendingTimers','openFiles','liveDeclaredGpuFences'])
assert not any(platform['liveObjects'].values()) and not platform['audibleOutput']
assert not platform['productionDelivery']['activeRestore'] and not platform['productionDelivery']['activeScene']
assert all(w['exited']and not w['error']for w in platform['productionDelivery']['workers'])
assert platform['ownedAsyncScheduled']==platform['ownedAsyncDelivered']
clock=cr['processClockResolution'];assert clock['beginCalls']==clock['endCalls']==1 and not clock['active']
selected=read(N/'selected-state.u32');hud=read(N/'hud-score.u32');actual=read(A/'observations.u32')
assert len(selected)==count*128 and hashlib.sha256(selected).hexdigest()==nr['selectedSha256']
assert len(hud)==count*8 and hashlib.sha256(hud).hexdigest()==nr['hudScoreSha256']
assert len(actual)==actual_count*456
native_rows=list(struct.iter_unpack('<32I',selected));native_hud=list(struct.iter_unpack('<2I',hud))
observed=list(struct.iter_unpack('<114I',actual));cpp_rows=[r[1:33]for r in observed];cpp_hud=[r[108:110]for r in observed]
assert all(r[0]==i+1 and r[28:31]==(2,1,2)for i,r in enumerate(observed))
raw_diff=Counter();raw_hud_diff=Counter();raw_first={}
for i,(n,c,nh,ch)in enumerate(zip(native_rows,cpp_rows,native_hud,cpp_hud)):
 for k,(a,b)in enumerate(zip(n,c)):
  if a!=b:raw_diff[k]+=1;raw_first.setdefault(str(k),dict(cppCallback=i+1,native=a,cpp=b))
 for k,(a,b)in enumerate(zip(nh,ch)):
  if a!=b:raw_hud_diff[k]+=1
native_zero=[i for i,r in enumerate(native_rows)if r[30]==6 and r[0]==0]
cpp_zero=[i for i,r in enumerate(cpp_rows)if r[30]==6 and r[0]==0]
assert len(native_zero)==135 and len(cpp_zero)==120 and native_zero[0]==cpp_zero[0]
for ids in [native_zero,cpp_zero]:assert ids==list(range(ids[0],ids[-1]+1))
extra=native_zero[len(cpp_zero):];assert extra==list(range(93573,93588))
# Diagnostic projection only. Keep all raw bytes, raw count failures and these
# explicit unmatched callback identities; never alter the engine or its input.
extra_set=set(extra);mapping=[i for i in range(count)if i not in extra_set];assert len(mapping)==actual_count
diag_diff=Counter();diag_first={};diag_hud=Counter();outside=Counter();hud_frames=[]
gameplay=set(range(21))|set(range(25,32))
for ci,ni in enumerate(mapping):
 n,c=native_rows[ni],cpp_rows[ci];window=c[30]==6 and 1<=c[0]<=30
 for k,(a,b)in enumerate(zip(n,c)):
  if a!=b:
   diag_diff[k]+=1;diag_first.setdefault(str(k),dict(nativeCallback=ni+1,cppCallback=ci+1,stage=c[30],frame=c[0],native=a,cpp=b))
   if k in gameplay and not window:outside[k]+=1
 for k,(a,b)in enumerate(zip(native_hud[ni],cpp_hud[ci])):
  if a!=b:diag_hud[k]+=1;hud_frames.append((c[30],c[0],k))
assert not outside
assert not any(k in diag_diff for k in range(12,21))
assert not diag_hud[1]
transition=[r for r in cpp_rows if r[30]==6 and 1<=r[0]<=30]+[native_rows[i]for i in extra]
transition_enemy_range=[min(r[25]for r in transition),max(r[25]for r in transition)]
transition_shot_range=[min(r[26]for r in transition),max(r[26]for r in transition)]
assert len(hud_frames)==57 and all(2<=s<=6 and f==0 and k==0 for s,f,k in hud_frames)
hud_stage_counts=dict(Counter(s for s,f,k in hud_frames))
terminal=load(A/'campaign-terminal.json');samples=terminal['samples'];assert len(samples)>=3 and terminal['quietSinceLastCallbackMs']>=3000
native_terminal=nr['terminalMenuSamples'][-1]
for sample in samples[-3:]:
 w=sample['words'];assert w[:5]==[2,6,1,1,3]and w[6:9]==[1,1,5]and w[9]==3 and w[16]==1
 assert native_terminal['forcedExit']==w[6]and native_terminal['cursor']==w[7]and native_terminal['menuCount']==w[8]
assert native_rows[-1][12]==cpp_rows[-1][12]==151106314
j=dict(integrityAuditPassed=True,originalCallbacks=count,cppCallbacks=actual_count,
 loadout='Sakuya B',difficulty='Hard',
 nativeStageCounts=dict(Counter(r[30]for r in native_rows)),cppStageCounts=dict(Counter(r[30]for r in cpp_rows)),
 rawCallbackSequenceExact=False,raw32Differences=dict(raw_diff),rawHud2Differences=dict(raw_hud_diff),rawFirstDifferences=raw_first,
 additionalNativeControlFrameZeroCallbacks=[i+1 for i in extra],nativeStage6ZeroFrameRows=135,cppStage6ZeroFrameRows=120,
 diagnosticProjectionOnly=True,rawRowsNeverRewritten=True,
 diagnostic32Differences=dict(diag_diff),diagnosticFirstDifferences=diag_first,diagnosticHud2Differences=dict(diag_hud),
 diagnosticMeasured28GameplayFieldsExactOutsideStage6Frames1To30=True,
 diagnosticScoreGrazePowerLifeBombAndRankWordsExact=True,transitionEnemyCountRange=transition_enemy_range,transitionPlayerShotCountRange=transition_shot_range,
 hudDisplayDifferences=57,hudDisplayDifferenceControlFrame=0,hudDisplayDifferencesByStage=hud_stage_counts,globalHudScoreWordExact=True,
 animationRngDifferencesRetained=True,completeReplayFlowReachedNativeForcedMenu=True,
 selectedPreCompletionScoreUnits=151106314,originalTerminalPostAwardScoreUnits=native_terminal['score'],cppTerminalPostAwardScoreCaptured=False,
 terminalPauseMenuShapeMatchesNative=True,allMeasuredOwnedResourcesRetired=True,silent=True,
 startupClockProfileFromNormalCase=True,sourceClockOrRngMatchedToHardReference=False,
 referenceRowsFedToGame=False,graphicsRecordingOnly=True,actualGpuAccepted=False,
 allComparedStatesIdentical=False,fullDetailedBulletsAccepted=False,ordinaryClearOrUnlockAccepted=False,
 allModesAccepted=False,completeGame=False,bindings=bindings)
target=H/'raw-audit.json';assert not target.exists();target.write_text(json.dumps(j,indent=2)+'\n')
print(json.dumps({k:v for k,v in j.items()if k not in ['bindings','rawFirstDifferences','diagnosticFirstDifferences']},indent=2))
