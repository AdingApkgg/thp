"""Verify finite TH14 STD/ECL worker integration and dependency ownership."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-frame-readback-oct28';SHA=lambda b:hashlib.sha256(b).hexdigest()
def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    home=H/'stage-ecl-browser-candidate-v2';browser=load(home/'build.json');before=load(H/'stage-ecl-browser-candidate/build.json');worker=load(home/'archive-worker/build.json')
    assert before['compiledUnits']==146 and browser['compiledUnits']==0 and browser['reusedObjectCount']==browser['sourceUnits']==146
    assert browser['wasmSha256']==before['wasmSha256']and browser['objectHashes']==before['objectHashes']and browser['wasmBytes']==2743750
    assert browser['rootUnrelatedResourceCryptExcluded']and browser['sourceBindings']['th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    assert browser['toolSha256']==SHA(raw(R/'tools/th14-build-webgpu-release.py'))
    for name,row in browser['sourceBindings'].items():assert SHA(raw(home/'source'/name))==row['sha256']
    for name in ('th12_web/cpp/game/GameResources.cpp','th12_web/cpp/game/GameResources.hpp','th12_web/cpp/game/EclResource.cpp','th12_web/cpp/game/EclResource.hpp','th12_web/cpp/game/StageEclTransferTh14.hpp','portable/sdl/Th14WebGpuLibrary.js','portable/sdl/Th14WebGpuRuntime.mjs','portable/sdl/Th14ArchiveReadAhead.mjs','portable/sdl/Th14ArchiveDecodeEndpoint.mjs','portable/sdl/Th14ArchiveDecodeClient.mjs'):
        assert SHA(raw(R/'runtimes/th12'/name))==browser['sourceBindings'][name]['sha256']
    assert worker['actualProductionStdAndEclParsers']and worker['parsedStdAndEclTransferVersion']==1 and worker['wasmBytes']==76918
    assert worker['buildToolSha256']==SHA(raw(R/'tools/th14-archive-worker-prototype-build-oct27.py'))
    for name,row in worker['sourceBindings'].items():
        if name.startswith('tools/'):assert SHA(raw(R/name))==row['sha256']
        elif name.startswith('runtimes/th12/th12_web/cpp/game/'):
            assert row['sha256']==browser['sourceBindings'][name.removeprefix('runtimes/th12/')]['sha256']
    for name,row in browser['archiveWorkerFiles'].items():assert len(raw(home/name))==row['bytes']and SHA(raw(home/name))==row['sha256']
    packet=load(H/'stage-ecl-transfer-component-v2/check.json');packet_build=load(H/'stage-ecl-transfer-component-v2/build.json')
    assert packet['passed']and packet['stdEntries']==7 and packet['eclEntries']==24 and len(packet['rows'])==31
    assert packet['transferredParsedBytes']==652018 and packet['rejectedPackets']==53 and all(x['allFieldsAndBytesEqual']for x in packet['rows'])
    assert packet['fixtureBuildSha256']==SHA(raw(H/'stage-ecl-transfer-component-v2/build.json'))
    assert packet['workerBuildSha256']==packet_build['workerBuildSha256']==SHA(raw(home/'archive-worker/build.json'))
    assert packet['checkerSha256']==SHA(raw(R/'tools/th14-stage-ecl-transfer-check-oct29.mjs'))
    assert packet_build['toolSha256']==SHA(raw(R/'tools/th14-stage-ecl-transfer-component-oct29.py'))
    baseline=load(H/'stage-ecl-resource-component-baseline/check.json');resources=load(H/'stage-ecl-resource-component-v2/check.json');resource_build=load(H/'stage-ecl-resource-component-v2/build.json')
    assert baseline['passed']and baseline['cases']==42 and len(baseline['batchEclMisses'])==12 and not baseline['allEclFilesWithinOwnedBatches']
    assert set(baseline['batchEclMisses'])=={'st04mbs2.ecl','st04bs2.ecl'}
    assert resources['passed']and resources['cases']==42 and all(x['allParsedValuesAndBytesEqual']for x in resources['rows'])
    assert resources['allEclFilesWithinOwnedBatches']and not resources['batchEclMisses']
    assert resources['parsedCalls']==resources['parsedCopies']==dict(std=43,ecl=265)
    assert resources['parsedAnmReads']==resources['parsedAnmCopies']==199 and resources['cacheReads']==resources['cacheCopies']==42
    assert resources['corruptedPacketCannotSilentlyFallback']and resources['failedBatchCannotSilentlyFallback']
    assert resources['browserBuildSha256']==resource_build['browserBuildSha256']==SHA(raw(home/'build.json'))
    assert resources['fixtureBuildSha256']==SHA(raw(H/'stage-ecl-resource-component-v2/build.json'))
    assert resources['checkerSha256']==SHA(raw(R/'tools/th14-background-resource-check-oct28.mjs'))
    assert resource_build['toolSha256']==SHA(raw(R/'tools/th14-background-resource-build-oct28.py'))
    for name,digest in resource_build['objectBindings'].items():assert digest==browser['objectHashes'][name]
    for name,digest in resource_build['sourceBindings'].items():
        if name.startswith('th12_web/tests/'):assert SHA(raw(R/'runtimes/th12'/name))==digest
    program=load(H/'stage-ecl-program-regression/check.json');program_build=load(H/'stage-ecl-program-regression/build.json')
    assert program['passed']and program['cases']==24 and program['directSnapshotBytesCompared']==1100649
    assert program['publishedVsCurrentActualCpp']and program['allDefinitionNamesLookedUp']and program['buildSha256']==SHA(raw(H/'stage-ecl-program-regression/build.json'))
    assert program['checkerSha256']==SHA(raw(R/'tools/th14-ecl-program-regression-check-oct29.mjs'))
    assert program_build['toolSha256']==SHA(raw(R/'tools/th14-ecl-program-regression-oct29.py'))
    for name in ('EclResource.cpp','EclResource.hpp'):
        relative='runtimes/th12/th12_web/cpp/game/'+name;assert program_build['builds']['current']['sourceBindings'][relative]==SHA(raw(R/relative))
    queue=load(H/'stage-ecl-runtime-controls/report.json');assert queue['passed']and queue['parsedStdEclDependencyClosureOwned']and queue['eclClosureDirectByteCases']==4
    assert queue['cpuFinishedDuringPendingFrame']and queue['callbackWaitedForFrame']and queue['staleCallbackDeliveredOnceForCppTokenCleanup']and queue['resumedGenerationPassed']
    for name,row in queue['sourceBindings'].items():assert SHA(raw(home/name))==row['sha256']
    raw(R/'tools/th14-archive-runtime-check-oct28.mjs')
    transport=load(H/'stage-ecl-launcher/http-check.json');assert transport['verifiedTransport']and transport['routes']==139 and len(transport['requests'])==27 and transport['wasmSha256']==browser['wasmSha256']
    # Actual browser evidence is deliberately required before public acceptance.
    served=load(H/'stage-ecl-launcher/served-current.json');assert served['wasmSha256']==browser['wasmSha256']and served['quietInjectedIntoParentAndIframe']
    for name in ('stage4-running','stage4-paused','stage4-resumed','short-natural-end','returned-replay-list'):
        image=raw(H/f'stage-ecl-browser-ui/{name}.jpg');assert image[:3]==b'\xff\xd8\xff'
        ax=raw(H/f'stage-ecl-browser-ui/{name}.ax.txt').decode();assert 'runtimeEpoch='in ax and '音频 0ms'in ax and '本机测试静音'in ax
    return dict(verifiedFiniteStageEclWorkerIntegration=True,stdResources=7,eclResources=24,parsedPacketBytesCompared=652018,malformedPacketsRejected=53,
        actualProductionGameResourceCases=42,validAnmImports=198,validStdImports=42,validEclImports=264,corruptImportControlsEachKind=1,
        previousOwnedEclMisses=12,currentOwnedEclMisses=0,eclDependencyClosureFromActualIncludes=True,
        publishedProgramRegressionCases=24,publishedProgramSnapshotBytesCompared=1100649,publishedProgramRegressionBase=program['publishedBase'],
        browserMainCppUnitsRecompiled=146,closureRefinementReusedMainCppUnits=146,mainModuleByteIdenticalAfterClosure=True,
        browserMainWasmBytes=browser['wasmBytes'],browserMainWasmSha256=browser['wasmSha256'],workerWasmBytes=worker['wasmBytes'],workerWasmSha256=worker['wasmSha256'],
        actualBrowserStage4PauseResumeAndShortReplayEndObserved=True,actualBrowserFullCampaignForThisBuildAccepted=False,
        allLoadingWorkOnCpuWorker=False,independentOriginalThreadSchedulingAccepted=False,
        completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();proof=evidence();target=R/'docs/porting/th14-stage-ecl-worker-verified-oct29.json'
    if a.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:proof[k]for k in ('verifiedFiniteStageEclWorkerIntegration','stdResources','eclResources','actualProductionGameResourceCases','currentOwnedEclMisses','completeGame')}))
if __name__=='__main__':main()
