"""Bind remaining core worker batches and actual rejection/recovery evidence."""
from pathlib import Path
import argparse, hashlib, json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-frame-readback-oct28'
SHA=lambda data:hashlib.sha256(data).hexdigest()

def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    def check(path,digest):assert SHA(raw(path))==digest,str(path)
    home=H/'core-tail-browser-candidate';build=load(home/'build.json');previous=load(H/'selected-player-browser-candidate-v2/build.json')
    assert build['basePublishedCommit']=='d0210754361a102e97e740bdaf0fcfd62ffee5f3'
    assert build['compiledUnits']==1 and build['reusedObjectCount']==145 and build['rootUnrelatedResourceCryptExcluded']
    app='th12_web/cpp/sdl/Application.cpp'
    assert [name for name,row in build['sourceBindings'].items()if row['sha256']!=previous['sourceBindings'][name]['sha256']]==[app]
    assert [name for name,digest in build['objectHashes'].items()if digest!=previous['objectHashes'][name]]==[app]
    for name,row in build['sourceBindings'].items():check(home/'source'/name,row['sha256'])
    for name,digest in build['objectHashes'].items():check(home/'objects'/(name.replace('/','_')+'.o'),digest)
    check(R/'runtimes/th12'/app,build['sourceBindings'][app]['sha256'])
    check(R/'tools/th14-build-webgpu-release.py',build['toolSha256'])
    check(home/'th14-sdl.wasm',build['wasmSha256']);check(home/'th14-sdl.mjs',build['loaderSha256'])
    assert build['archiveWorkerFiles']==previous['archiveWorkerFiles']
    for name,row in build['archiveWorkerFiles'].items():check(home/name,row['sha256'])
    worker=load(home/'archive-worker/build.json')
    component=H/'core-tail-resource-component';fixture=load(component/'build.json');result=load(component/'check.json')
    assert result['passed'] and result['validCoreBatches']==8 and result['rawShtCopies']==12 and result['parsedAnmCopies']==9 and result['parsedEclCopies']==2
    for key in ('actualProductionCoreOwner','actualIndependentCpuWorker','allCoreAnmAndShtFieldsAndEclDefinitionsEqual','invalidJobRejected','duplicateJobsDoNotRead','failedBatchCannotFallback','corruptPacketCannotFallback','subsequentValidCoreLoadsPassed','shotParsingRemainsOnMainConsumer'):assert result[key],key
    assert not result['actualApplicationControllerTest']
    assert [row['index']for row in result['rows']]==[3,6,7,8]
    assert fixture['browserBuildSha256']==result['browserBuildSha256']==SHA(raw(home/'build.json'))
    check(component/'build.json',result['fixtureBuildSha256']);check(component/'resources.wasm',fixture['wasmSha256']);check(component/'resources.mjs',fixture['loaderSha256'])
    check(R/'tools/th14-background-resource-build-oct28.py',fixture['toolSha256']);check(R/'tools/th14-core-tail-worker-check-oct29.mjs',result['checkerSha256'])
    assert fixture['objectBindings']=={name:digest for name,digest in build['objectHashes'].items()if name.startswith('th12_web/cpp/game/')}
    for name,digest in fixture['sourceBindings'].items():
        check(component/'source'/name,digest)
        if '/tests/'in name:check(R/'runtimes/th12'/name,digest)
    native={}
    for backend in ('gles','webgpu'):
        new=H/('core-tail-native-'+backend+'-build');old=H/('selected-player-native-'+backend+'-build')
        n=load(new/'build.json');p=load(old/'build.json')
        assert n['newObjects']==p['newObjects'] and n['coreObjects']==p['coreObjects']
        assert raw(new/'application.wasm')==raw(old/'application.wasm')
        check(new/'application.wasm',n['wasmSha256'])
        for name,digest in n['newObjects'].items():check(new/name,digest);check(old/name,digest)
        for name,row in n['sourceBindings'].items():check(R/name,row['sha256'])
        baseline=H/('selected-player-native-'+backend+'-baseline');run=load(baseline/'report.json')
        assert run['completed']and not run['error']and run['frames']==2264 and len(run['checks'])==7
        assert all(row['passed']for row in run['checks'])and run['wasmSha256']==n['wasmSha256']
        for capture in run['captures']:
            check(baseline/capture['file'],capture['sha256']);check(baseline/capture['liveAnimations']['file'],capture['liveAnimations']['sha256'])
        native[backend]=dict(wasmByteIdentical=True,platformObjectsByteIdentical=True,wasmSha256=n['wasmSha256'],previousFiniteRunFrames=2264,noNewNativeRunClaimed=True)
    transport=load(H/'core-tail-launcher/http-check.json');assert transport['verifiedTransport']and transport['routes']==139 and len(transport['requests'])==27
    served=load(H/'core-tail-launcher/served-restored.json');assert served['wasmSha256']==build['wasmSha256']and served['actualServedMainAndWorkerBytesEqual']and served['quietInjectedIntoParentAndIframe']
    for request in served['requests']:check(home/request['route'].rsplit('/',1)[-1],request['sha256'])
    fault=load(H/'core-tail-fault-pl01/launcher-report.json');assert fault['testOnlyFaultInjection']and not fault['productionFilesModified']and fault['wasmSha256']==build['wasmSha256']and fault['faultResource']=='pl01.anm'
    check(R/'tools/th14-boot-worker-control-oct29.py',fault['controlToolSha256'])
    endpoint=raw(R/fault['files']['runtime/th14/Th14ArchiveDecodeEndpoint.mjs']['path'])
    injection=b"      if (Array.isArray(message.names) && message.names.includes('pl01.anm')) throw new Error('TH14_TEST_ONLY_SELECTED_PLAYER_REJECTION');\n"
    assert endpoint.count(injection)==1 and endpoint.replace(injection,b'',1)==raw(home/'Th14ArchiveDecodeEndpoint.mjs')
    assert len(load(H/'core-tail-fault-pl01/served.json')['checks'])==3
    assert 'core-tail-fault-pl01/launcher-report.json'in load(H/'core-tail-fault-pl01/stopped-server.json')['CommandLine']
    ui=H/'core-tail-browser-ui';flow=load(ui/'flow-receipt.json')
    for key in ('titleObserved','shortReplayNaturalEndObserved','returnedReplayList','coreWorkerRejectionObserved','normalWorkerRestored','restoredTitleObserved','restoredReplayListObserved'):assert flow[key],key
    assert flow['selectedShortHud']==dict(score=3100,lives=1,powerHundredths=103,graze=2)
    for name in ('title','replay-list','short-natural-end','returned-replay-list','core-worker-rejected','restored-title','restored-replay-list'):
        assert raw(ui/(name+'.jpg'))[:3]==b'\xff\xd8\xff';ax=raw(ui/(name+'.ax.txt')).decode();assert '本机测试静音'in ax and 'runtimeEpoch='in ax
        assert ('TH14 background core resource decode failed'in ax)if name=='core-worker-rejected'else('音频 0ms'in ax)
    raw(ui/'core-worker-rejected.logs.json')
    return dict(verifiedFiniteRemainingCoreWorker=True,coreJobIndices=[3,6,7,8],anmResources=['enemy.anm','pl00.anm','pl01.anm','pl02.anm'],rawShotResources=['pl00a.sht','pl00b.sht','pl01a.sht','pl01b.sht','pl02a.sht','pl02b.sht'],eclResource='default.ecl',compiledBrowserUnits=1,validatedReusedObjects=145,mainWasmBytes=build['wasmBytes'],mainWasmSha256=build['wasmSha256'],workerWasmBytes=worker['wasmBytes'],workerWasmSha256=worker['wasmSha256'],workerFilesByteIdenticalToSelectedPlayerBuild=True,actualValidCoreBatches=8,invalidAndCorruptControlsPassed=True,shotParsingRemainsOnMainConsumer=True,nativeFeatureOff=native,actualBrowserCoreRejectionObserved=True,normalWorkerRestored=True,shortNaturalEndAndReturnObserved=True,allLoadingWorkOnCpuWorker=False,originalIndependentThreadSchedulingAccepted=False,currentBuildInheritsFrozenFullCampaign=False,completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();proof=evidence();target=R/'docs/porting/th14-core-tail-worker-verified-oct29.json'
    if args.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:proof[key]for key in ('verifiedFiniteRemainingCoreWorker','compiledBrowserUnits','actualBrowserCoreRejectionObserved','completeGame')}))
if __name__=='__main__':main()
