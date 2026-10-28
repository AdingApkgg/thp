"""Bind actual browser UI observations, score roundtrip and retained failures.

This verifies saved artifacts. It does not drive the browser again or promote
finite UI checks, a codec component or the worker prototype to whole-game fidelity.
"""
from pathlib import Path
import argparse,hashlib,json,struct

R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def jpeg_dimensions(raw):
    assert raw[:2]==b'\xff\xd8'
    cursor=2
    while cursor<len(raw):
        assert raw[cursor]==255
        while raw[cursor]==255:cursor+=1
        marker=raw[cursor];cursor+=1
        if marker in (1,*range(0xd0,0xda)):continue
        length=struct.unpack_from('>H',raw,cursor)[0]
        assert length>=2 and cursor+length<=len(raw)
        if marker in (0xc0,0xc1,0xc2):
            height,width=struct.unpack_from('>2H',raw,cursor+3);return width,height
        cursor+=length
    raise AssertionError('JPEG frame dimensions missing')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    p.add_argument('--output',type=Path,default=R/'docs/porting/th14-browser-startup-observed-oct28.json')
    a=p.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    h=R/'artifacts/th14/native-frame-readback-oct28';ui=h/'browser-startup'
    delivery=h/'fullscreen-runtime-delivery'
    build=load(delivery/'browser-candidate/build.json');transport=load(delivery/'launcher-candidate/transport.json')
    assert build['compiled']and build['compiledUnits']==0 and build['reusedObjectCount']==146
    assert any('ccall,requestFullscreen'in flag for flag in build['linkFlags'])
    assert build['wasmSha256']=='35e69e59c0d31bf08e73cefc67ba18ba681af5d421c26de6fe76bda91adae3bd'
    assert SHA(read(delivery/'browser-candidate/build-tool.py'))==build['toolSha256']
    assert transport['verifiedTransport']and transport['quietByDefault']and len(transport['requests'])==21
    pictures=[]
    for name in ('fullscreen-getter-failure','ordinary-selection','normal-first-stage','ordinary-pause-menu','ordinary-game-over','persisted-score-export'):
        raw=read(ui/(name+'.jpg'))
        width,height=jpeg_dimensions(raw);assert width>=640 and height>=480
        pictures.append(dict(label=name,width=width,height=height,sha256=SHA(raw)))
    ax=read(ui/'persisted-score-export-ax.txt').decode()
    assert '已开始下载原版存档'in ax and '127.0.0.1:8230/'in ax
    score=ui/'persisted-score';production=load(score/'production.json');native=load(score/'native/native.json')
    packed=read(score/'browser-export.dat');raw=read(score/'production.raw')
    assert len(packed)==21656 and len(raw)==149076
    assert production['passed']and production['productionDecodeSyncAndRoundtripExact']and native['passed']
    assert SHA(packed)==production['inputSha256']==native['inputSha256']==native['rewrittenSha256']
    assert SHA(raw)==production['decodedSha256']==native['decodedSha256']
    assert read(score/'native/retail-loaded.raw')==raw and read(score/'native/retail-rewritten.dat')==packed
    assert production['normalReimuARanking'][-1]['displayedScore']==124431
    assert production['normalReimuARanking'][-1]['continues']==1
    read(ui/'verify-exported-score.py');read(R/'tools/th14-browser-score-native.py')
    read(score/'fixture.cpp');read(score/'command.json');read(score/'score.wasm')
    full=load(R/'docs/porting/th14-current-full-replay-verified-oct28.json')
    assert full['verifiedFiniteApplicationFullReplay']and full['frames']==123412 and full['assertions']==44
    assert full['finalLivingStock']==1 and full['finalScoreUnits']==154806314
    assert full['previousIncompleteVmObservationRetained']and full['previousWebGpuWallBudgetFailureRetained']
    read(R/'tools/th14-application-full-replay-evidence-oct28.py')
    worker=R/'artifacts/th14/native-frame-readback-oct27/archive-worker-public-v2'
    wb=load(worker/'build.json');wc=load(worker/'check.json')
    assert wc['passed']and wc['actualIndependentWorkerThread']and wc['archiveEntries']==227
    assert wc['directByteComparison']and wc['comparedDecodedBytes']==253480939
    assert wc['reverseOrderComparisons']==227 and not wc['reverseOrderIsDirectByteComparison']
    assert wc['mainEventLoopPulsesDuringWorkerRequests']>0
    for flag in ('immutableInputUnchanged','distinctTransferredOutputBuffers','malformedArchiveRejected',
        'missingResourceRejected','emptyBatchRejected','subsequentJobAfterRejectionPassed','cancellationRejectedPendingJob','freshWorkerAfterCancellationPassed'):
        assert wc[flag],flag
    assert not wc['productionIntegrated']and not wc['browserAcceptance']
    for name,row in wc['sourceBindings'].items():assert SHA(read(worker/name))==row['sha256'],name
    assert SHA(read(worker/'archive-decoder.wasm'))==wb['wasmSha256']
    for path,row in wb['sourceBindings'].items():
        frozen=worker/'source'/Path(path).name if path.startswith('runtimes/')else R/path
        assert SHA(read(frozen))==row['sha256'],path
    old_worker=load(R/'artifacts/th14/native-frame-readback-oct27/archive-worker-public/check.json')
    assert not old_worker['passed']and 'ResourceCrypt.cpp'in old_worker['error']
    native_home=R/'artifacts/th14/native-frame-readback-oct27/initial-cpu-worker-boundaries'
    nr=load(native_home/'report.json');read(native_home/'run-tool.py')
    assert nr['childExited']and nr['frameReadbackCompleted']and nr['stageWorkerBoundariesComplete']and not nr['error']
    assert nr['originalCodeWrites']==nr['gameStateWrites']==0 and not nr['inputInjection']
    assert nr['threadContextRedirects']==2 and nr['plan']['stageWorkerHardwareObservationPerturbsScheduling']
    boundaries=nr['stageWorkerBoundaries'];assert len(boundaries)==11
    assert not boundaries[0]['optionVms']
    assert [len(x['optionVms'])for x in boundaries[1:]]==[4]*10
    assert {x['ageCurrent']for x in boundaries[1]['optionVms']}=={1}
    assert {x['ageCurrent']for x in boundaries[-1]['optionVms']}=={33}
    read(native_home/'stage-worker-boundaries.jsonl');read(native_home/'resource-pump-entries.jsonl')
    comparison=load(R/'artifacts/th14/native-frame-readback-oct27/initial-cpu-worker-strict-v2.json')
    assert not comparison['strictAllSelectedStateLiveVmsAndPixelsEqual']and not comparison['bothRngEqual']
    assert comparison['nativeRngWords'][1]==8616 and comparison['portRngWords'][1]==8640
    assert comparison['pixelDifferentBytes']==42666 and comparison['pixelDifferentPixels']==14069
    result=dict(actualBrowserFiniteUiObserved=True,
        ordinaryBrowserScope=['startup','Normal/Reimu-A selection','first stage','pause and resume',
            'natural early game over','score-name completion','return to title','page reload','Launcher score download'],
        browser='Chromium156 on Windows; in-app browser',quietByDefault=True,
        startupFailureRetained=True,fix='Export requestFullscreen in Emscripten runtime methods so SDL3 can assign it during video initialization',
        unchangedGameplayWasmSha256=build['wasmSha256'],compiledCppUnits=0,reusedObjects=146,
        transportRoutes=133,httpChecks=21,observedPreviewUrl='http://127.0.0.1:8230/?game=th14',
        scoreAfterReloadBytes=len(packed),scoreDecodedBytes=len(raw),scoreRoundtripAndOriginalCodecEqual=True,
        displayedSavedNormalReimuAScore=124431,screenshots=pictures,
        currentGlesFullReplayFrames=123412,currentGlesFullReplayAssertions=44,currentWebGpuFullReplayPassed=False,
        standaloneCpuWorkerEntries=227,standaloneCpuWorkerDecodedBytes=253480939,workerIntegratedIntoGame=False,
        originalCpuWorkerBoundaries=11,thirdNativeGameplayFrameStillStrictlyFailed=True,
        originalOrdinaryUiEquivalence=False,originalWholeApplicationPixelsOrPcmCompared=False,
        completeBrowserAcceptance=False,replaySaveAndReloadNotAccepted=True,
        physicalAudioAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    if a.check:assert json.loads(a.output.read_bytes())==result
    else:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('bindings','screenshots')}))

if __name__=='__main__':main()
