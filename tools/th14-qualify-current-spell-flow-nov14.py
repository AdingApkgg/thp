from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/current-concurrent-mixer-nov14';O=H/'spell-practice-flow'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=load(O/'build.json');shortcut=load(O/'current-v5/report.json');writer=load(O/'natural-save-v2/report.json');saved=load(O/'natural-save-v2/saved-replay.json');reader_path=H/'replay-settings-gate/current-spell-replay-v1';reader=load(reader_path/'report.json');codec=load(O/'native-codec/report.json')
for report in [shortcut,writer,reader]:assert report['finished'] and report['retired'] and report['exception'] is None and not report['errors']
assert shortcut['moduleSha256']==writer['moduleSha256']==build['moduleSha256']==sha(O/'candidate.wasm')
assert sha(O/'natural-save-v2/spell-recording.rpy')==saved['sha256']==reader['inputSha256']==codec['inputSha256']
assert codec['passed'] and codec['actualRetailInstructionBodies'] and codec['allDecodedBytesEqualIndependentPythonMirror']
assert load(reader_path/'description.json')==saved['description']
assert saved['description']['mode']=='spell-practice' and saved['description']['stages']==[{'id':1,'score':0,'frames':590}]
decoded=(O/'native-codec/decoded.bin').read_bytes();assert decoded[10]&2 and struct.unpack_from('<i',decoded,0x90)[0]==3
assert decoded[0x170+589*6:0x170+590*6]==b'\xff'*6
def checkpoint(report,name):return next(c for c in report['checkpoints'] if c['label']==name)
for report in [shortcut,writer]:
 first=checkpoint(report,'spell-first-player');retry=checkpoint(report,'spell-retry-first-player');restored=checkpoint(report,'spell-selector-restored');ordinary=checkpoint(report,'ordinary-first-player')
 assert first['mode'][4]==retry['mode'][4]==restored['selector'][6]==3
 assert first['mode'][9:12]==retry['mode'][9:12]==[0,0,400]
 assert retry['behavior'][5]<first['behavior'][5]+60 and retry['behavior'][15]>first['behavior'][15]
 assert restored['selector'][4]==1 and restored['menu'][2]==1
 assert ordinary['mode'][1:5]==[1,0,0,0xffffffff] and ordinary['mode'][9:12]==[2,3,100]
 assert checkpoint(report,'unseen-row-remains-locked')['menu'][:3]==[18,2,0]
writer_state=saved['ended']['behavior'];reader_state=reader['outcome']['state'];indices=[1,2,3,4,5,6,7,8,9,10,11,12,13,16,17,18,19]
assert all(writer_state[i]==reader_state[i] for i in indices)
assert saved['ended']['mode'][9]==reader['outcome']['outcome'][2]==0xffffffff
assert reader['outcome']['viewer']==[1,589,590,1,2,1] and reader['outcome']['outcome'][0]==0
failures={}
reasons={'current-v1':'test assumed unseen Hard/Lunatic row was selectable with a Normal-earned save','current-v2':'test used the paused enum value for stage phase','current-v3':'test requested pause before the native 30-frame input gate','current-v4':'test expected direct selector return instead of title plus reentry','natural-save-v1':'test confused compact result save and title menu indices'}
for name,reason in reasons.items():
 p=O/name/'report.json';r=load(p);assert not r['finished'] and r['retired'] and r['exception'];failures[name]={'reportSha256':sha(p),'classification':'test-driver-assumption-corrected','reason':reason,'originalReportRetained':True}
q={'schema':'th14/current-spell-practice-flow/1','passed':True,'acceptanceStandard':'observable-behavior-alignment','moduleSha256':build['moduleSha256'],'gameSessionNormalizedSourceSha256':build['currentGameSessionNormalizedSha256'],'gameplayUnitsRecompiled':0,'verifiedProviderObjects':build['verifiedProviderObjects'],'earnedSaveSha256':writer['earnedSaveSha256'],'menuFlow':'earned save -> Reimu B Normal spell 3 -> pause retry -> title -> resume spell selector -> ordinary Normal','unseenRowRemainsLocked':True,'nativeShortcutRetryPreservesSpellAndResetsStocks':True,'retryPlayerCallbackAdvancedAndLocalClockReset':True,'titleReentryRestoresLoadoutRowAndDifficulty':True,'ordinarySpellIdCleared':True,'ordinaryInitialStocks':[2,3,100],'spellInitialStocks':[0,0,400],'naturalFailureResultMenuAccepted':True,'ordinarySaveInterfaceAccepted':True,'savedReplayBytes':saved['bytes'],'savedReplaySha256':saved['sha256'],'savedReplayMode':saved['description']['mode'],'spellId':3,'declaredReplayFrames':590,'naturalFailureControlFrame':589,'freshProcessReplayUiEnabled':False,'freshProcessReplayEndedNaturally':True,'freshProcessReplayComparedBehaviorIndices':indices,'freshProcessReplayComparedBehaviorWords':len(indices),'nativeCodec':codec,'currentFlowReportSha256':sha(O/'current-v5/report.json'),'naturalFailureReportSha256':sha(O/'natural-save-v2/report.json'),'freshReplayReportSha256':sha(reader_path/'report.json'),'correctedTestAssumptions':failures,'silentMemoryAudio':True,'graphicsRecordingOnly':True,'originalFullSpellPlayAccepted':False,'spellCaptureSuccessAccepted':False,'allSpellsOrLoadoutsAccepted':False,'browserAccepted':False,'productionChanged':False,'completeGame':False}
for p in [O/'qualified.json',R/'docs/porting/th14-current-spell-flow-nov14.json']:p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'normalStocksRestored':True,'savedReplayBytes':saved['bytes'],'freshReplayControlFrame':589,'matchedBehaviorWords':len(indices),'browserAccepted':False,'completeGame':False}))
