"""Qualify bounded real-input spell capture, persistence and viewer regressions."""
from pathlib import Path
import hashlib,json,struct

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-concurrent-mixer-nov14'
O=H/'spell-viewer-completion'
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=load(O/'build.json');layout=load(O/'layout-qualified.json')
assert build['compiled'] and layout['passed']
assert sha(O/'candidate.wasm')==build['sha256']
cases=['completion-capture-v2','completion-capture-ui-on-v1','completion-failure-v1','completion-practice-v1','completion-ordinary-v1','completion-native-return-v1']
reports={n:load(H/'replay-settings-gate'/n/'report.json') for n in cases}
for n,r in reports.items():
    assert r['finished'] and r['retired'] and r['exception'] is None and not r['errors'],n
    assert r['wasmSha256']==build['sha256'] and r['silentMemoryAudioBackend']
old=load(H/'replay-settings-gate/current-spell-capture-replay-v2/report.json')
assert not old['finished'] and old['retired'] and 'escaped to title' in old['exception']
assert old['inputSha256']==reports[cases[0]]['inputSha256']
writer=load(H/'spell-practice-flow/capture-dodge-v2/report.json')
assert writer['finished'] and writer['retired'] and writer['exception'] is None
capture=load(H/'spell-practice-flow/capture-dodge-v2/capture-result.json')
assert capture['ownPracticeCaptures']==capture['ownPracticeAttempts']==1
assert capture['ownSpellHigh']==317960
fresh=load(H/'spell-capture-persistence/after/report.json')
codec=load(H/'spell-capture-persistence/after/native-codec-qualified.json')
assert fresh['finished'] and fresh['retired'] and fresh['noGameplayStarted']
assert fresh['exception'] is None and not fresh['errors']
assert codec['passed'] and codec['actualRetailDecryptAndLzss'] and codec['originalInstructionBytesPatched']==0
before=(H/'spell-score-persistence/before/native-decoded.bin').read_bytes()
after=(H/'spell-capture-persistence/after/native-decoded.bin').read_bytes()
assert after==(H/'spell-capture-persistence/after/score-observed.bin').read_bytes()
assert len(before)==len(after)==149076
assert hashlib.sha256(after).hexdigest()==fresh['loadedSha256']==codec['decodedSha256']
size=0x5298;spell=0x978;stride=0x9c;changed=[]
for selection in range(7):
    for number in range(120):
        at=selection*size+spell+number*stride
        a=struct.unpack_from('<4I',before,at+0x80);b=struct.unpack_from('<4I',after,at+0x80)
        assert a[0]==b[0] and a[2]==b[2]
        expected=317960 if (selection,number)==(1,3) else struct.unpack_from('<I',before,at+0x98)[0]
        assert struct.unpack_from('<I',after,at+0x98)[0]==expected
        if a!=b:
            assert (selection,number) in [(1,3),(6,3)] and a==(1,0,1,0) and b==(1,1,1,1)
            changed.append({'selection':selection,'spell':number,'before':list(a),'after':list(b)})
assert len(changed)==2
assert struct.unpack_from('<2I',after,size+0x7b8)==(2,123371)
assert struct.unpack_from('<2I',before,size+0x7b8)==(1,121635)
allowed=set(range(size+0x7b8,size+0x7c0))
for selection in [1,6]:
    for off,length in [(4,4),(spell+3*stride+0x84,4),(spell+3*stride+0x8c,4)]:
        allowed.update(range(selection*size+off,selection*size+off+length))
allowed.update(range(size+spell+3*stride+0x98,size+spell+3*stride+0x9c))
diff=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
assert len(diff)==13 and set(diff)<=allowed
assert before[7*size:]==after[7*size:]
for selection in range(6):
    assert before[selection*size+0x7c0:selection*size+0x7f0]==after[selection*size+0x7c0:selection*size+0x7f0]
q={'schema':'th14/spell-viewer-completion/1','passed':True,'acceptanceStandard':'observable-behavior-alignment','wasmSha256':build['sha256'],
   'sourceBefore':build['sourceBefore'],'sourceAfter':build['sourceAfter'],'layout':layout,
   'originalFailure':{'reportSha256':sha(H/'replay-settings-gate/current-spell-capture-replay-v2/report.json'),'exception':old['exception'],'inputSha256':old['inputSha256']},
   'regressions':{n:{k:r[k] for k in ['enabled','finished','retired','exception','outcome','inputSha256']} for n,r in reports.items()},
   'capture':{'spellId':3,'selection':1,'difficulty':1,'controlFrames':1736,'declaredReplayFrames':1737,'score':3179620,'storedHighScoreUnits':317960,'actualInputOnly':True,'gameplayStateOrRngWrites':False},
   'persistence':{'freshReaderNeverStartedGameplay':True,'all149076BytesEqualToRetailDecodedSave':True,'changedSpellCounters':changed,'changedBytes':13,'ordinaryCountersAndOther838PracticeCountersPreserved':True,'other839SpellHighScoresPreserved':True,'playCountDelta':1,'playTimeDelta':1736,'settingsAndClearUnlockFieldsPreserved':True,'sourceSha256':fresh['sourceSha256'],'decodedSha256':fresh['loadedSha256']},
   'silentMemoryAudio':True,'graphicsRecordingOnly':True,'browserGpuAccepted':False,'nativeReplayMenuUiAccepted':False,'viewerCloseUsesExistingPublicApi':True,'productionChanged':False,'completeGame':False}
for p in [O/'qualified.json',R/'docs/porting/th14-spell-viewer-completion-nov14.json']:
    p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'regressions':len(reports),'decodedChangedBytes':13,'productionChanged':False,'completeGame':False}))
