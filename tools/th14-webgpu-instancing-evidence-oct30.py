"""Recheck private native/Asyncify instancing controls and actual Application pair.

Original buffers stay private. This accepts a bounded candidate, not its
production integration, browser FPS or whole-game equivalence.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
BASE='8d50230dc1123c30f83a0fb29de2f6728564f60b'

def verify(home):
    bindings={};historical={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]={'bytes':len(raw),'sha256':SHA(raw)};return raw
    def load(path):return json.loads(read(path))
    def source(name,digest):
        path=ROOT/name
        if path.exists()and SHA(path.read_bytes())==digest:return read(path)
        assert name.startswith(('runtimes/','tools/'))
        raw=subprocess.check_output(['git','-C',str(ROOT/'tools/tmp/github-source-release'),'show',BASE+':'+name])
        assert SHA(raw)==digest,name
        historical[name]=dict(commit=BASE,bytes=len(raw),sha256=digest)
        return raw
    cpp=load(home/'build/build.json');js=load(home/'js-build-v2/build.json')
    assert cpp['privateInstanceCandidate']and not cpp['originalRendererSourcesUnmodified']and not cpp['productionChanged']
    assert js['privateRendererCandidate']and js['asyncify']and not js['productionSourcesModified']
    for folder,build in [('build',cpp),('js-build-v2',js)]:
        for name,row in build['sourceBindings'].items():source(name,row['sha256'])
        for name,row in build['sourceFiles'].items():
            digest=row['sha256']if isinstance(row,dict)else row
            assert SHA(read(home/folder/'src'/name))==digest
    assert SHA(read(home/'build/probe.wasm'))==cpp['wasmSha256']
    assert SHA(read(home/'js-build-v2/component.wasm'))==js['wasmSha256']
    assert SHA(read(home/'js-build-v2/component.mjs'))==js['loaderSha256']
    for name in ['WebGpuRenderer.hpp','Th14WebGpu.wgsl']:
        assert read(home/'build/src'/name)==read(home/'js-build-v2/src'/name)
    for name in ['Th14WebGpuHost.mjs','Th14WebGpuRuntime.mjs','Th14WebGpu.wgsl',
                 'Th14ArchiveDecodeClient.mjs','Th14ArchiveReadAhead.mjs']:
        assert read(home/'js-build-v2'/name)==read(home/'js-build-v2/src'/name)
    correction=load(home/'stage-scope-correction.json')
    assert correction['originalComparisonSha256']==SHA(read(home/'stage-replay/comparison.json'))
    assert correction['originalRunnerSha256']==SHA(read(home/'instance-runner-stage-v1.py'))
    assert correction['privateCppRendererCandidate']and not correction['originalRendererSourcesUnmodified']
    stage=ROOT/'artifacts/th14/stage-gpu-stream-replay';synthetic=home/'synthetic-reference'
    totals=[]
    for native,folder,js_folder,count in [(stage,'stage-replay','js-stage',21),(synthetic,'synthetic-candidate','js-synthetic-v2',8)]:
        prepared=load(native/'prepared.json');reference_report=load(native/'native.json');reference=read(native/'native.bgra')
        assert SHA(reference)==reference_report['pixelsSha256']
        current=load(home/folder/'comparison.json');other=load(home/js_folder/'report.json')
        assert current['frames']==current['exactFrames']==other['frames']==other['exactFrames']==count
        assert current['strictPixelsEqual']and current['differentChannels']==other['differentBytes']==0
        assert current['buildSha256']==SHA(read(home/'build/build.json'))
        assert other['buildSha256']==SHA(read(home/'js-build-v2/build.json'))
        assert current['contextToolSha256']==SHA(read(home/'instance-context.py'))
        assert other['toolSha256']==SHA(read(home/'js-runner.mjs'))
        if folder=='stage-replay':assert current['toolSha256']==SHA(read(home/'instance-runner-stage-v1.py'))
        else:assert current['toolSha256']==SHA(read(home/'instance-runner.py'))and current['privateRendererCandidate']
        for report in [current,other]:
            assert report['wasmSha256']==(cpp if report is current else js)['wasmSha256']
            assert report['preparedSha256']==SHA(read(native/'prepared.json'))
            assert report['nativeReportSha256']==SHA(read(native/'native.json'))
            assert report['nativePixelsSha256']==SHA(reference)
            assert not report['browserRun']and not report['browserAcceptance']and not report['completeGame']
            assert not report['contextInfo']['requiredFeatures']if report is current else not report['requiredFeatures']
        for expected,a,b in zip(reference_report['frames'],current['rows'],other['rows'],strict=True):
            assert (expected['stage'],expected['frame'])==(a['stage'],a['frame'])==(b['stage'],b['frame'])
            raw=reference[expected['offset']:expected['offset']+expected['bytes']]
            assert len(raw)==640*480*4 and SHA(raw)==expected['sha256']==a['actualSha256']==b['actualSha256']
            name=f"stage{expected['stage']}-frame{expected['frame']}.bgra"
            assert read(home/folder/name)==read(home/js_folder/name)==raw
        totals.append(dict(frames=count,nativeExactFrames=count,javascriptExactFrames=count,
                           directInputDraws=sum(f['directDraws']for f in prepared['frames']),
                           actualNativeDraws=current['gpuCalls'].get('th14_webgpu_draw',0)+current['gpuCalls'].get('th14_webgpu_draw_instances',0),
                           actualJavascriptDraws=other['gpuCalls']['draw']))
    assert [(t['directInputDraws'],t['actualNativeDraws'],t['actualJavascriptDraws'])for t in totals]==[(1005,630,630),(3128,9,9)]
    inputs=load(synthetic/'prepared.json')
    assert [f['directDraws']for f in inputs['frames']]==[1,2,3,17,1023,1024,1025,33]
    assert all(f['controlledScreenQuadsExcluded']==0 for f in inputs['frames'])
    assert all(f['profile']['varyingFactor']and f['profile']['varyingEye']for f in inputs['frames'])
    runs={}
    for name in ['serial-window','instance-window']:
        run=load(home/name/'report.json');ended=load(home/(name+'-process-end.json'))
        assert run['completed']and not run['error']and ended['exitCode']==0 and ended['guardStop']is None
        assert run['frames']==2264 and len(run['checks'])==21
        assert not run['browserRun']and not run['browserAcceptance']and run['physicalAudioDevicesOpened']==0
        assert run['actualCppApplicationWithPrivateRendererHost']and not run['actualProductionApplicationAndDevices']
        assert run['toolSha256']==SHA(read(home/'application-runner.py'))
        assert run['hostToolSha256']==SHA(read(home/'instance-context.py'))
        assert read(home/name/'run-tool.py')==read(home/'application-runner.py')
        runs[name]=run
    a,b=runs.values()
    for key in ['frames','actions','checks','rows','pcmFrames','pcmSha256','initialSave','finalSave','pendingAsyncCallbacks','deliveredCallbackSequence','metadataEpochAtFrameZero','declaredInitialGameTicks']:
        assert a[key]==b[key],key
    assert len(a['rows'])==496 and len(a['captures'])==len(b['captures'])==2
    for left,right in zip(a['captures'],b['captures'],strict=True):
        assert left==right
        raw=read(home/'serial-window'/left['file']);assert len(raw)==640*480*4 and SHA(raw)==left['sha256']
        assert raw==read(home/'instance-window'/right['file'])
        live=left['liveAnimations']['file'];raw=read(home/'serial-window'/live)
        assert SHA(raw)==left['liveAnimations']['sha256']and raw==read(home/'instance-window'/live)
    assert a['pcmFrames']==1508352
    for name in runs:
        replay=read(home/name/'save/replay/th14_01.rpy')
        assert len(replay)==110022 and SHA(replay)=='c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74'
    app=load(home/'application-build/build.json')
    assert app['privateRendererCandidate']and app['rendererObjectsRecompiled']==1 and app['platformObjectsReused']==4
    assert SHA(read(home/'application-build/application.wasm'))==app['wasmSha256']==b['wasmSha256']
    assert SHA(read(home/'application-build/build.json'))==b['buildReportSha256']
    for name,row in app['sourceBindings'].items():
        if name in app['privateSourcePaths']:assert SHA(read(Path(app['privateSourcePaths'][name])))==row['sha256']
        else:source(name,row['sha256'])
    for name,digest in app['newObjects'].items():assert SHA(read(home/'application-build'/name))==digest
    assert len(app['coreObjects'])==141
    for row in app['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
    native_draws=[a['glCalls']['th14_webgpu_draw'],b['glCalls']['th14_webgpu_draw']+b['glCalls']['th14_webgpu_draw_instances']]
    assert native_draws==[225938,82420]
    first_build=load(home/'js-build/build.json')
    assert first_build['wasmSha256']==js['wasmSha256']and first_build['loaderSha256']==js['loaderSha256']
    assert 'Th14ArchiveDecodeClient.mjs' in read(home/'js-synthetic.log').decode()
    for name in ['prepare.py','synthetic-inputs.py','synthetic-hal.py','prepare-js.py','prepare-application.py','run-application-windows.py']:
        read(home/name)
    attract=ROOT/'artifacts/th14/webgpu-instance-attract-oct30'
    plan=load(attract/'plan.json');scenario=load(attract/'scenario.json')
    assert plan['maximumFramesEach']==30000 and plan['maximumWallSecondsEach']==1800
    assert plan['maximumOutputBytes']==128*1024**2 and plan['minimumFreeBytes']==100*1024**3
    assert not plan['priorAttractAcceptanceInherited']and plan['cleanPrivateSave']
    assert all(not action.get('held',0)and not action.get('pause',0)for action in scenario['actions'])
    demos={}
    for name in ['gles','webgpu']:
        run=load(attract/name/'report.json');ended=load(attract/(name+'-process-end.json'))
        assert run['completed']and not run['error']and run['frames']==17547 and len(run['checks'])==30
        assert ended['exitCode']==0 and ended['guardStop']is None and ended['elapsedSeconds']<1830
        assert run['initialSave']==run['finalSave']=={}and run['physicalAudioDevicesOpened']==0
        assert not run['browserRun']and not run['browserAcceptance']and not run['completeGame']
        assert run['toolSha256']==SHA(read(home/'application-runner.py'))
        demos[name]=run
    left,right=demos.values()
    for key in ['actions','checks','rows','pcmFrames','pcmSha256','initialSave','finalSave','pendingAsyncCallbacks','deliveredCallbackSequence']:
        assert left[key]==right[key],key
    assert left['pcmFrames']==12681216 and len(left['captures'])==len(right['captures'])==7
    for before_capture,after_capture in zip(left['captures'],right['captures'],strict=True):
        assert before_capture==after_capture
        raw=read(attract/'gles'/before_capture['file']);assert len(raw)==640*480*4 and SHA(raw)==before_capture['sha256']
        assert raw==read(attract/'webgpu'/after_capture['file'])
        name=before_capture['liveAnimations']['file'];raw=read(attract/'gles'/name)
        assert SHA(raw)==before_capture['liveAnimations']['sha256']and raw==read(attract/'webgpu'/name)
    assert len(left['actions'])==13
    assert [left['actions'][i]['state'][1]for i in [2,6,10]]==[3,4,1]
    assert all(left['actions'][i]['state'][0:2]==[0,0]for i in [4,8,12])
    pair=load(attract/'pair.json')
    assert not pair['runningPrefixOnly']and pair['pairedImages']==7 and pair['allPairedCapturedBuffersEqual']
    assert pair['allSharedActionStatesEqual']and pair['journalComparison']['allRowsEqual']
    assert pair['silentPcmSinkComparison']['framesEqual']and pair['silentPcmSinkComparison']['reportedHashEqual']
    assert sum(p.stat().st_size for p in attract.rglob('*')if p.is_file())<128*1024**2
    observed=sum(p.stat().st_size for p in home.rglob('*')if p.is_file())
    assert observed<128*1024**2 and shutil.disk_usage(home).free>=100*1024**3
    return dict(schema='th14/webgpu-instancing-candidate/1',privateCandidateVerified=True,
                finiteGraphics=totals,applicationFramesEach=2264,applicationAssertionsEach=21,
                sameSelectedJournalRows=496,applicationWholeCapturedBuffersEqual=2,
                silentPcmFramesEach=1508352,silentPcmSha256=a['pcmSha256'],
                applicationDrawCallsBefore=225938,applicationDrawCallsAfter=82420,
                coreObjectsVerified=141,rootProductionRendererChanged=False,
                attractFramesEach=17547,attractAssertionsEach=30,attractWholeCapturedBuffersEqual=7,
                attractJournalRows=len(left['rows']),attractSilentPcmFramesEach=12681216,
                attractCurrentCoreThreeNaturalReturns=True,
                asyncComponentStaticImportsFixed=True,priorMissingModuleFailureRetained=True,
                browserFpsAccepted=False,productionIntegrationAccepted=False,
                originalWholeApplicationPixelsOrPcmCompared=False,completeGame=False,nativeEquivalent=False,
                verifierSha256=SHA(Path(__file__).read_bytes()),historicalSources=historical,bindings=bindings)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/webgpu-instance-candidate-oct30')
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=args.home.resolve();output=args.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')
    assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    result=verify(home)
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['privateCandidateVerified','applicationFramesEach','applicationDrawCallsBefore','applicationDrawCallsAfter','productionIntegrationAccepted']}))
