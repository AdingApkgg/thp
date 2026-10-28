"""Verify the finite TH14 terminal-reader and ordinary Application regressions."""
from pathlib import Path
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/'artifacts/th14/native-frame-readback-oct28'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(ROOT)
        b=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    old=load(HOME/'replay-rate-terminal-baseline-v2/report.json')
    fixed=load(HOME/'replay-rate-terminal-fixed/report.json')
    tool=SHA(raw(ROOT/'tools/th14-replay-rate-terminal-oct28.py'))
    assert old['toolSha256']==fixed['toolSha256']==tool
    assert fixed['passed']and not fixed['mismatches']and not old['passed']and len(old['mismatches'])==208
    assert old['cases']==fixed['cases']==36 and old['steps']==fixed['steps']==2804
    assert fixed['allNativeFpsReadsCheckedWithinExplicitData']and fixed['nativeOutOfPayloadReadsExcluded']
    assert fixed['nativeEntry']==0x455180 and fixed['nativePauseRequestControlledAt']==0x448ef0
    assert fixed['nativeKeyboardEdgesExecute']and fixed['cppActualProductionCodecRoundTrip']
    assert fixed['nativeExecutableSha256']==old['nativeExecutableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert all(a['decodedSha256']==b['decodedSha256']and a['recordedRates']==b['recordedRates']for a,b in zip(old['records'],fixed['records']))
    for before,case in zip(old['records'],fixed['records']):
        assert case['cppOpenedProductionEncodedContainer']and len(before['rows'])==len(case['rows'])
        for previous,row in zip(before['rows'],case['rows']):
            assert previous['native']==row['native']and previous['active']==row['active']
            assert row['native'][:2]==row['cpp'][:2]
            assert not row['active']or row['native'][2]==row['cpp'][2]
            assert row['equal']and all(0<=i<len(case['recordedRates'])for i in row['nativeFpsReadOffsets'])
            if row['active']and row['native'][2]:assert not row['nativeFpsReadOffsets']
    reader='runtimes/th12/th12_web/cpp/game/Replay.cpp';source=SHA(raw(ROOT/reader))
    assert fixed['sourceBindings']['th12_web/cpp/game/Replay.cpp']==source
    for row in fixed['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    core=load(HOME/'replay-terminal-core/observer-build.json')
    assert core['sourceHashes']['th12_web/cpp/game/Replay.cpp']==source
    assert core['replayTerminalReaderBuildReportSha256']==SHA(raw(HOME/'replay-rate-terminal-fixed/report.json'))
    for name,digest in fixed['headerBindings'].items():assert SHA(raw(ROOT/'runtimes/th12/th12_web/cpp/game'/name))==digest
    runs=[];reports=[];buffers=[];vm_rows=[]
    original_replay=raw(HOME/'browser-replay/downloaded-th14_01.rpy');assert len(original_replay)==823
    for backend in ('gles','webgpu'):
        home=HOME/f'replay-terminal-application-{backend}';run=load(home/'report.json')
        assert run['completed']and not run['error']and run['frames']==2142 and len(run['checks'])==27 and all(x['passed']for x in run['checks'])
        assert run['physicalAudioDevicesOpened']==0 and not run['browserAcceptance']
        assert run['initialSave']==run['finalSave']and raw(home/'save/replay/th14_01.rpy')==original_replay
        assert run['toolSha256']==SHA(raw(home/'run-tool.py'))
        build=load(HOME/f'replay-terminal-{backend}-build/build.json')
        assert build['coreSourceHashes']['th12_web/cpp/game/Replay.cpp']==source and build['wasmSha256']==run['wasmSha256']
        assert [x['label']for x in run['captures']]==['replay-list','first-natural-end','second-natural-end','returned-replay-list']
        images=[];live=[]
        for cap in run['captures']:
            pixels=raw(home/cap['file']);assert len(pixels)==1228800 and SHA(pixels)==cap['sha256'];images.append(pixels)
            data=raw(home/cap['liveAnimations']['file']);assert SHA(data)==cap['liveAnimations']['sha256']
            v=json.loads(data);assert v['complete']and len(v['rows'])==v['expected']and v['comparedValues']==303
            live.append(v['rows'])
        assert images[1]==images[2]
        ends=[x['state']for x in run['actions']if x['state'][0]==2 and x['state'][6]==717]
        assert len(ends)>=2 and all([x[7],x[8],x[9]]==[1,103,310]for x in ends)
        assert run['actions'][-1]['state'][0]==0 and run['actions'][-1]['state'][3]==11
        reports.append(run);buffers.append(images);vm_rows.append(live)
        runs.append(dict(backend=backend,frames=2142,assertions=27,captures=4,liveRows=sum(map(len,live)),
            naturalReplayEnds=2,encodedReplayBytesPreserved=823,pcmFrames=run['pcmFrames'],pcmSha256=run['pcmSha256'],
            productionWasmSha256=run['wasmSha256'],nativeOriginalOrdinaryPlaybackAccepted=False))
    assert reports[0]['actions']==reports[1]['actions']and reports[0]['rows']==reports[1]['rows']
    assert buffers[0]==buffers[1]and vm_rows[0]==vm_rows[1]
    assert reports[0]['pcmFrames']==reports[1]['pcmFrames']==1391616 and reports[0]['pcmSha256']==reports[1]['pcmSha256']
    browser=load(HOME/'replay-terminal-browser-candidate/build.json')
    previous=load(HOME/'replay-fps-browser-candidate-v2/build.json')
    assert browser['compiled']and browser['sourceUnits']==146 and browser['compiledUnits']==1 and browser['reusedObjectCount']==145
    assert browser['sourceBindings']['th12_web/cpp/game/Replay.cpp']['sha256']==source
    changed=[name for name,digest in browser['objectHashes'].items()if digest!=previous['objectHashes'][name]]
    assert changed==['th12_web/cpp/game/Replay.cpp']
    assert browser['rootUnrelatedResourceCryptExcluded']and browser['sourceBindings']['th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    transport=load(HOME/'replay-terminal-launcher/http-check.json');served=load(HOME/'replay-terminal-launcher/served-current.json')
    assert transport['verifiedTransport']and transport['routes']==139 and len(transport['requests'])==27
    assert transport['wasmSha256']==served['wasmSha256']==browser['wasmSha256']and served['quietInjectedIntoParentAndIframe']
    for name in ('replay-list','first-natural-end','second-natural-end','returned-replay-list'):
        image=raw(HOME/f'replay-terminal-browser-ui/{name}.jpg');assert image[:3]==b'\xff\xd8\xff'
        ax=raw(HOME/f'replay-terminal-browser-ui/{name}.ax.txt').decode();assert 'runtimeEpoch=1'in ax and '音频 0ms'in ax and '本机测试静音'in ax
    return dict(verifiedFiniteTerminalFix=True,th14TerminalPreservesCursorAndRecordedFps=True,
        retailReaderCases=36,retailReaderSteps=2804,beforeMismatchSteps=208,afterMismatchSteps=0,
        comparedReaderFields=fixed['comparedFields'],nativePauseRequestBoundaryControlled=True,
        nativeInputMasksNotComparedToRawReplayWords=True,nativeOutOfPayloadReadsExcluded=True,
        applicationRuns=runs,applicationActionAndJournalRowsEqual=True,applicationCaptureBuffersEqual=4,
        applicationLiveRowsEqual=295,applicationWordsPerLiveVm=303,silentPcmSinksEqual=True,
        browserMainWasmBytes=browser['wasmBytes'],browserMainWasmSha256=browser['wasmSha256'],
        browserCompiledUnits=1,browserReusedUnits=145,browserTransportRoutes=139,browserHttpChecks=27,
        actualBrowserPartialReplayNaturalEnds=2,browserReplayAgainAndReturnListVisuallyObserved=True,
        browserVisualObservationIsNotStrictOriginalPixelComparison=True,
        completeMultiStageBrowserReplayAccepted=False,completeOriginalOrdinaryPlaybackAccepted=False,
        independentProductionLoadingAccepted=False,completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    proof=evidence();target=ROOT/'docs/porting/th14-replay-terminal-verified-oct28.json'
    if a.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:proof[k]for k in ('verifiedFiniteTerminalFix','retailReaderCases','retailReaderSteps','afterMismatchSteps','browserCompiledUnits','browserReusedUnits','completeGame')}))


if __name__=='__main__':main()
