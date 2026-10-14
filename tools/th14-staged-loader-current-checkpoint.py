"""Bind fresh production267 evidence, without rerunning or promoting mismatches."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / 'runtimes/th12/th12_web'
GAME_INPUTS = Path('H:/Games/th/14').resolve()
DOC = ROOT / 'docs/porting'
bindings = {}


def bind(name, digest=None, size=None):
    path = Path(name)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT) or path.is_relative_to(GAME_INPUTS), str(path)
    key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()
    if key not in bindings:
        with path.open('rb') as stream:
            h = hashlib.file_digest(stream, 'sha256').hexdigest()
        bindings[key] = {'bytes': path.stat().st_size, 'sha256': h}
    row = bindings[key]
    if digest is not None:
        assert row['sha256'] == digest, key
    if size is not None:
        assert row['bytes'] == size, key
    return row


def load(name, digest=None):
    bind(name, digest)
    path = Path(name)
    return json.loads((path if path.is_absolute() else ROOT / path).read_text(encoding='utf-8-sig'))


def rows(entries):
    for name, item in entries.items() if isinstance(entries, dict) else ((x['path'], x) for x in entries):
        bind(name, item['sha256'], item.get('bytes'))


def include_closure(path, seen=None):
    seen = set() if seen is None else seen
    path = path.resolve()
    if path in seen:
        return seen
    seen.add(path)
    bind(path)
    for name in re.findall(r'^\s*#\s*include\s*"([^"]+)"', path.read_text(encoding='utf-8-sig'), re.M):
        include_closure(path.parent / name, seen)
    return seen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='th14-staged-loader-current-checkpoint-oct14.json')
    parser.add_argument('--pixels-report', default='docs/porting/th14-deferred-capture-success-dirty-verified-oct14.json')
    parser.add_argument('--pixels-review', default='artifacts/th14/deferred-capture-independent-review-oct14/candidate-complete-review.json')
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9-]+\.json', args.output)
    output = DOC / args.output
    assert not output.exists(), 'New checkpoint only; preserve earlier receipts'
    engine_path = ROOT / 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'
    engine = load(engine_path)
    assert engine['title'] == 14 and engine['engineSources'] == len(engine['sources']) == 141
    source = engine['sourceHashes']
    assert len(source) == 267
    for name, digest in source.items():
        bind(RT / name, digest)
    bind(engine_path.with_name('engine-th14.wasm'), engine['sha256'], engine['bytes'])
    engine_sha = bind(engine_path)['sha256']

    raw_path = DOC / 'th14-staged-loader-production-raw-evidence-verified-oct14.json'
    raw = load(raw_path, '5350554b30bf448c33dd2e5df62b28f8fd2914b1eaa8abff54b05545ab6feb82')
    assert raw['productionRawEvidenceVerified'] and raw['sourceHashes'] == source
    assert raw['sourceFilesVerified'] == 267 and raw['engineObjectsVerified'] == 141
    assert raw['bindingCount'] == len(raw['bindings']) == 3290
    bind('tools/th14-staged-loader-production-raw-evidence-check.py', raw['toolSha256'])
    object_hashes = {}
    headers = sorted(n for n in source if not n.endswith('.cpp'))
    header_key = hashlib.sha256('\n'.join(n + ' ' + source[n] for n in headers).encode()).hexdigest()
    for name in engine['sources']:
        path = engine_path.parent / 'objects-th14' / (name.replace('/', '_') + '.o')
        object_hashes[name] = bind(path, raw['objectHashes'][name])['sha256']
        expected_key = hashlib.sha256(json.dumps([engine['compileFlags'], header_key, source[name]], separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        key_path = Path(str(path) + '.key')
        bind(key_path)
        assert key_path.read_text() == raw['objectKeys'][name] == expected_key
    custody = load('artifacts/th14/staged-loader-production-raw-evidence-oct14/native-input-custody.json', '5688e69fcd9f379e15d9d97f1e27e644fd81043ba387654445695d6b3f1f148a')
    assert custody['nativeInputCustodyVerified'] and len(custody['bindings']) == 16
    rows(custody['bindings'])
    review = load('artifacts/th14/staged-loader-production-raw-evidence-oct14/independent-code-review.json')
    assert review['independentReadOnlyReviewPassed'] and review['actualIssues'] == []
    assert review['mainBindingsDirectlyVerified'] == 3290 and review['inputCustodyBindingsDirectlyVerified'] == 16
    assert review['hashFailures'] == review['sizeFailures'] == 0
    bind(review['reviewedReceipt'], review['receiptSha256'])
    bind(review['reviewedNativeInputCustody'], review['nativeInputCustodySha256'])

    target = load('runtimes/th14/target.json')
    archive = bind(target['dataArchives']['th14.dat']['path'], size=target['dataArchives']['th14.dat']['bytes'])
    labels = [('reimua-lunatic', 'th14_udzp01', 90793, 750), ('reimub-lunatic', 'th14_udzp02', 98074, 750),
              ('reimua-extra', 'th14_udzp07', 39458, 0), ('sakuyaa-normal', 'th14_udzp05', 96016, 750)]
    production = {}
    for short, replay_name, count, inactive in labels:
        label = short + '-staged-loader-oct14'
        home = ROOT / 'artifacts/th14/staged-loader-production-playback' / label
        run = load(home / 'report.json')
        assert run['productionPlaybackVerified'] and run['candidatePlaybackEnded'] and run['phase'] == 4
        assert not any(run[k] for k in ['error', 'gameOverRequested', 'unsupported', 'skipped', 'forcedProgression', 'invulnerabilityOverride', 'gpuPrepared'])
        assert run['allPhysicalCallbacksRetained'] and run['frames'] == run['selectedCallbacks'] == count and run['inactiveCallbacks'] == inactive
        assert run['sourceHashes'] == source and run['objectHashes'] == object_hashes
        assert run['archiveSha256'] == archive['sha256'] and run['engineBuildSha256'] == engine_sha
        assert load(home / 'engine-build.json', engine_sha) == engine
        bind('tools/th14-staged-loader-production-replay-check.mjs', run['toolSha256'])
        for name, digest in run['fixtureDependencyHashes'].items():
            bind(name, digest)
        for name, digest in run['fixtureHashes'].items():
            bind(RT / 'tests/cpp' / name, digest)
        for name, key in [('production-clock-fixture.cpp', 'generatedFixtureSha256'), ('production-replay.wasm', 'wasmSha256'),
                          ('selected-state.u32', 'selectedStateSha256'), ('callback-active.u8', 'callbackActiveSha256')]:
            bind(home / name, run[key])
        bind('artifacts/th14/public-replay-reference/' + replay_name + '.rpy', run['replaySha256'])
        bind('artifacts/th14/public-replay-reference/' + replay_name + '-source.json', run['replaySourceSha256'])
        case = next(x for x in raw['cases'] if x['label'] == label)
        assert case['physicalCallbacks'] == count and case['inactiveCallbacks'] == inactive
        for key in ['allDifferences', 'nativeExpectedRaw32']:
            if key in case:
                rows([case[key]])
        if case['nativeRawComparisonAvailable']:
            assert case['rawGameplayDifferences'] == (0 if short == 'reimua-extra' else 10)
            assert case['allNativeCallbacksPaired'] and not case['comparisonPassed']
            assert case['allGameplayDifferencesDuringInactiveCallbacks']
        else:
            assert short == 'reimub-lunatic'
        production[label] = run
    obj = raw['productionObjects']
    assert obj['currentProductionObjectEvidenceVerified'] and not obj['comparisonPassed']
    assert (obj['retainedDetailDifferences'], obj['inactiveLoadingDetailDifferences'], obj['activeBattleDetailDifferences']) == (65, 57, 8)
    object_home = ROOT / 'artifacts/th14/staged-loader-production-objects/reimua-lunatic-oct14'
    object_run = load(object_home / 'report.json')
    assert object_run['engineBuild'] == engine and object_run['objectHashes'] == object_hashes
    assert len(object_run['detailDifferences']) == 65 and len(object_run['differences']) == 10
    for name, key in [('reference.wasm', 'wasmSha256'), ('late-combat-fixture.cpp', 'fixtureSha256'), ('portable-details.json', 'rawDetailSha256'),
                      ('portable-state.u32', 'portableStateSha256'), ('native-state.u32', 'nativeStateSha256')]:
        bind(object_home / name, object_run[key])
    bind('tools/th14-staged-loader-production-objects-check.mjs', object_run['toolSha256'])

    asan_home = ROOT / 'artifacts/th14/staged-loader-production-sanitized/staged-loader-oct14'
    asan = load(asan_home / 'report.json')
    assert asan['sanitizerMatrixVerified'] and asan['sourceHashes'] == source and asan['engineBuildSha256'] == engine_sha
    assert len(asan['cases']) == 4 and '-fno-sanitize-recover=all' in asan['sanitizerFlags']
    assert load(asan_home / 'engine-build.json', engine_sha) == engine
    for name, key in [('sanitized-clock-fixture.cpp', 'generatedFixtureSha256'), ('sanitized.mjs', 'loaderSha256'), ('sanitized.wasm', 'wasmSha256')]:
        bind(asan_home / name, asan[key])
    for name, digest in asan['objectSha256'].items():
        bind(asan_home / 'objects' / (name.replace('/', '_') + '.o'), digest)
    for name, digest in asan['fixtureDependencyHashes'].items():
        bind(name, digest)
    for item, (short, replay_name, count, inactive) in zip(asan['cases'], labels):
        assert item['file'] == replay_name + '.rpy' and item['frames'] == count and item['sanitizerPassed'] and item['allRaw32WordsEqual']
        run = production[short + '-staged-loader-oct14']
        assert item['selectedStateSha256'] == run['selectedStateSha256'] and item['callbackActiveSha256'] == run['callbackActiveSha256']
        bind(asan_home / (item['file'] + '.state.u32'), item['selectedStateSha256'])
        bind(asan_home / (item['file'] + '.active.u8'), item['callbackActiveSha256'])
        bind('artifacts/th14/staged-loader-production-playback/' + short + '-staged-loader-oct14/report.json', item['playbackReportSha256'])
    bind('tools/th14-staged-loader-production-sanitized-check.mjs', asan['toolSha256'])

    normal_home = ROOT / 'artifacts/th14/natural-input/normal-sakuyaa-staged-loader-oct14'
    normal = load(DOC / 'th14-natural-storage-normal-sakuyaa-staged-loader-oct14-observed-oct14.json')
    assert load(normal_home / 'post-storage/report.json') == normal
    prep = load(normal_home / 'staged-driver-prepared.json')
    assert prep['sourceHashes'] == source and prep['engineBuildSha256'] == normal['engineBuildSha256'] == engine_sha
    assert normal['diagnosticEvidenceVerified'] and normal['passed'] and not normal['forcedProgression'] and not normal['invulnerabilityOverride']
    assert (normal['naturalInputFrames'], normal['endingIndex'], normal['endingFrames'], normal['finalPhase'], normal['titleScreen']) == (95220, 5, 3737, 0, 1)
    assert normal['archiveSha256'] == archive['sha256']
    for name, key in [('held-keys.u32', 'inputsSha256'), ('storage-clock-fixture.cpp', 'fixtureSha256'), ('storage-clock-driver.mjs', 'toolSha256')]:
        bind(normal_home / name, normal[key])
    bind(normal_home / 'report.json', prep['archivedInputReportSha256'])
    bind(normal_home / 'engine-build.json', engine_sha)
    bind('tools/th14-staged-loader-production-normal-storage-check.mjs', prep['toolSha256'])
    bind('tools/th14-normal-natural-storage-check.mjs', prep['originalDriverSha256'])
    for name, key in [('storage.wasm', 'wasmSha256'), ('scoreth14.dat', 'scoreSha256'), ('retail-rewritten.dat', 'scoreSha256'),
                      ('production.raw', 'rawSha256'), ('retail-loaded.raw', 'rawSha256'), ('menu-saved.rpy', 'menuReplaySha256')]:
        bind(normal_home / 'post-storage' / name, normal[key])
    before_path = normal_home / 'post-storage/before-serialization.raw'
    bind(before_path)
    canonical = bytearray(before_path.read_bytes())
    assert len(canonical) == normal['rawBytes'] == 7 * 0x5298 + 0x42c
    for index in range(7):
        struct.pack_into('<I', canonical, index * 0x5298 + 12, index)
    for index in range(8):
        offset, length = index * 0x5298, 0x5298 if index < 7 else 0x42c
        struct.pack_into('<I', canonical, offset + 4, sum(canonical[offset + 8:offset + length]) & 0xffffffff)
    assert bytes(canonical) == (normal_home / 'post-storage/production.raw').read_bytes()
    native_score = load(normal_home / 'post-storage/native.json')
    assert native_score == normal['native'] and native_score['passed']
    bind('tools/th14-natural-score-native.py', normal['nativeToolSha256'])
    bind('tools/th14-browser-score-native.py', native_score['parentSourceSha256'])
    bind('H:/Games/th/14/th14.exe', native_score['nativeExecutableSha256'])
    storage_fixture = RT / 'tests/cpp/th14-normal-natural-storage-fixture.cpp'
    bind(storage_fixture, 'd11e13231a3d44ccdb54c665ba1f4e7f5a81ab4aa017b720ee18e773b301ab93')
    storage_closure = include_closure(storage_fixture)

    v3 = ROOT / 'artifacts/th14/staged-loader-integration-oct14/cancel-v3'
    cancel = load(v3 / 'cancellation-verified.json')
    assert cancel['privateCancellationVerified'] and len(cancel['cases']) == 8
    assert set(cancel['privateSourceHashes']) == set(source)
    private_difference = [n for n in source if source[n] != cancel['privateSourceHashes'][n]]
    assert private_difference == ['cpp/game/GameSession.cpp']
    private_build = load(v3 / 'private-build.json', cancel['sourceBuildSha256'])
    bind(v3 / 'staged-loader-integration.wasm', cancel['wasmSha256'])
    bind(v3 / 'source/runtimes/th12/th12_web/tests/cpp/th14-staged-loader-integration-fixture.cpp', private_build['fixtureSha256'])
    bind(v3 / 'frozen-source.json', 'd754a50cc94ea8d962b13e595555dba17a6c3621cfda1dbb6eed8772dc446eed')
    reset = load(DOC / 'th14-deferred-reset-policy-unit-verified-oct14.json')
    assert reset['privateResetPolicyVerified'] and len(reset['cases']) == 4
    rows(reset['sourceBindings'])
    reset_session = ROOT / 'artifacts/th14/deferred-reset-policy-unit-oct14/source/runtimes/th12/th12_web/cpp/game/GameSession.cpp'
    private_text = reset_session.read_text()
    comments = '    // Whole-session/direct-stage replacement cancels old copy requests.\n    // Ordinary VM clear and overlapping NextStage retain the queue.\n'
    actual_text = (RT / 'cpp/game/GameSession.cpp').read_text()
    assert actual_text.replace(comments, '', 1) == private_text
    assert all(x['queueCancelled'] for x in reset['cases'][:3]) and reset['cases'][3]['ordinaryManagerClearRetainsQueue']

    sdl_home = ROOT / 'runtimes/th14/th14_web/artifacts/sdl3-release'
    sdl = load(sdl_home / 'build.json')
    assert sdl['title'] == 14 and sdl['releaseProfile'] and len(sdl['sources']) == 146 and len(sdl['headers']) == 149
    assert sdl['sha256'] == '64b46da7c4aa1af2426d024c176e8c77b9ecae5a3da13a1eeea6c648ee82ca54'
    for group in ['sources', 'headers']:
        for name, digest in sdl[group].items():
            bind(ROOT / 'runtimes/th12' / name, digest)
    bind(sdl_home / 'th11.wasm', sdl['sha256'], sdl['bytes'])
    bind(sdl_home / 'th11.mjs', sdl['loaderSha256'])
    assert not any(x['name'].startswith('th11_probe_') or x['name'] in ['th11_tick', 'th11_audio_probe', 'th11_audio_samples'] for x in sdl['exports'])
    runtime = load(DOC / 'th14-launcher-runtime-prepared-staged-capture-oct14.json')
    package = load(DOC / 'th14-launcher-preview-prepared-staged-capture-oct14.json')
    assert runtime['passed'] and runtime['build'] == sdl and len(runtime['files']) == 40
    assert package['passed'] and len(package['files']) == 127
    for name, row in runtime['files'].items():
        bind(Path(runtime['out']) / name, row['sha256'], row['bytes'])
    for name, row in package['files'].items():
        bind(Path(package['site']) / name, row['sha256'], row['bytes'])
    for name, item in package['moduleSources'].items():
        bind(item['source'], item['sourceSha256'])
    bind(Path(package['site']) / 'files.json')
    bind(DOC / 'th14-launcher-runtime-prepared-staged-capture-oct14.json', package['runtimeManifestSha256'])
    bind('artifacts/th14/staged-loader-checkpoint-oct14/attempt01-report-path-failure/checker.py')
    bind('artifacts/th14/staged-loader-checkpoint-oct14/attempt01-report-path-failure/failure.json')

    pixels = None
    if (ROOT / args.pixels_report).exists() and (ROOT / args.pixels_review).exists():
        candidate = load(args.pixels_report)
        candidate_review = load(args.pixels_review, '5616d773a90879eaa337a524adaa73314cb492aadaaf46d8c4a8b2ab6ad7639d')
        assert candidate['privateSuccessDirtyCandidateVerified'] and candidate_review['candidatePhysicalReviewPassed'] and candidate_review['independentSourceReviewPassed']
        assert candidate['cases'] == candidate['exactNativeFullBuffers'] == 8 and candidate['comparedRawBytes'] == 5242880 and candidate['differentBytes'] == 0
        assert candidate['candidateHelperSha256'] == sdl['headers']['th12_web/cpp/sdl/ApplicationCaptureTh14.hpp']
        rows(candidate['bindings']); rows(candidate['stateBindings']); rows(candidate_review['bindings'])
        pixel_home = ROOT / 'artifacts/th14/deferred-capture-success-dirty-oct14'
        build = load(pixel_home / 'webgl-build.json')
        assert build['wasmSha256'] == candidate['wasmSha256']
        bind(candidate['candidateHelperPath'], candidate['candidateHelperSha256'])
        native = load('artifacts/th14/deferred-capture-pixels-oct14/native.json')
        for index, comparison in enumerate(candidate['comparisons']):
            assert comparison['strictNativeEqual'] and comparison['differentBytes'] == 0
            bind(pixel_home / 'webgl-capture' / f'portable-{index:03}.pixels', comparison['candidateSha256'], comparison['bytes'])
            bind(ROOT / 'artifacts/th14/deferred-capture-pixels-oct14' / native['cases'][index]['pixelFile'], comparison['nativeSha256'], comparison['bytes'])
        pixels = {'privateCandidatePhysicalPixelsVerified': True, 'cases': 8, 'bytes': 5242880, 'differentBytes': 0,
                  'sameHelperBytesAsCurrentProduction': True, 'finalReleaseBrowserVerified': False,
                  'scope': candidate_review['referenceDomain']}

    result = {'diagnosticCheckpointVerified': True, 'completeGame': False, 'nativeEquivalent': False,
      'sourceFilesVerified': 267, 'sourceHashes': source, 'engineObjectsVerified': 141, 'objectHashes': object_hashes,
      'freshProductionReplays': raw['cases'], 'fullObjects': obj,
      'rawReceipt': {'bindingsPreviouslyVerified': 3290, 'sha256': bind(raw_path)['sha256']},
      'custodySupplement': {'bindingsDirectlyReverified': 16, 'scope': custody['scope']},
      'secondReview': {'mainBindingsDirectlyVerified': 3290, 'custodyBindingsDirectlyVerified': 16, 'passed': True},
      'sanitizers': {'cases': asan['cases'], 'scope': asan['scope'], 'rawEqualityMeans': 'ASAN versus fresh same-source uninstrumented output, not Native equality'},
      'ordinaryNormal': {'frames': 95220, 'endingIndex': 5, 'endingFrames': 3737, 'scoreBytes': 22379,
        'recordHeaderCanonicalizationRecomputed': True, 'nativeScoreCodecBytesEqual': True,
        'currentStorageFixtureClosureFiles': len(storage_closure), 'newCurrentFixtureBindingAdded': 'th14-normal-natural-storage-fixture.cpp was not recorded by the original storage report; its present bytes/include closure are separately bound here, not claimed as a past recorded dependency.',
        'inputReportRole': 'Archived old natural input only; current result is post-storage/report and staged-driver-prepared.',
        'clockMode': prep['clockMode'], 'captureRetirement': prep['captureRetirement'], 'nativeOrdinaryEndingVerified': False},
      'privateCancellationSupport': {'revision': 'cancel-v3', 'cases': 8, 'privateSourceDifferencesFromProduction': private_difference,
        'productionCancellationExecutionVerified': False, 'actualGpuCancellationExecuted': False},
      'resetPolicySupport': {'privateCases': 4, 'actualProductionSourceDiffersOnlyTwoComments': True,
        'ordinaryManagerClearRetainsQueue': True, 'scope': reset['scope']},
      'sdlRelease': {'sha256': sdl['sha256'], 'bytes': sdl['bytes'], 'sourceFiles': 146, 'headers': 149, 'compiled': True, 'browserVerified': False},
      'preparedRuntimeFiles': 40, 'preparedLauncherFiles': 127, 'candidatePixels': pixels,
      'finalReleaseBrowserVerified': False, 'prior265CheckpointInherited': False,
      'bindingSelection': 'Current sources/objects/keys, actual modules/input/output/fixture closures, all sixteen Native custody files, current release/runtime/site and specific supporting receipts are directly verified. Duplicate archival source/object trees from the3290 receipt are not independently rehashed here; its immutable receipt and second review retain that separate claim.',
      'externalInputs': {name: row for name, row in bindings.items() if Path(name).is_absolute()},
      'bindings': bindings, 'bindingCount': len(bindings), 'toolSha256': bind(Path(__file__))['sha256'],
      'scope': 'New current267 production checkpoint.10/10/0 Native gameplay differences and65 full-object differences remain failed; ReimuB has no matching Native oracle. Controlled host time/no-target headless draws and private cancellation/reset supports are distinct from real SDL scheduling/teardown. Copy fixture8 full buffers do not prove complete compositor/game graphics/audio1:1 or final64b46 browser loading. No Native process, compiler, gameplay, browser or external publication runs occur in this verifier.'}
    # bind(__file__) may add one row; calculate the final count afterward.
    result['bindingCount'] = len(bindings)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'diagnosticCheckpointVerified': True, 'sources':267, 'objects':141, 'bindings':len(bindings),
                      'report':output.relative_to(ROOT).as_posix(), 'sha256':bind(output)['sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
