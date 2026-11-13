"""Independent checkpoint audit, preserving failed fixtures and scope limits."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/behavior-matrix-nov13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
ordinary=load(H/'matrix-report.json');assert ordinary['passed']and ordinary['completed']==24
build=load(H/'component/build.json')
for n,h in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():assert sha(R/n)==h,n
assert len(build['objectBindings'])==145
rows=[];bindings={};all_cases=list(ordinary['cases'])
extra_path=H/'extra-matrix-report.json'
if extra_path.exists():
 extra=load(extra_path);assert extra['passed']and extra['completed']==6;all_cases+=extra['cases']
for row in all_cases:
 p=H/row['path'];j=load(p/'report.json');assert sha(p/'report.json')==row['reportSha256']
 assert j['passed']and j['retired']and j['terminal']and not j['exception']and not j['errors']
 assert j['sourceWasmSha256']==build['outputs']['candidate']['wasmSha256']
 assert sha(p/'executed-driver.mjs')==j['driverSha256']
 points={v['name']:v for v in j['checkpoints']}
 for n in ['fast-shoot','slow-shoot','wait-pause','paused','resume-release','wait-resume','bomb-key','bomb-running','passed']:assert n in points,n
 s=lambda n:points[n]['state'];signed=lambda x:x if x<0x80000000 else x-0x100000000
 expected_stage=7 if row['difficulty']==4 else 1
 assert s('passed')[1:5]==[expected_stage,row['character'],row['subtype'],row['difficulty']]
 initial,fast,slow=map(s,['fast-shoot','slow-shoot','wait-pause'])
 dx_fast=signed(initial[6])-signed(fast[6]);dx_slow=signed(slow[6])-signed(fast[6])
 assert dx_fast>dx_slow>0 and slow[12]==1 and j['maxActiveProjectiles']>0
 paused,resume=s('paused'),s('resume-release');assert paused[0]==resume[0]==2 and paused[14]==3
 assert paused[5]==resume[5]and paused[15]==resume[15]
 assert points['resume-release']['frame']-points['paused']['frame']>=20
 assert s('bomb-key')[0]==s('passed')[0]==1 and s('bomb-key')[15]>paused[15]+4
 assert s('passed')[9]==s('bomb-key')[9]-1 and j['bombObserved']
 if row['difficulty']==1:assert j['bombFinished']and s('passed')[10]==0
 platform=load(p/'platform.json');assert not platform['audibleOutput']
 assert not any(platform[k]for k in ['stream','window','context','pendingTimers','openFiles','liveDeclaredGpuFences'])
 assert not any(platform['liveObjects'].values())
 assert platform['ownedAsyncScheduled']==platform['ownedAsyncDelivered']
 assert not platform['productionDelivery']['activeScene']and not platform['productionDelivery']['activeRestore']
 clock=load(p/'process-clock.json');assert not clock['active']and clock['beginCalls']==clock['endCalls']==1
 assert all(w['returned']and not w['error']for w in j['workers'])and all(w['closed']and w['exitCode']==0 for w in j['physicalWorkers'])
 rows.append(dict(character=row['character'],subtype=row['subtype'],difficulty=row['difficulty'],stage=expected_stage,
  fastMovement=dx_fast,focusedMovement=dx_slow,maxProjectiles=j['maxActiveProjectiles'],bombFinished=j['bombFinished'],passed=True))
 for name in ['report.json','plan.json','platform.json','process-clock.json','executed-driver.mjs']:bindings[(p/name).relative_to(R).as_posix()]=sha(p/name)
old=load(H/'c0-s0-d1/report.json');assert not old['passed']and old['retired']and old['phase']=='fast-shoot'
report=dict(ordinaryCases=24,extraCases=len(rows)-24,allDeclaredCasesPassed=True,rows=rows,
 actualApplicationAnd145NormalProviders=True,selectionByOrdinaryMenuKeys=True,shootMoveFocusPauseAndBombVerified=True,
 sixNormalBombLifetimesComplete=True,twentyPausedFramesFrozenPerCase=True,originalUserSaveUnchanged=True,
 extraUsesControlledExternalUnlockedSave=extra_path.exists(),unlockEarnedByOrdinaryPlayAccepted=False,
 originalAllModeBehaviorCompared=False,fullStagesOrAllDetailedShotStatesAccepted=False,hardwareVisualsAccepted=False,
 audibleOutput=False,allMeasuredOwnedResourcesRetired=True,invalidLifeStateZeroFixtureRejectedAndRetained=True,
 productionSourceChanged=False,completeGame=False,bindings=bindings)
name='qualified-30.json'if len(rows)==30 else'qualified-24.json';assert not(H/name).exists()
(H/name).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['rows','bindings']}))
