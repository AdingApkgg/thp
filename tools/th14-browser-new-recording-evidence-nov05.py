"""Bind a finite ordinary save/reload/play flow; publish no replay or raw seed."""
from pathlib import Path
import hashlib,json,struct

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/browser-new-recording-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()
bindings={}

def raw(path):
    path=path.resolve();assert path.is_relative_to(R)
    data=path.read_bytes()
    bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data))
    return data

def read(path):return json.loads(raw(path))

served=read(R/'artifacts/th14/browser-lifecycle-nov05/served-version.json')
assert served['verifiedCurrentServedVersion']
assert served['wasmSha256']=='4a8e02cc5d27c6fe13c3948fe750f9050d2a941421056a3f5b12bf745eedeca9'
packed=raw(H/'saved-slot02.rpy');decoded=raw(H/'saved-slot02-decoded.bin')
assert len(packed)==1240 and SHA(packed)=='ec04b9bea043c092e4f7b2fd18f379cb38419c5597ed7d640193fbefc344434a'
assert decoded[:8]==b'B       ' and decoded[8]==0
assert struct.unpack_from('<I',decoded,20)[0]==424
assert struct.unpack_from('<4I',decoded,0x78)==(1,0,1,1)
assert struct.unpack_from('<H',decoded,0x94)[0]==1
assert struct.unpack_from('<I',decoded,0x98)[0]==1294
codec=read(H/'native-replay-codec.json')
assert codec['passed'] and codec['files']==1
row,=codec['rows'];assert row['actualNativeCodecVerified']
assert row['sha256']==SHA(packed) and row['decodedSha256']==SHA(decoded)
assert row['nativeExecutableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert row['trailingBytes']==0 and [row[k] for k in ('character','subtype','difficulty')]==[0,1,1]
assert row['stages'][0]['frames']==1294
raw(H/'verify-codec.py');raw(H/'adapted-codec.py')
assert row['nativeCodecObserverSha256']==SHA(raw(R/'tools/th14-browser-saved-replay-native-codec-check.py'))

exports=[]
for name in ['th14_01.rpy','th14_02.rpy',*[f'th14_ud{i:04}.rpy' for i in range(4)]]:
    before=H/'saved-slot02.rpy' if name=='th14_02.rpy' else R/'artifacts/th14/browser-lifecycle-nov05'/('after-full-'+name)
    data=raw(H/('after-play-'+name));assert data==raw(before)
    exports.append(dict(name=name,bytes=len(data),sha256=SHA(data),byteIdenticalToBeforePlayback=True))
assert sum(row['bytes'] for row in exports)==420661

# These are operator observations from ordinary visible controls and screenshots,
# not a programmatic extraction of engine state or a pixel-equivalence assertion.
for name in ['live-game-over','save-slot-list-before','empty-slot02-selected','name-b-confirm','slot02-written',
    'reloaded-replay-list','new-replay-stage-list','new-replay-playing','new-replay-natural-end',
    'new-replay-stable-end','replay-quit-launcher','manager-not-open-after-second-quit',
    'reloaded-six-files','manager-after-two-title-quits']:
    assert raw(H/(name+'.jpg'))[:3]==bytes.fromhex('ffd8ff')
for name in ['new-replay-end-dom.txt','manager-not-open-dom.txt','manager-after-two-title-quits-dom.txt']:raw(H/name)
logs=read(H/'console.json')
known='emscripten_set_main_loop_timing: Cannot set timing mode for main loop since a main loop does not exist! Call emscripten_set_main_loop first to set one up.'
assert len(logs)==4 and all(row['message']==known for row in logs)

out=dict(schema='th14/browser-new-recording-public-evidence/1',
    verifiedOneActualBrowserOrdinaryNewSaveReloadAndPlay=True,
    wasmSha256=served['wasmSha256'],backend='gles',noOutputProbe=True,quietPreview=True,
    observationsSource='Operator-visible ordinary menus and local screenshot bindings; file and codec checks are executable assertions.',
    selection=dict(character='Reimu',subtype='B',difficulty='Normal',stage=1),
    recording=dict(slot=2,previouslyEmpty=True,name='B',bytes=len(packed),sha256=SHA(packed),
        declaredFrames=1294,browserCallbackCountRead=False,ordinaryCollisionsReachedGameOver=True,
        continueUsed=False,saveEntry='GameOver menu Save, directly to slot list',
        nameEditorDeleteAppendAndEndUsed=True,saveYesNoConfirmationObserved=False,
        naturalPlayEndObserved=True,fastForwardUsed=False,parentReloadBeforePlayback=True),
    selectedVisibleTerminalFields=dict(displayedScore=4240,lives=0,lifePieces='0/3',bombs=3,bombPieces='0/8',
        power='1.00',pointValue=10000,graze=11,matchedLiveGameOverAndStableReplayEnd=True),
    returnedReplayListAndOrdinaryQuit=True,
    codec=dict(actualOriginalMachineCode=True,decryptPc='0x4028e0',lzssPc='0x465840',
        controlledAllocatorCopyFreeBoundaries=True,allDecodedBytesEqualIndependentMirror=True,
        decodedNameAndSelectionAndScoreChecked=True,ordinaryOriginalGuiPlayback=False),
    replayExports=exports,allFiveOldFilesUnchanged=True,newFileUnchangedAfterReloadPlaybackAndQuit=True,
    exportedBytes=420661,
    retainedFailure=dict(managerDidNotOpenAfterReplayQuit=True,consoleNewFailureMessage=False,
        fullPageReloadRecovered=True,twoSubsequentTitleQuitManagerChecksPassed=True,
        rootCauseProven=False,fixed=False,completeManagerAcceptance=False),
    consoleKnownTimingMessages=4,consoleNewOtherWarnOrErrorMessages=0,consoleTimingMessageFixed=False,
    productionSourcesChanged=False,allSaveAndReplayPathsAccepted=False,allModesAccepted=False,
    originalWholeFrameOrPcmCompared=False,independentTimingEquivalent=False,
    completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,
    rawAssetsSeedsImagesReplaysScoresOrBinariesUploaded=False,evidenceBindings=bindings,
    toolSha256=SHA(Path(__file__).read_bytes()))
target=R/'docs/porting/th14-browser-new-recording-nov05.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(ordinaryNewSaveReloadAndPlayPassed=True,oldFilesUnchanged=5,newFileUnchanged=True,
    declaredFrames=1294,retainedManagerFailure=True,completeGame=False)))
