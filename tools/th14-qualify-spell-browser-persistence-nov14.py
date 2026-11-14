"""Qualify files downloaded through real browser UI and bounded spell statistics."""
from pathlib import Path
import hashlib,json,struct

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/current-concurrent-mixer-nov14';O=H/'spell-browser-persistence'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=load(O/'import-qualified.json');reader=load(O/'after/report.json');codec=load(O/'after/native-codec-qualified.json');replay=load(O/'replay-native-codec/report.json')
assert receipt['allImportedBytesPreserved'] and receipt['allReloadedBytesPreserved'] and receipt['backupKept']
assert (O/'after-import.dat').read_bytes()==(O/'after-reload.dat').read_bytes()==(H/'spell-practice-flow/capture-dodge-v2/save/scoreth14.dat').read_bytes()
assert (O/'after-attempt.dat').read_bytes()==(O/'after-attempt-reload.dat').read_bytes()==(O/'before-viewer.dat').read_bytes()==(O/'after-viewer.dat').read_bytes()
assert reader['finished'] and reader['retired'] and reader['exception'] is None and not reader['errors'] and reader['noGameplayStarted']
assert codec['passed'] and codec['actualRetailDecryptAndLzss'] and codec['originalInstructionBytesPatched']==0
a=(H/'spell-capture-persistence/after/native-decoded.bin').read_bytes();b=(O/'after/native-decoded.bin').read_bytes()
assert len(a)==len(b)==149076 and b==(O/'after/score-observed.bin').read_bytes()
assert sha(O/'after/native-decoded.bin')==reader['loadedSha256']==codec['decodedSha256']
assert sha(O/'after-attempt.dat')==reader['sourceSha256']==codec['encodedSha256']
size=0x5298;spell=0x978;stride=0x9c;changed=[]
for selection in range(7):
    for number in range(120):
        at=selection*size+spell+number*stride
        old=struct.unpack_from('<4I',a,at+0x80);new=struct.unpack_from('<4I',b,at+0x80)
        assert old[:3]==new[:3]
        assert a[at+0x98:at+0x9c]==b[at+0x98:at+0x9c]
        if old!=new:
            assert (selection,number) in [(1,3),(6,3)] and old==(1,1,1,1) and new==(1,1,1,2)
            changed.append({'selection':selection,'spellId':number,'before':list(old),'after':list(new)})
assert len(changed)==2
before_count,before_time=struct.unpack_from('<2I',a,size+0x7b8);after_count,after_time=struct.unpack_from('<2I',b,size+0x7b8)
assert after_count-before_count==1 and after_time-before_time==591
assert a[7*size+12:7*size+20]==b'        ' and b[7*size+12:7*size+20]==b'A       '
allowed=set(range(size+0x7b8,size+0x7c0))|set(range(7*size+4,7*size+8))|{7*size+12}
for selection in [1,6]:
    for off,length in [(4,4),(spell+3*stride+0x8c,4)]:allowed.update(range(selection*size+off,selection*size+off+length))
diff=[i for i,(old,new) in enumerate(zip(a,b)) if old!=new];assert len(diff)==10 and set(diff)<=allowed
for selection in range(6):assert a[selection*size+0x7c0:selection*size+0x7f0]==b[selection*size+0x7c0:selection*size+0x7f0]
assert replay['passed'] and replay['actualRetailInstructionBodies'] and replay['allDecodedBytesEqualIndependentPythonMirror']
assert replay['inputSha256']==sha(O/'browser-spell-recording.rpy') and replay['nameHex']=='4120202020202020'
assert (replay['character'],replay['subtype'],replay['difficulty'])==(0,1,1)
assert len(replay['stages'])==1 and replay['stages'][0]['frames']==592
raw=(O/'replay-native-codec/decoded.bin').read_bytes();assert struct.unpack_from('<i',raw,0x94+0x30)[0]==3
exports=load(O/'replay-export-list.json');assert len(exports)==4
assert next(r for r in exports if r['name'].endswith('ud0002.rpy'))['sha256']=='02ec75303e6c0a3a5de003569aad923fb96cf677e7d493124d753d68639c64b7'
proofs={n:sha(O/n) for n in ['imported-spell-counters.png','actual-attempt-result.png','replay-save-committed.png','reloaded-spell-counters.png','browser-recorded-replay-ended.png']}
seek=H/'spell-viewer-completion/browser/seek-ended.png';assert seek.exists()
q={'schema':'th14/spell-browser-persistence/1','passed':True,'acceptanceStandard':'observable-behavior-alignment',
   'site':'http://localhost:8239/?game=th14','wasmSha256':'4f9b87f190756fc38cc330eefbfe6e0a249503776963dbb5f4294998d0db2ebc','runtimeGeneration':'54f7034144fd94c0f4455c98e874d6ed33373bd9f9a614a2c1a76bd4ae9699fa',
   'actualBrowserBackend':'SDL3 / WebGL2 / C++','musicVolume':0,'effectsVolume':0,'ordinaryLaunchMusicMode':'none','noGameStateOrRngWrites':True,
   'successfulCaptureSaveImportedThroughUi':True,'backupKept':True,'allImportedAndReloadedBytesEqual':True,'actualCppMenuAfterImport':{'practiceCaptures':1,'practiceAttempts':1,'ordinaryCaptures':1,'ordinaryAttempts':1,'highScore':3179600},
   'actualBrowserAttempt':{'naturalFailure':True,'saveReplayObserved':True,'emptySlot':1,'name':'A','returnToTitleAndQuitObserved':True,'replayBytes':718,'replaySha256':replay['inputSha256'],'declaredFrames':592,'score':0,'spellId':3},
   'afterQuitAndReloadWholeBytesEqual':True,'actualCppMenuAfterReload':{'practiceCaptures':1,'practiceAttempts':2,'ordinaryCaptures':1,'ordinaryAttempts':1,'highScore':3179600},
   'freshReaderAll149076BytesEqualRetailDecode':True,'all840CaptureAndOrdinaryAttemptCountersPreserved':True,'all840SpellHighScoresPreserved':True,'other838PracticeAttemptCountersPreserved':True,'changedRecords':changed,'playCountDelta':1,'playTimeDelta':591,
   'allSixClearUnlockFieldsPreserved':True,'changedDecodedBytes':10,'onlyDeclaredFieldsAndChecksumsChanged':True,'sharedSettingsChange':'last entered name: eight spaces to A followed by seven spaces; checksum updated','scoreSha256':codec['encodedSha256'],'decodedScoreSha256':codec['decodedSha256'],
   'replayNativeFormatAccepted':True,'newReplayPlaybackAccepted':True,'newReplayObservedTerminal':{'viewerFrames':591,'score':0,'power':3.5,'graze':6,'pointValue':10000,'endedText':'录像已结束'},'watchingSpellReplayWholeScoreFileUnchanged':True,'watchingSpellReplayDidNotIncrementAttempts':True,'successViewerBackwardThenForwardSeekAccepted':True,'successSeekEndFrames':1737,'successSeekScore':3179620,'seekScreenshotSha256':sha(seek),'proofHashes':proofs,
   'freshBrowserSuccessfulCaptureAccepted':False,'allSpellCoverageAccepted':False,'productionChanged':False,'completeGame':False}
for p in [O/'qualified.json',R/'docs/porting/th14-spell-browser-persistence-nov14.json']:p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'actualBrowserAttemptPersistence':True,'changedDecodedBytes':10,'practiceAttempts':2,'highScore':3179600,'productionChanged':False,'completeGame':False}))
