"""Recompute finite selected-player worker, lifecycle and browser evidence."""
from pathlib import Path
import argparse, hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/native-frame-readback-oct28'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def evidence():
    bindings = {}

    def raw(path):
        path = path.resolve(strict=True)
        assert path.is_relative_to(R)
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    def digest(path, wanted):
        assert SHA(raw(path)) == wanted, str(path)

    home = H / 'selected-player-browser-candidate-v2'
    build = load(home / 'build.json')
    assert build['basePublishedCommit'] == '77158662e01747a90f0bfc66a692b8e03add59fe'
    assert build['compiledUnits'] == 146 and build['reusedObjectCount'] == 0
    assert build['rootUnrelatedResourceCryptExcluded'] and not build['retailAssetsIncluded']
    for name, row in build['sourceBindings'].items():
        digest(home / 'source' / name, row['sha256'])
    for name, value in build['objectHashes'].items():
        digest(home / 'objects' / (name.replace('/', '_') + '.o'), value)
    for name in ('game/GameSessionResources.cpp', 'game/GameSessionResources.hpp', 'game/GameSession.cpp', 'sdl/Application.cpp'):
        name = 'th12_web/cpp/' + name
        digest(R / 'runtimes/th12' / name, build['sourceBindings'][name]['sha256'])
    assert build['sourceBindings']['th12_web/cpp/game/ResourceCrypt.cpp']['sha256'] == 'd57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    digest(R / 'tools/th14-build-webgpu-release.py', build['toolSha256'])
    digest(home / 'th14-sdl.wasm', build['wasmSha256'])
    digest(home / 'th14-sdl.mjs', build['loaderSha256'])
    previous = load(H / 'boot-anm-browser-candidate/build.json')
    assert build['archiveWorkerFiles'] == previous['archiveWorkerFiles']
    for name, row in build['archiveWorkerFiles'].items():
        digest(home / name, row['sha256'])
    worker = load(home / 'archive-worker/build.json')

    component = H / 'selected-player-resource-component'
    fixture = load(component / 'build.json')
    checks = load(component / 'check.json')
    assert checks['passed'] and checks['selectionCases'] == 6
    assert checks['validWorkerImports'] == 11 and checks['corruptPacketImports'] == 1
    assert checks['totalParsedCopies'] == 12 and checks['synchronousConsumerCases'] == 6
    assert checks['duplicateCompletionsRejected'] == 6
    for key in ('wrongOwnerRejectedWithoutCopy', 'cancelledOwnerRejectedWithoutCopy', 'replacedOwnerRejectedWithoutCopy', 'failedBatchCannotFallback', 'corruptPacketCannotFallback', 'subsequentValidLoadsPassed', 'actualProductionGameSessionResourcesObject', 'actualIndependentCpuWorker'):
        assert checks[key], key
    assert not checks['actualApplicationControllerTest']
    assert [row['name'] for row in checks['rows']] == ['pl00.anm', 'pl00b.anm', 'pl01.anm', 'pl01b.anm', 'pl02.anm', 'pl02b.anm']
    assert all(row['allParsedFieldsAndBytesEqual'] and row['callerDidNotParse'] and row['duplicateRejected'] for row in checks['rows'])
    assert checks['browserBuildSha256'] == fixture['browserBuildSha256'] == SHA(raw(home / 'build.json'))
    digest(component / 'build.json', checks['fixtureBuildSha256'])
    digest(component / 'resources.wasm', fixture['wasmSha256'])
    digest(component / 'resources.mjs', fixture['loaderSha256'])
    digest(R / 'tools/th14-selected-player-worker-check-oct29.mjs', checks['checkerSha256'])
    digest(R / 'tools/th14-background-resource-build-oct28.py', fixture['toolSha256'])
    assert fixture['objectBindings'] == {name: value for name, value in build['objectHashes'].items() if name.startswith('th12_web/cpp/game/')}
    for name, value in fixture['sourceBindings'].items():
        digest(component / 'source' / name, value)
        if '/tests/' in name:
            digest(R / 'runtimes/th12' / name, value)

    core = load(H / 'selected-player-native-core/observer-build.json')
    assert core['engineSourcesRecompiledForThisLink'] == 141 and core['engineObjectsReusedForThisLink'] == 0
    assert core['browserBuildSha256'] == SHA(raw(home / 'build.json')) and core['unrelatedRootResourceCryptExcluded']
    digest(R / 'tools/th14-build-snapshot-core-oct29.py', core['buildToolSha256'])
    digest(H / 'selected-player-native-core/observer.wasm', core['wasmSha256'])
    for name, value in {**core['sourceHashes'], **core['headerHashes']}.items():
        assert build['sourceBindings'][name]['sha256'] == value
    for row in core['objectBindings']:
        digest(Path(row['path']), row['sha256'])

    def native_build(backend):
        directory = H / ('selected-player-native-' + backend + '-build')
        result = load(directory / 'build.json')
        assert result['coreBuildSha256'] == SHA(raw(H / 'selected-player-native-core/observer-build.json'))
        assert result['coreObjects'] == core['objectBindings']
        digest(directory / 'application.wasm', result['wasmSha256'])
        digest(directory / 'build-tool.py', result['toolSha256'])
        for name, row in result['sourceBindings'].items():
            digest(R / name, row['sha256'])
        for name, value in result['newObjects'].items():
            digest(directory / name, value)
        return result

    native_builds = {backend: native_build(backend) for backend in ('gles', 'webgpu')}

    def run(name, backend):
        directory = H / name
        result = load(directory / 'report.json')
        assert result['completed'] and not result['error'] and len(result['checks']) == 7
        assert all(row['passed'] for row in result['checks'])
        assert result['applicationTicks'] == 2264 and result['physicalAudioDevicesOpened'] == 0
        assert result['actualProductionApplicationAndDevices'] and not result['browserRun']
        assert result['wasmSha256'] == native_builds[backend]['wasmSha256']
        digest(H / ('selected-player-native-' + backend + '-build/build.json'), result['buildReportSha256'])
        digest(R / 'tools/th14-native-application-process-host-oct27.py', result['toolSha256'])
        digest(R / ('tools/th14-native-' + backend + '-context.py'), result['hostToolSha256'])
        digest(R / 'artifacts/th14/native-frame-readback-oct27/idle-demo-scenario.json', result['scenarioSha256'])
        for capture in result['captures']:
            digest(directory / capture['file'], capture['sha256'])
            digest(directory / capture['liveAnimations']['file'], capture['liveAnimations']['sha256'])
        return result

    gles = run('selected-player-native-gles-baseline', 'gles')
    webgpu = run('selected-player-native-webgpu-baseline', 'webgpu')
    assert gles['frames'] == webgpu['frames'] == 2264
    for key in ('rows', 'actions', 'checks', 'captures', 'initialSave', 'finalSave', 'files', 'pcmFrames', 'pcmSha256', 'finalReferenceState', 'initialLoadingObservations'):
        assert gles[key] == webgpu[key], key
    assert gles['pcmFrames'] == 1508352
    assert gles['captures'][-1]['liveAnimations']['count'] == 339
    observations = gles['initialLoadingObservations']
    assert any(row['words'][5] == 3 and row['words'][7] == 0 and row['words'][11] == 0 for row in observations)
    first = next(index for index, row in enumerate(observations) if row['words'][11])
    before, after = observations[first - 1]['words'], observations[first]['words']
    assert before[5] == 2 and before[6] == before[7] == 1 and before[11] == 0
    assert after[5] == 1 and after[11] == 1
    for kind in ('player', 'decode', 'resume'):
        result = run('selected-player-native-pause-' + kind, 'gles')
        assert result['frames'] == 2269 and result['workerPauseKind'] == kind
        events = result['workerPauseEvents']
        assert [row['kind'] for row in events] == ['suspend', 'stale-callback-returned', 'resume']
        assert events[1]['pendingStatePreserved'] and events[0]['words'] == events[2]['words']
        assert events[2]['frame'] - events[0]['frame'] == 5
        for key in ('initialSave', 'finalSave', 'files', 'pcmFrames', 'pcmSha256', 'finalReferenceState'):
            assert result[key] == gles[key], (kind, key)
        # Rows are sampled on host-frame boundaries. Compare only samples at
        # the same Application tick, explicitly accounting for five skipped
        # host frames; do not equate shifted host-frame samples.
        reference_rows = {row['frame']: row['state'] for row in gles['rows']}
        paired = []
        for row in result['rows']:
            if events[0]['frame'] <= row['frame'] < events[2]['frame']:
                continue
            tick = row['frame'] - (5 if row['frame'] >= events[2]['frame'] else 0)
            if tick in reference_rows:
                assert row['state'] == reference_rows[tick]
                paired.append(tick)
        assert len(paired) == (123 if kind == 'decode' else 124)
        assert result['checks'] == [{**row, 'frame': row['frame'] + (5 if row['frame'] >= events[0]['frame'] else 0)} for row in gles['checks']]
        for actual, expected in zip(result['captures'], gles['captures'], strict=True):
            assert (actual['sha256'], actual['referenceState'], actual['liveAnimations']) == (expected['sha256'], expected['referenceState'], expected['liveAnimations'])
            assert raw(H / ('selected-player-native-pause-' + kind) / actual['file']) == raw(H / 'selected-player-native-gles-baseline' / expected['file'])

    transport = load(H / 'selected-player-launcher/http-check.json')
    assert transport['verifiedTransport'] and transport['routes'] == 139 and len(transport['requests']) == 27
    served = load(H / 'selected-player-launcher/served-restored.json')
    assert served['wasmSha256'] == build['wasmSha256'] and served['quietInjectedIntoParentAndIframe'] and served['actualServedMainAndWorkerBytesEqual']
    for request in served['requests']:
        digest(home / request['route'].rsplit('/', 1)[-1], request['sha256'])
    fault = load(H / 'selected-player-fault-pl00/launcher-report.json')
    assert fault['testOnlyFaultInjection'] and not fault['productionFilesModified'] and fault['wasmSha256'] == build['wasmSha256']
    assert fault['faultResource'] == 'pl00.anm'
    digest(R / 'tools/th14-boot-worker-control-oct29.py', fault['controlToolSha256'])
    endpoint = raw(R / fault['files']['runtime/th14/Th14ArchiveDecodeEndpoint.mjs']['path'])
    injected = b"      if (Array.isArray(message.names) && message.names.includes('pl00.anm')) throw new Error('TH14_TEST_ONLY_SELECTED_PLAYER_REJECTION');\n"
    assert endpoint.count(injected) == 1 and endpoint.replace(injected, b'', 1) == raw(home / 'Th14ArchiveDecodeEndpoint.mjs')
    assert len(load(H / 'selected-player-fault-pl00/served.json')['checks']) == 3
    stopped = load(H / 'selected-player-fault-pl00/stopped-server.json')
    assert 'selected-player-fault-pl00/launcher-report.json' in stopped['CommandLine']
    ui = H / 'selected-player-browser-ui'
    flow = load(ui / 'flow-receipt.json')
    assert all(flow[key] for key in ('titleObserved', 'automaticDemoObserved', 'shortReplayNaturalEndObserved', 'returnedReplayList', 'selectedPlayerRejectionObserved', 'normalWorkerRestored', 'sakuyaBHardStage4Observed', 'replayAgainReloadedStage4', 'finalReplayListObserved'))
    assert flow['selectedShortHud'] == dict(score=3100, lives=1, powerHundredths=103, graze=2)
    for name in ('title', 'automatic-demo', 'short-natural-end', 'returned-replay-list', 'selected-player-rejected', 'restored-title', 'restored-replay-list', 'sakuya-b-stage4-running', 'sakuya-b-stage4-paused', 'sakuya-b-stage4-replayed', 'final-replay-list'):
        assert raw(ui / (name + '.jpg'))[:3] == b'\xff\xd8\xff'
        ax = raw(ui / (name + '.ax.txt')).decode()
        assert '本机测试静音' in ax and 'runtimeEpoch=' in ax
        if name == 'selected-player-rejected':
            assert 'TH14 background player resource decode failed' in ax
        else:
            assert '音频 0ms' in ax
    raw(ui / 'selected-player-rejected.logs.json')
    return dict(verifiedFiniteSelectedPlayerWorker=True, selections=[row['name'] for row in checks['rows']], compiledBrowserUnits=146, compiledNativeCoreUnits=141, mainWasmBytes=build['wasmBytes'], mainWasmSha256=build['wasmSha256'], workerWasmBytes=worker['wasmBytes'], workerWasmSha256=worker['wasmSha256'], workerFilesByteIdenticalToColdBootBuild=True, validWorkerImports=11, corruptPacketImports=1, synchronousConsumerCases=6, ownerControlsPassed=True, actualNativeFramesPerBackend=2264, actualNativeAssertionsPerBackend=7, silentPcmFrames=1508352, actualNativePauseKinds=['player', 'decode', 'resume'], controlledHostFramesSkippedPerPause=5, initialPlayerCpuBeforeUploadObserved=True, playerAppearsAfterFile9CompletionObserved=True, actualBrowserSelectedPlayerRejectionObserved=True, actualBrowserReplayAgainAndReturnObserved=True, normalWorkerRestored=True, nativeTestsUseDeclaredCallbackClock=True, nativeTestsUseArchiveWorkerFeatureOff=True, physicalBrowserWorkerPauseAccepted=False, allLoadingWorkOnCpuWorker=False, originalIndependentThreadSchedulingAccepted=False, currentBuildInheritsFrozenFullCampaign=False, completeBrowserAcceptance=False, completeGame=False, nativeEquivalent=False, verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    proof = evidence()
    target = R / 'docs/porting/th14-selected-player-worker-verified-oct29.json'
    if args.check:
        assert json.loads(target.read_bytes()) == proof
    else:
        target.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: proof[key] for key in ('verifiedFiniteSelectedPlayerWorker', 'compiledBrowserUnits', 'actualBrowserReplayAgainAndReturnObserved', 'completeGame')}))


if __name__ == '__main__':
    main()
