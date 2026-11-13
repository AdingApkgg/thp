"""Audit ordinary menu recording, fresh title playback, and retained differences."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ordinary-replay-menu-nov13'
W=H/'write-c0-s1-d1-v2';P=H/'reopen-v1'
load=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
w,p=load(W/'report.json'),load(P/'report.json')
for directory,report in ((W,w),(P,p)):
 assert report['passed']and report['retired']and report['closed']and report['exception']is None and not report['errors']
 assert sha((directory/'executed-driver.mjs').read_bytes())==report['driverSha256']
 assert all(x['closed']and x['exitCode']==0 for x in report['physicalWorkers'])
 platform=load(directory/'platform.json');assert not platform['audibleOutput']
 assert not any(platform[k]for k in ['stream','window','context','pendingTimers','openFiles','liveDeclaredGpuFences'])
 assert not any(platform['liveObjects'].values())
data=(W/'save/replay/th14_01.rpy').read_bytes();saved=load(W/'saved-replay.json');assert sha(data)==saved['sha256']
assert data[:6]==b't13r\x02\x00'and struct.unpack_from('<I',data,12)[0]==len(data)
packed,unpacked=struct.unpack_from('<II',data,0x1c);assert packed+0x24==len(data)
spec=importlib.util.spec_from_file_location('replay_mirror',R/'tools/th-replay-container.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
decoded=codec.decode_with(data,packed,unpacked,codec.TH13);assert decoded is not None and len(decoded)==unpacked
assert decoded[:9]==b'A       \0'
assert struct.unpack_from('<4I',decoded,0x78)==(1,0,1,1)
start=0x94;stage,seed=struct.unpack_from('<HH',decoded,start);frames,payload=struct.unpack_from('<II',decoded,start+4)
assert stage==1 and struct.unpack_from('<I',decoded,start+0xd8)[0]==1
inputs=list(struct.iter_unpack('<3H',decoded[start+0xdc:start+0xdc+frames*6]));assert inputs[-1]==(65535,65535,65535)
previous=0
for held,pressed,released in inputs[:-1]:
 assert pressed==held&~previous and released==previous&~held
 previous=held
held_counts=Counter(x[0]for x in inputs[:-1]);assert all(held_counts[k]>=2 for k in [65,137,2])
assert len(decoded)==start+0xdc+payload and payload==frames*6+(frames-2)//30+1
live=list(struct.iter_unpack('<114I',(W/'observations.u32').read_bytes()));replay=list(struct.iter_unpack('<114I',(P/'observations.u32').read_bytes()))
assert len(live)==frames-1==344 and len(replay)==frames==345
differences=Counter(i for a,b in zip(live,replay)for i in range(1,33)if a[i]!=b[i])
assert differences==Counter({22:344,23:344})
assert all(a[108:110]==b[108:110]for a,b in zip(live,replay))
assert all(a[0]==i+1 for i,a in enumerate(live))and all(a[0]==i+1 for i,a in enumerate(replay))
terminal=load(P/'terminal-playback.json');assert terminal['end'][:5]==[2,1,1,1,3]and terminal['end'][14]==1
assert terminal['pause'][7:10]==[1,1,345]
(H/'saved-replay.decoded').write_bytes(decoded)
report=dict(passed=True,coreCommit='336a1ff0f9fdd197eba3ff5d8e7f94f1e31c34b4',
 actualOrdinaryGameplayAndPauseMenuSave=True,freshProcessTitleMenuReplaySelection=True,
 replayName='A',character=0,subtype=1,difficulty=1,stage=1,encodedBytes=len(data),decodedBytes=len(decoded),
 encodedSha256=sha(data),decodedSha256=sha(decoded),recordedFrames=frames-1,terminalMarkerFrames=1,
 allRecordedInputEdgesValidated=True,heldInputCounts=dict(held_counts),
 liveCallbacks=len(live),replayCallbacks=len(replay),matchedSelectedGameplayFieldsPerLiveCallback=30,
 gameplayRngSeedAndCounterMatch=True,hudScorePairMatch=True,
 retainedAnimationScriptRngDifferentRows=344,retainedAnimationScriptRngFields=[22,23],
 animationRngNotRestoredByInitialPlayback=True,animationVisualEqualityAccepted=False,
 forcedReplayEndMenuReached=True,allMeasuredWorkersDevicesAndTimersRetired=True,silent=True,
 graphicsRecordingOnly=True,originalWholeGamePlaybackOfThisNewFileAccepted=False,
 browserUiOrPersistenceAccepted=False,allModesOrLongReplayAccepted=False,completeGame=False)
(H/'qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
