"""Qualify natural deaths and the ordinary Continue path, without injected hits."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ordinary-replay-menu-nov13/death-continue-c0-s1-d1-v4'
load=lambda p:json.loads(p.read_bytes())
r=load(H/'report.json');assert r['passed']and r['retired']and r['closed']and r['phase']=='passed'and r['exception']is None
assert not r['errors']and all(w['closed']and w['exitCode']==0 for w in r['physicalWorkers'])
assert hashlib.sha256((H/'executed-driver.mjs').read_bytes()).hexdigest()==r['driverSha256']
platform=load(H/'platform.json');assert not platform['audibleOutput']and not any(platform['liveObjects'].values())
assert not any(platform[k]for k in ['stream','window','context','pendingTimers','openFiles','liveDeclaredGpuFences'])
stock=[x['state'][19]for x in r['checkpoints']if x['name']=='life-stock-change'];assert stock==[1,0,0xffffffff]
game_over=next(x for x in r['checkpoints']if x['name']=='game-over')['state'];assert game_over[0]==3 and game_over[19]==0xffffffff
tail=next(x for x in r['checkpoints']if x['name']=='continue-respawn-tail')['state'];assert tail[0]==1 and tail[19]==2 and tail[9]==3
pause=load(H/'continue-pause.json');s=pause['behavior'];end=pause['end']
assert s[0]==2 and s[1:5]==[1,0,1,1]and s[8]==1 and s[9]==3 and s[18]==400 and s[19]==2
assert s[5]>game_over[5]and end[9]==1
rows=list(struct.iter_unpack('<114I',(H/'observations.u32').read_bytes()));assert len(rows)>1300
assert all(x[2]==0 for x in rows), 'neutral input during active ordinary play'
first_continued=next(x for x in rows if x[1]>game_over[5]and x[17]==2)
assert first_continued[16]==400 and first_continued[19]==2 and first_continued[109]==0
assert rows[-1][16]==400 and rows[-1][17]==2 and rows[-1][19]==3
result=dict(passed=True,coreCommit='336a1ff0f9fdd197eba3ff5d8e7f94f1e31c34b4',
 naturalBulletDamage=True,ordinaryGameOverAndContinue=True,damageHealthLivesOrEconomyInjected=False,
 lifeStockSequence=[2,1,0,-1,2],gameOverControlFrame=game_over[5],continuedControlFrame=s[5],
 continuedStage=1,stageClockNotRestarted=True,continuedActiveLives=2,continuedActiveBombs=3,continuedPower=400,
 firstContinuedPlayerCallback=first_continued[0],firstContinuedBombs=2,firstContinuedGlobalScore=0,
 lastObservedGlobalScore=rows[-1][109],continuedPauseDisabledChoices=1,returnedToTitle=True,
 callbacks=len(rows),allActiveGameplayHeldInputsNeutral=True,allMeasuredResourcesRetired=True,silent=True,
 originalNativeContinueForThisCaseCompared=False,fullRankingOrUnlockProgressionAccepted=False,
 graphicsRecordingOnly=True,browserUiAccepted=False,completeGame=False,
 retainedFailures=['v2: assumed internal two-bomb continue value survived respawn','v3: attempted transient two-bomb assertion after the death callback already completed'])
(H.parent/'natural-death-continue-qualified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
