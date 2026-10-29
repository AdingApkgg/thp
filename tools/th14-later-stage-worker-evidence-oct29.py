"""Recompute finite later-stage CPU ownership and real browser transition evidence."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-frame-readback-oct28';SHA=lambda b:hashlib.sha256(b).hexdigest()
def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);data=path.read_bytes()
        bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    def check(path,digest):assert SHA(raw(path))==digest,str(path)
    home=H/'later-stage-browser-candidate';build=load(home/'build.json');previous=load(H/'bootstrap-browser-candidate/build.json')
    assert build['basePublishedCommit']=='4d73dffe1f7a374f32c727f01feb7ea3f9daee63'and build['compiledUnits']==146 and build['reusedObjectCount']==0
    assert build['rootUnrelatedResourceCryptExcluded']and not build['retailAssetsIncluded']
    changed={'th12_web/cpp/sdl/Application.cpp','th12_web/cpp/game/GameSessionResources.cpp','th12_web/cpp/game/GameSessionResources.hpp','th12_web/cpp/sdl/StageDecodeTh14.hpp'}
    assert {name for name,row in build['sourceBindings'].items()if name not in previous['sourceBindings']or row['sha256']!=previous['sourceBindings'][name]['sha256']}==changed
    for name,row in build['sourceBindings'].items():check(home/'source'/name,row['sha256'])
    for name in changed:check(R/'runtimes/th12'/name,build['sourceBindings'][name]['sha256'])
    for name,digest in build['objectHashes'].items():check(home/'objects'/(name.replace('/','_')+'.o'),digest)
    check(R/'tools/th14-build-webgpu-release.py',build['toolSha256']);check(home/'th14-sdl.wasm',build['wasmSha256']);check(home/'th14-sdl.mjs',build['loaderSha256'])
    assert build['archiveWorkerFiles']==previous['archiveWorkerFiles']
    for name,row in build['archiveWorkerFiles'].items():check(home/name,row['sha256'])
    worker=load(home/'archive-worker/build.json');component=H/'later-stage-resource-component'
    fixture=load(component/'build.json');result=load(component/'check.json')
    assert result['passed']and result['cases']==30 and result['synchronousConsumers']==30 and result['imports']==468 and result['batches']==203
    assert [(row['stage'],row['selection'])for row in result['rows']]==[(stage,selection)for stage in range(2,7)for selection in range(6)]
    assert all(row['allParsedFieldsAndBytesEqual']and row['synchronousConsumerPassed']for row in result['rows'])
    for key in ('actualProductionControllerAndSessionOwner','actualIndependentCpuWorker','allParsedFieldsAndBytesEqual','cancelBeforeAnyGpuRequestPassed','cancelAfterPublishedScenePassed','suspendResumeAllPhasesPassed','noGraphicsOrAudioDevices'):assert result[key],key
    assert not result['actualApplicationControllerTest']and len(result['controls'])==16
    for phase in range(3):
        assert any(x.get('phase')==phase and x.get('cancelBeforeGpuAndStaleOwnerRejected')for x in result['controls'])
        assert any(x.get('phase')==phase and x.get('suspendStaleRejectedAndResumeRequeued')for x in result['controls'])
        assert any(x.get('phase')==phase and x.get('failedBatchNoSynchronousFallback')for x in result['controls'])
    assert {(x['phase'],x['corruptKind'])for x in result['controls']if 'corruptKind'in x}=={(0,'anm'),(1,'std'),(1,'anm'),(2,'ecl'),(2,'anm')}
    assert result['browserBuildSha256']==fixture['browserBuildSha256']==SHA(raw(home/'build.json'))
    check(component/'build.json',result['fixtureBuildSha256']);check(component/'resources.wasm',fixture['wasmSha256']);check(component/'resources.mjs',fixture['loaderSha256'])
    check(R/'tools/th14-later-stage-worker-check-oct29.mjs',result['checkerSha256']);check(R/'tools/th14-background-resource-build-oct28.py',fixture['toolSha256'])
    assert fixture['objectBindings']=={name:digest for name,digest in build['objectHashes'].items()if name.startswith('th12_web/cpp/game/')}
    for name,digest in fixture['sourceBindings'].items():
        check(component/'source'/name,digest)
        if '/tests/'in name:check(R/'runtimes/th12'/name,digest)
    core=load(H/'later-stage-native-core/observer-build.json')
    assert core['engineSourcesRecompiledForThisLink']==141 and core['engineObjectsReusedForThisLink']==0 and core['unrelatedRootResourceCryptExcluded']
    assert core['browserBuildSha256']==SHA(raw(home/'build.json'))
    check(R/'tools/th14-build-snapshot-core-oct29.py',core['buildToolSha256']);check(H/'later-stage-native-core/observer.wasm',core['wasmSha256'])
    for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert build['sourceBindings'][name]['sha256']==digest
    for row in core['objectBindings']:check(Path(row['path']),row['sha256'])
    runs={}
    for backend in ('gles','webgpu'):
        directory=H/('later-stage-native-'+backend+'-build');native=load(directory/'build.json')
        assert native['coreBuildSha256']==SHA(raw(H/'later-stage-native-core/observer-build.json'))and native['coreObjects']==core['objectBindings']
        check(directory/'application.wasm',native['wasmSha256']);check(directory/'build-tool.py',native['toolSha256'])
        for name,row in native['sourceBindings'].items():check(R/name,row['sha256'])
        for name,digest in native['newObjects'].items():check(directory/name,digest)
        directory=H/('later-stage-native-'+backend+'-baseline');run=load(directory/'report.json')
        assert run['completed']and not run['error']and run['frames']==run['applicationTicks']==2264 and len(run['checks'])==7
        assert all(row['passed']for row in run['checks'])and run['physicalAudioDevicesOpened']==0 and run['actualProductionApplicationAndDevices']and not run['browserRun']
        assert run['wasmSha256']==native['wasmSha256']and run['pcmFrames']==1508352
        check(H/('later-stage-native-'+backend+'-build/build.json'),run['buildReportSha256'])
        check(R/'tools/th14-native-application-process-host-oct27.py',run['toolSha256']);check(R/('tools/th14-native-'+backend+'-context.py'),run['hostToolSha256'])
        for capture in run['captures']:
            check(directory/capture['file'],capture['sha256']);check(directory/capture['liveAnimations']['file'],capture['liveAnimations']['sha256'])
        runs[backend]=run
    old=load(H/'bootstrap-native-gles-baseline/report.json')
    for key in ('rows','actions','checks','captures','initialSave','finalSave','files','pcmFrames','pcmSha256','finalReferenceState','initialLoadingObservations'):assert runs['gles'][key]==runs['webgpu'][key]==old[key],key
    for capture in runs['gles']['captures']:
        assert raw(H/'later-stage-native-gles-baseline'/capture['file'])==raw(H/'later-stage-native-webgpu-baseline'/capture['file'])==raw(H/'bootstrap-native-gles-baseline'/capture['file'])
    transport=load(H/'later-stage-launcher/http-check.json');assert transport['verifiedTransport']and transport['routes']==139 and len(transport['requests'])==27
    served=load(H/'later-stage-launcher/served-restored.json');assert served['wasmSha256']==build['wasmSha256']and served['actualServedMainAndWorkerBytesEqual']and served['quietInjectedIntoParentAndIframe']
    for request in served['requests']:check(home/request['route'].rsplit('/',1)[-1],request['sha256'])
    fault=load(H/'later-stage-fault-st06logo/launcher-report.json');assert fault['testOnlyFaultInjection']and not fault['productionFilesModified']and fault['wasmSha256']==build['wasmSha256']and fault['faultResource']=='st06logo.anm'
    check(R/'tools/th14-boot-worker-control-oct29.py',fault['controlToolSha256'])
    injection=b"      if (Array.isArray(message.names) && message.names.includes('st06logo.anm')) throw new Error('TH14_TEST_ONLY_LATER_STAGE_REJECTION');\n"
    endpoint=raw(R/fault['files']['runtime/th14/Th14ArchiveDecodeEndpoint.mjs']['path'])
    assert endpoint.count(injection)==1 and endpoint.replace(injection,b'',1)==raw(home/'Th14ArchiveDecodeEndpoint.mjs')
    assert len(load(H/'later-stage-fault-st06logo/served.json')['checks'])==3
    assert 'later-stage-fault-st06logo/launcher-report.json'in load(H/'later-stage-fault-st06logo/stopped-server.json')['CommandLine']
    ui=H/'later-stage-browser-ui';flow=load(ui/'flow-receipt.json')
    for key in ('stage5ReplayStarted','stage5To6TransitionObserved','stage6RunningObserved','laterHudRejectionObserved','normalWorkerRestored','restoredTitleObserved'):assert flow[key],key
    for name in ('stage5-selected','stage5-running','stage6-running','stage-worker-rejected','restored-title'):
        assert raw(ui/(name+'.jpg'))[:3]==b'\xff\xd8\xff';ax=raw(ui/(name+'.ax.txt')).decode();assert '本机测试静音'in ax and 'runtimeEpoch='in ax
        assert ('TH14 background stage resource decode failed'in ax)if name=='stage-worker-rejected'else('音频 0ms'in ax)
    raw(ui/'stage-worker-rejected.logs.json')
    return dict(verifiedFiniteLaterStageWorker=True,stages=[2,3,4,5,6],playerSelections=6,workerResourceCases=30,synchronousConsumerCases=30,
        componentControls=16,realWorkerBatches=203,resourceImports=468,allParsedFieldsAndBytesEqual=True,
        compiledBrowserUnits=146,compiledNativeCoreUnits=141,mainWasmBytes=build['wasmBytes'],mainWasmSha256=build['wasmSha256'],workerWasmSha256=worker['wasmSha256'],
        actualNativeFramesPerBackend=2264,actualNativeAssertionsPerBackend=7,actualNativeResultsAndPreviousEqual=True,nativeApplicationRunsUseArchiveWorkerFeatureOff=True,
        actualBrowserStage5To6Observed=True,actualBrowserLaterStageRejectionObserved=True,normalWorkerRestored=True,
        shtParsingGpuUploadAndTemplatesRemainOnCaller=True,originalIndependentThreadSchedulingAccepted=False,
        currentBuildInheritsCoreTailFullReplay=False,browserVsOriginalWholeFrameComparison=False,browserVsOriginalWholeAudioComparison=False,
        completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();proof=evidence();target=R/'docs/porting/th14-later-stage-worker-verified-oct29.json'
    if a.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:proof[k]for k in ('verifiedFiniteLaterStageWorker','workerResourceCases','actualBrowserStage5To6Observed','completeGame')}))
if __name__=='__main__':main()
