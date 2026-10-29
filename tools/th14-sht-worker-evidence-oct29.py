"""Recompute finite production SHT worker evidence; private inputs are not published."""
from pathlib import Path
import argparse,hashlib,json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/sht-worker-oct29'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    def check(path,digest):assert SHA(raw(path))==digest,str(path)
    def sources(report,prefix=R):
        for name,row in report['sourceBindings'].items():check(prefix/name,row['sha256']if isinstance(row,dict)else row)

    worker=load(H/'cpu-worker/build.json')
    assert worker['compiled']and worker['actualProductionShtParser']and worker['parsedShtTransferVersion']==1 and worker['browserRuntimeModules']
    assert worker['publishedBase']=='872da5bdfa263a1d76bce01845d14e09b538f6aa'
    check(R/'tools/th14-archive-worker-prototype-build-oct27.py',worker['buildToolSha256'])
    # The worker stages published ResourceCrypt, deliberately excluding an unrelated root edit.
    for name,row in worker['sourceBindings'].items():
        staged=(H/'cpu-worker/source'/Path(name).name)if '/cpp/game/'in name else H/'cpu-worker'/Path(name).name
        check(staged,row['sha256'])
        if not name.endswith('/ResourceCrypt.cpp'):check(R/name,row['sha256'])
    assert worker['sourceBindings']['runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    check(H/'cpu-worker/archive-decoder.wasm',worker['wasmSha256'])
    check(H/'cpu-worker/archive-decoder.mjs',worker['loaderSha256'])

    consumer=load(H/'consumer/build.json');case=load(H/'component-check-v2/check.json')
    assert consumer['compiled']and consumer['productionConsumer']and consumer['workerFeatureEnabled']
    assert consumer['reusedProductionCoreObjects']==140 and consumer['compiledProductionCoreObjects']==1
    sources(consumer);check(H/'consumer/consumer.wasm',consumer['wasmSha256'])
    for row in consumer['objectBindings']:check(Path(row['path']),row['sha256'])
    check(R/'tools/th14-sht-worker-component-build-oct29.py',consumer['toolSha256'])
    assert case['passed']and case['cases']==6 and len(case['rows'])==6 and len(case['controls'])==125
    assert sum(row['groups']for row in case['rows'])==60 and sum(row['shots']for row in case['rows'])==283
    assert case['allParsedFieldsAndCanonicalBytesEqual']and case['actualIndependentCpuWorker']and case['actualProductionShtParser']
    assert case['actualProductionGameResourcesConsumer']and case['mainConsumerUsesTestPacketProvider']and not case['actualApplicationControllerTest']
    assert case['parsedCopies']==18 and case['consumerRawReads']==0 and len(case['batches'])==4
    assert all(row['allHeaderAndShotBytesEqual']and row['canonicalPacketBytesEqual']and row['consumerRawReads']==0 for row in case['rows'])
    assert all(row['independentPacketOwnership']for row in case['batches'])
    for row in case['controls']:
        if 'name'in row:assert row['rejected']and row['noRawFallback']
    assert case['workerBuildSha256']==SHA(raw(H/'cpu-worker/build.json'))and case['consumerBuildSha256']==SHA(raw(H/'consumer/build.json'))
    sources(case);check(R/'tools/th14-sht-worker-check-oct29.mjs',case['checkerSha256'])
    check(R/'tools/th14-sht-worker-host-oct29.mjs',case['workerAdapterSha256'])

    browser=load(H/'browser-candidate/build.json')
    assert browser['compiled']and browser['compiledUnits']==146 and browser['reusedObjectCount']==0
    assert browser['basePublishedCommit']==worker['publishedBase']and browser['rootUnrelatedResourceCryptExcluded']and not browser['retailAssetsIncluded']
    sources(browser,H/'browser-candidate/source')
    assert len(browser['objectHashes'])==146
    for name,digest in browser['objectHashes'].items():check(H/'browser-candidate/objects'/(name.replace('/','_')+'.o'),digest)
    for name in ['th12_web/cpp/game/GameResources.cpp','th12_web/cpp/game/ShtTransferTh14.hpp','portable/sdl/Th14ArchiveDecodeClient.mjs','portable/sdl/Th14ArchiveDecodeEndpoint.mjs','portable/sdl/Th14ArchiveReadAhead.mjs','portable/sdl/Th14WebGpuRuntime.mjs']:
        check(R/'runtimes/th12'/name,browser['sourceBindings'][name]['sha256'])
    assert browser['archiveWorkerBuildSha256']==SHA(raw(H/'cpu-worker/build.json'))
    for name,row in browser['archiveWorkerFiles'].items():check(H/'browser-candidate'/name,row['sha256'])
    check(H/'browser-candidate/th14-sdl.wasm',browser['wasmSha256']);check(H/'browser-candidate/th14-sdl.mjs',browser['loaderSha256'])
    check(R/'tools/th14-build-webgpu-release.py',browser['toolSha256'])

    corebuild=load(H/'core-tail-component/build.json');core=load(H/'core-tail-component/check.json')
    assert corebuild['compiled']and corebuild['mainGameResourceObjectUsed']and corebuild['browserBuildSha256']==SHA(raw(H/'browser-candidate/build.json'))
    sources(corebuild,R/'runtimes/th12')
    check(H/'core-tail-component/resources.wasm',corebuild['wasmSha256']);check(H/'core-tail-component/resources.mjs',corebuild['loaderSha256'])
    check(R/'tools/th14-background-resource-build-oct28.py',corebuild['toolSha256'])
    assert corebuild['objectBindings']=={name:digest for name,digest in browser['objectHashes'].items()if name.startswith('th12_web/cpp/game/')}
    for name,digest in corebuild['objectBindings'].items():check(H/'browser-candidate/objects'/(name.replace('/','_')+'.o'),digest)
    assert core['passed']and core['actualProductionCoreOwner']and core['actualIndependentCpuWorker']and core['allCoreAnmAndShtFieldsAndEclDefinitionsEqual']
    assert core['validCoreBatches']==8 and core['rawShtCopies']==0 and core['parsedShtCopies']==12 and core['parsedAnmCopies']==9 and core['parsedEclCopies']==2
    for key in ['invalidJobRejected','duplicateJobsDoNotRead','failedBatchCannotFallback','corruptPacketCannotFallback','subsequentValidCoreLoadsPassed','actualProductionShtParserOnWorker']:assert core[key],key
    assert not core['shotParsingRemainsOnMainConsumer']and not core['actualApplicationControllerTest']
    assert core['fixtureBuildSha256']==SHA(raw(H/'core-tail-component/build.json'))
    check(R/'tools/th14-core-tail-worker-check-oct29.mjs',core['checkerSha256'])

    native=load(H/'native-off-object/check.json')
    assert native['passed']and native['changedSourceObjectByteIdentical']and native['workerFeatureOff']and native['newTransferHeaderNotIncluded']and not native['newNativeApplicationRunClaimed']
    check(R/'runtimes/th12/th12_web/cpp/game/GameResources.cpp',native['sourceSha256'])
    check(H/'native-off-object/GameResources.cpp.o',native['objectSha256']);check(Path(native['originalObject']['path']),native['objectSha256'])
    check(R/'tools/th14-sht-native-off-check-oct29.py',native['toolSha256'])

    normal=load(H/'launcher/served.json');fault=load(H/'fault-corrupt-sht/served.json')
    for served in [normal,fault]:
        assert served['actualServedMainAndWorkerBytesEqual']and served['quietParentAndIframe']and served['mainWasmSha256']==browser['wasmSha256']
    normalmanifest=load(H/'launcher/launcher-report.json');faultmanifest=load(H/'fault-corrupt-sht/launcher-report.json')
    endpoint='runtime/th14/Th14ArchiveDecodeEndpoint.mjs'
    good=raw(R/normalmanifest['files'][endpoint]['path']);bad=raw(R/faultmanifest['files'][endpoint]['path'])
    marker=b"          if (kind === 'sht' && name === 'pl00a.sht') new DataView(parsedResource).setUint32(0, 0, true); // TH14_TEST_ONLY_SHT_TRANSFER_CORRUPTION\n"
    assert bad.count(marker)==1 and bad.replace(marker,b'',1)==good
    rejected=load(H/'browser-ui/fault-observed.json');stopped=load(H/'fault-corrupt-sht/stopped-server.json')
    assert rejected['rejectedBeforeTitle']and rejected['actualCppError']=='SHT resource pl00a.sht: invalid background SHT transfer'
    assert rejected['mainWasmSha256']==browser['wasmSha256']and rejected['quiet']and rejected['testOnlyPacketCorruption']and not rejected['productionFilesModified']
    assert '--port 8241'in stopped['CommandLine']
    stopped_check=load(H/'fault-corrupt-sht/stopped-verification.json')
    assert stopped_check['ownFaultPid']==stopped['ProcessId']and stopped_check['ownFaultProcessAbsent']and stopped_check['faultListenerAbsent']and stopped_check['faultBrowserTabClosed']
    for name in ['corrupt-transfer.txt','corrupt-transfer.jpg','corrupt-transfer-logs.json']:raw(H/'browser-ui'/name)

    flow=load(H/'browser-ui/flow-receipt.json')
    assert flow['mainWasmSha256']==browser['wasmSha256']and flow['runtimeEpoch']==3 and flow['quiet']
    assert flow['normalRecoveryObserved']and flow['replayStartStage']==5 and flow['stage6BattleObserved']and flow['naturalReplayEndObserved']and flow['returnedToReplayList']
    assert flow['launcherReplayRediscoveredAfterReload']and flow['ordinaryDownloadByteIdentical']and not flow['wholeRunFromStage1Accepted']
    assert flow['replayBytes']==110306 and flow['replaySha256']=='866bf6bac02e1c2b9067dacce6705dc71a512eeb2755106474be492a2d23dcdc'
    check(H/'browser-ui/downloaded-replay.rpy',flow['replaySha256'])
    for name in flow['evidenceFiles']:raw(H/'browser-ui'/name)
    logs=load(H/'browser-ui/replay-logs.json')
    assert any('[replay] selected: record stage 5, character 2 subtype 1 difficulty 2, 110306 bytes'in row['message']for row in logs)
    assert not any('invalid background SHT transfer'in row['message']for row in logs)
    for proof in [case,core,native,browser,flow]:assert not proof['completeGame']and not proof['nativeEquivalent']

    return dict(verifiedFiniteShtWorkerIntegration=True,actualProductionParserAndResourceConsumer=True,
        files=6,groups=60,shots=283,malformedFailureCancelAndRecoveryControls=125,multiResourceBatches=4,
        parsedShtCopies=18,mainRawShtReads=0,allFieldsAndCanonicalPacketBytesEqual=True,
        actualCoreOwnerBatches=8,coreParsedShtCopies=12,coreRawShtCopies=0,
        browserCompiledUnits=146,browserMainWasmSha256=browser['wasmSha256'],cpuWorkerWasmSha256=worker['wasmSha256'],
        nativeWorkerOffObjectByteIdentical=True,newNativeApplicationRunsClaimed=0,
        actualBrowserCorruptShtRejectedBeforeTitle=True,testOnlyFaultServerStopped=True,
        browserNormalRecoveryObserved=True,browserReplayStartStage=5,browserStage6BattleAndNaturalEndObserved=True,
        browserReturnReloadRediscoveryAndDownloadObserved=True,browserWholeRunFromStage1Accepted=False,
        browserQuiet=True,ordinaryIndependentOriginalTimingAccepted=False,nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),
        limitations=['The isolated field and core-owner component tests use declared packet-provider services; they are not Application controller runs.',
            'The current ordinary browser run starts at stage5. Whole-run retail pixels, PCM, continuous frame rate and all-mode fidelity remain unaccepted.',
            'Independent original loading/RNG timing and ordinary original cold Replay initialization remain open. Import/link/template/GPU preparation retains its owning caller.'],
        completeGame=False,nativeEquivalent=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    result=evidence();target=R/'docs/porting/th14-sht-worker-verified-oct29.json'
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:value for key,value in result.items()if key!='bindings'},ensure_ascii=False))


if __name__=='__main__':main()
