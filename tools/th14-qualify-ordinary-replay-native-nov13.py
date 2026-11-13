"""Compare the actual menu-saved file in retail and the independent Application."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ordinary-replay-native-nov13';N=H/'end-menu-preflight';P=R/'artifacts/th14/ordinary-replay-menu-nov13/reopen-v1'
load=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
n,p=load(N/'report.json'),load(P/'report.json');assert n['childExited']and n['childExitCode']==0 and not n['error']and p['passed']and p['retired']
assert n['callbacks']==345 and n['sourceFullReplaySha256']=='ce8c38538b730b049d04ea66962b61b514ece8be306a47d268677d1a68934720'
assert n['observedForcedReplayEndMenu']and len(n['terminalMenuSamples'])>=3
assert all(x['stage']==1 and x['callbacks']==345 for x in n['terminalMenuSamples'][-3:])
assert not n['debuggerAttached']and n['instructionBytesPatched']==6 and n['rngOrCounterWrites']==0
assert n['configuredMusicAndSoundVolumeZero']and not n['originalDiskFilesChanged']and not n['originalProcessNaturalExitClaimed']
assert n['caseInitialization']['attractBitClearOnly']
assert sha((N/'observer-source.py').read_bytes())==n['sourceSha256']
assert sha((P/'executed-driver.mjs').read_bytes())==p['driverSha256']
raw=(N/'selected-state.u32').read_bytes();assert sha(raw)==n['selectedSha256']and len(raw)==345*128
native=list(struct.iter_unpack('<32I',raw));cpp=list(struct.iter_unpack('<114I',(P/'observations.u32').read_bytes()));assert len(native)==len(cpp)==345
different=Counter(i for a,b in zip(native,cpp)for i in range(32)if a[i]!=b[i+1]);assert different==Counter({21:345,22:345})
hud=(N/'hud-score.u32').read_bytes();assert sha(hud)==n['hudScoreSha256']
assert list(struct.iter_unpack('<2I',hud))==[r[108:110]for r in cpp]
asset=load(R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-ce8c38538b73/manifest.json')
assert asset['passed']and asset['changedEntries']==['demo0.rpy']and asset['unchangedEntries']==226
result=dict(passed=True,actualRetailGameLoadedMenuSavedReplay=True,actualRetailAttractReplayHarness=True,
 originalWholeTitleMenuSelectionAccepted=False,nativeCallbacks=345,cppCallbacks=345,
 matchedSelectedStateFieldsPerCallback=30,gameplayRngSeedAndCounterMatch=True,hudScorePairMatch=True,
 retainedAnimationRngDifferentRows=345,retainedAnimationRngSelectedIndices=[21,22],
 full32FieldEquality=False,fullDetailedCombatOrVisualEqualityAccepted=False,
 actualStableForcedReplayEndMenuObserved=True,terminalSamples=3,nativeChildReaped=True,
 observerTerminatedAfterStableMenu=True,originalNaturalProcessExitClaimed=False,
 privateNativeTextObserverBytes=6,oneTimeAttractFlagInitialization=True,rngOrCounterWrites=0,
 debuggerAttached=False,originalGameDiskFilesChanged=False,silent=True,
 newArchiveBytes=asset['physicalNewArchiveBytes'],newExtractions=0,otherArchiveEntriesUnchanged=226,
 sourceReplaySha256=n['sourceFullReplaySha256'],nativeExecutableSha256=n['executableSha256'],
 nativeReportSha256=sha((N/'report.json').read_bytes()),cppReportSha256=sha((P/'report.json').read_bytes()),
 browserUiOrPersistenceAccepted=False,allModesOrLongReplayAccepted=False,completeGame=False)
(H/'qualified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
