"""Bind actual visible browser flows and exported files without uploading them."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/browser-lifecycle-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def raw(path):
    path=path.resolve();assert path.is_relative_to(R)
    data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
def read(path):return json.loads(raw(path))
flow=read(H/'flow-receipt.json');served=read(H/'served-version.json');metadata=read(H/'exported-replay-metadata.json')
assert served['verifiedCurrentServedVersion']and served['wasmSha256']==flow['wasmSha256']=='4a8e02cc5d27c6fe13c3948fe750f9050d2a941421056a3f5b12bf745eedeca9'
assert flow['noOutputProbe']and flow['quietParentAndIframe']
full=flow['fullReplay'];assert full['stagesVisuallyObserved']==[1,2,3,4,5,6]and full['naturalEndObserved']and full['stableEndObserved']
assert full['returnedReplayList']and full['ordinaryQuitReturnedLauncher']and full['parentReloadBeforeLaunch']and full['parentReloadAfterQuit']
rows=[]
for row in metadata['files']:
    before=raw(R/row['path']);after_path=H/Path(row['path']).name.replace('exported-','after-full-');after=raw(after_path)
    assert before==after and len(before)==row['bytes'] and SHA(before)==row['sha256']
    rows.append(dict(name=after_path.name.replace('after-full-',''),bytes=len(after),sha256=SHA(after),unchangedAfterFullReplayQuitAndReload=True))
assert len(rows)==5
replay=next(row for row in metadata['files']if row['path'].endswith('th14_ud0002.rpy'))
assert replay['sha256']==full['sourceSha256']=='c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74'
assert [replay[k]for k in ['character','subtype','difficulty','totalFrames']]==[0,1,1,122385]
assert [s['stage']for s in replay['stages']]==[1,2,3,4,5,6]
for name in ['replay-list-existing','replay-playing','replay-natural-end','replay-again-end','replay-return-list','replay-quit-launcher',
    'full-normal-stage-list','full-normal-start',*[f'full-normal-fast-{i:02}'for i in range(1,13)],
    'full-normal-stable-end','full-normal-return-list','full-normal-quit-launcher','after-full-reload-manager']:
    assert raw(H/(name+'.jpg'))[:3]==bytes.fromhex('ffd8ff')
for name in ['replay-end-dom.txt','full-normal-stable-end-dom.txt','after-full-manager-dom.txt']:raw(H/name)
expected='emscripten_set_main_loop_timing: Cannot set timing mode for main loop since a main loop does not exist! Call emscripten_set_main_loop first to set one up.'
logs=read(H/'console-after-full.json');assert len(logs)==2 and all(row['message']==expected for row in logs)
native_proof=read(R/'docs/porting/th14-beam-cookie-and-terminal-hud-verified-oct23.json');assert native_proof['verified']
binding=next(row for row in native_proof['evidenceBindings']if row['path'].endswith('retail-reimub-full-hud-menu-hardware-oct23/report.json'))
data=raw(R/binding['path']);assert len(data)==binding['bytes'] and SHA(data)==binding['sha256']
native=json.loads(data);assert native['realOriginalWindowsProcess'] and native['observedForcedReplayEndMenu']and not native['debugErrors']
assert native['instructionBytesPatched']==0 and native['rngOrCounterWrites']==0
assert len(native['terminalMenuSamples'])==3
assert all(row['hudSidebarDisplayedScore']*10==full['displayedScore']and row['lives']==full['displayedLives']for row in native['terminalMenuSamples'])
score=read(H/'score-codec-retry1/verified.json');native_codec=read(H/'score-codec-retry1/original/native.json')
assert score['verifiedActualBrowserExportScoreCodec']and score['allProductionDecodedBytesEqualOriginal']and score['completeEncodedRoundtripEqual']
packed=raw(H/'after-full-save-export.dat');assert len(packed)==score['sourceBytes']==21647 and SHA(packed)==score['sourceSha256']==native_codec['inputSha256']
assert raw(H/'score-codec-retry1/production.raw')==raw(H/'score-codec-retry1/original/retail-loaded.raw')
assert raw(H/'score-codec-retry1/original/retail-rewritten.dat')==packed
base=read(R/'artifacts/th14/script-rng-read-generation-nov05/portable-audit-build/observer-build.json')
for name,digest in base['headerHashes'].items():assert SHA(raw(Path(base['sourceSnapshotRoot'])/name))==digest
for row in score['objectsReused']:assert SHA(raw(Path(row['path'])))==row['sha256']
raw(H/'check-score.py');raw(H/'inspect-exported.py');raw(H/'check-served.py')
out=dict(schema='th14/browser-lifecycle-public-evidence/1',verifiedOneActualBrowserFullReplayFlow=True,
    wasmSha256=flow['wasmSha256'],backend='gles',noOutputProbe=True,quietPreview=True,
    sourceReplaySha256=replay['sha256'],selection='ReimuB Normal',declaredReplayFrames=122385,
    browserCallbackCountRead=False,stagesVisuallyObserved=[1,2,3,4,5,6],productionReplayFastForwardKeyUsed=True,
    originalHostClocksOrRngValuesProvidedToEngine=False,naturalAndStableEndObserved=True,
    selectedVisualTerminalFields=dict(displayedScore=full['displayedScore'],lives=full['displayedLives'],matchRetainedOriginalTerminalObservations=True),
    browserInternalEconomyScoreRead=False,originalWholeFrameOrPcmCompared=False,
    returnedReplayListAndOrdinaryQuit=True,parentReloadBeforeAndAfterFullRun=True,replayExports=rows,
    allFiveReplayFilesByteIdenticalAfterFullReplayQuitAndReload=True,
    scoreCodec=dict(browserExportBytes=21647,decodedBytes=149076,allDecodedBytesEqualOriginal=True,encodedRoundtripEqual=True,
        loaderPc='0x456de0',writerPc='0x456f60',controlledEmulatorCrtBoundaries=True,ordinaryOriginalFilesystemTest=False,
        scoreBeforeFullRunNotExported=True),
    shortReplayFlow=flow['shortReplay'],selectedFieldsRecordedByOperatorFromVisibleScreenshots=True,
    knownConsoleTimingMessages=2,newOtherWarnOrErrorMessages=0,consoleTimingMessageFixed=False,
    productionSourcesChanged=False,allModesAccepted=False,independentTimingEquivalent=False,completeBrowserAcceptance=False,
    completeGame=False,nativeEquivalent=False,rawAssetsImagesReplaysScoresOrBinariesUploaded=False,
    evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))
target=R/'docs/porting/th14-browser-lifecycle-nov05.json';target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(verifiedOneActualBrowserFullReplayFlow=True,stages=[1,2,3,4,5,6],unchangedReplayFiles=5,
    originalScoreCodecDecodedBytes=149076,knownConsoleTimingMessages=2,completeGame=False)))
