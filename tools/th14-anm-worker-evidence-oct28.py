"""Verify finite production ANM worker parsing, ownership and browser evidence."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-frame-readback-oct28';SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    packet=load(H/'anm-parser-transfer-component/check.json');fixture=load(H/'anm-parser-transfer-component/build.json')
    worker_home=R/fixture['workerBuildPath'];worker=load(worker_home/'build.json')
    assert packet['passed']and packet['archiveEntries']==227 and packet['decodedBytes']==253480939
    assert packet['anmEntries']==len(packet['rows'])==57 and packet['transferredAnmBytes']==245717904 and packet['rejectedPackets']==68
    assert all(x['allFieldsAndBytesEqual']for x in packet['rows'])
    assert packet['actualIndependentCpuWorker']and packet['actualCppPacketImporter']and packet['failedImportPreservesDestination']
    assert packet['fixtureBuildSha256']==SHA(raw(H/'anm-parser-transfer-component/build.json'))
    assert packet['workerBuildSha256']==fixture['workerBuildSha256']==SHA(raw(worker_home/'build.json'))
    assert packet['checkerSha256']==SHA(raw(R/'tools/th14-anm-transfer-check-oct28.mjs'))
    assert fixture['toolSha256']==SHA(raw(R/'tools/th14-anm-transfer-component-oct28.py'))
    for name,field in [('fixture.mjs','loaderSha256'),('fixture.wasm','wasmSha256')]:assert SHA(raw(H/'anm-parser-transfer-component'/name))==fixture[field]
    browser_home=H/'anm-parser-browser-candidate-v2';browser=load(browser_home/'build.json')
    assert browser['compiled']and browser['compiledUnits']==browser['sourceUnits']==146 and browser['reusedObjectCount']==0
    assert browser['rootUnrelatedResourceCryptExcluded']and browser['sourceBindings']['th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    for path,row in browser['sourceBindings'].items():
        assert SHA(raw(browser_home/'source'/path))==row['sha256']
    for path in ('th12_web/cpp/game/GameResources.cpp','th12_web/cpp/game/AnmTransferTh14.hpp','portable/sdl/Th14WebGpuLibrary.js','portable/sdl/Th14WebGpuRuntime.mjs','portable/sdl/Th14ArchiveReadAhead.mjs','portable/sdl/Th14ArchiveDecodeClient.mjs','portable/sdl/Th14ArchiveDecodeEndpoint.mjs'):
        assert SHA(raw(R/'runtimes/th12'/path))==browser['sourceBindings'][path]['sha256']
    assert SHA(raw(R/'tools/th14-build-webgpu-release.py'))==browser['toolSha256']
    worker_current=load(browser_home/'archive-worker/build.json')
    assert worker_current['actualProductionAnmParser']and worker_current['parsedAnmTransferVersion']==1
    assert worker_current['wasmSha256']==worker['wasmSha256']and worker_current['buildToolSha256']==SHA(raw(R/'tools/th14-archive-worker-prototype-build-oct27.py'))
    for path,row in worker_current['sourceBindings'].items():
        if path.startswith('runtimes/th12/th12_web/cpp/game/'):
            relative=path.removeprefix('runtimes/th12/');assert row['sha256']==browser['sourceBindings'][relative]['sha256']
        elif path.startswith('tools/'):assert SHA(raw(R/path))==row['sha256']
    for name,row in browser['archiveWorkerFiles'].items():assert len(raw(browser_home/name))==row['bytes']and SHA(raw(browser_home/name))==row['sha256']
    resources=load(H/'anm-parser-resource-component/check.json');resource_build=load(H/'anm-parser-resource-component/build.json')
    assert resources['passed']and resources['cases']==len(resources['rows'])==42 and all(x['allParsedValuesAndBytesEqual']for x in resources['rows'])
    assert resources['parsedAnmReads']==resources['parsedAnmCopies']==199 and resources['parsedAnmBytes']==496420831
    assert resources['actualProductionCppImporterUsed']and resources['corruptedPacketCannotSilentlyFallback']and resources['synchronousAnmOutsideBatchPassed']
    assert resources['cacheReads']==resources['cacheCopies']==336
    assert resources['browserBuildSha256']==resource_build['browserBuildSha256']==SHA(raw(browser_home/'build.json'))
    assert resources['checkerSha256']==SHA(raw(R/'tools/th14-background-resource-check-oct28.mjs'))
    assert resource_build['toolSha256']==SHA(raw(R/'tools/th14-background-resource-build-oct28.py'))
    for path,digest in resource_build['objectBindings'].items():assert digest==browser['objectHashes'][path]
    assert resource_build['sourceBindings']['th12_web/tests/cpp/th14-background-resource-fixture.cpp']==SHA(raw(R/'runtimes/th12/th12_web/tests/cpp/th14-background-resource-fixture.cpp'))
    queue=load(H/'anm-parser-runtime-controls/report.json')
    assert queue['passed']and queue['cpuFinishedDuringPendingFrame']and queue['callbackWaitedForFrame']and queue['staleCallbackDeliveredOnceForCppTokenCleanup']and queue['resumedGenerationPassed']
    assert queue['parsedAnmTransferredAndOwned']and queue['parsedAnmFailureAndGenerationClearingPassed']
    for name,row in queue['sourceBindings'].items():assert SHA(raw(browser_home/name))==row['sha256']
    raw(R/'tools/th14-archive-runtime-check-oct28.mjs')
    transport=load(H/'anm-parser-launcher/http-check.json');served=load(H/'anm-parser-launcher/served-current.json')
    assert transport['verifiedTransport']and transport['routes']==139 and len(transport['requests'])==27
    assert transport['wasmSha256']==served['wasmSha256']==browser['wasmSha256']and served['quietInjectedIntoParentAndIframe']
    for name in ('startup-current','demo-running','replay-list','first-natural-end','second-natural-end','returned-replay-list'):
        image=raw(H/f'anm-parser-browser-ui/{name}.jpg');assert image[:3]==b'\xff\xd8\xff'
        ax=raw(H/f'anm-parser-browser-ui/{name}.ax.txt').decode();assert 'runtimeEpoch=1'in ax and '音频 0ms'in ax and '本机测试静音'in ax
    return dict(verifiedFiniteAnmWorkerIntegration=True,archiveEntries=227,decodedArchiveBytes=253480939,anmEntries=57,
        parsedAnmPacketBytesCompared=245717904,malformedPacketsRejected=68,actualProductionGameResourceCases=42,
        validParsedAnmImports=198,corruptedPacketControls=1,totalParsedAnmImportCalls=199,
        actualCpuWorkerAndCppImporter=True,actualProductionRuntimeQueueControlsPassed=True,
        browserCppUnitsRecompiled=146,browserWasmBytes=browser['wasmBytes'],browserWasmSha256=browser['wasmSha256'],workerWasmBytes=worker_current['wasmBytes'],workerWasmSha256=worker_current['wasmSha256'],
        browserRoutes=139,browserHttpChecks=27,actualBrowserDemoAndTwoPartialReplayEndsVisuallyObserved=True,
        browserStrictOriginalPixelComparison=False,allInitialResourcesParsedOnWorker=False,stdAndEclParsingStillOnMainThread=True,
        independentProductionSchedulingAccepted=False,completeMultiStageBrowserReplayAccepted=False,
        completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();proof=evidence();target=R/'docs/porting/th14-anm-worker-verified-oct28.json'
    if a.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:proof[k]for k in ('verifiedFiniteAnmWorkerIntegration','anmEntries','actualProductionGameResourceCases','totalParsedAnmImportCalls','browserWasmBytes','completeGame')}))
if __name__=='__main__':main()
