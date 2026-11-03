"""Bind the integrated camera publication fix to finite component and replay evidence."""
from pathlib import Path
import argparse, hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/camera-publication-candidate-v3-nov04'
OLD = R / 'artifacts/th14/camera-publication-candidate-v2-nov04'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path, default=R / 'docs/porting/th14-camera-publication-nov04.json')
    args = parser.parse_args()
    bindings = {}

    def read(path):
        raw = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(raw), sha256=sha(raw))
        return raw

    def load(path):
        return json.loads(read(path))

    integrated = load(H / 'integration.json')
    assert integrated['integrated'] and not integrated['oldCameraOrRngFailuresClosed']
    core = load(H / 'core/observer-build.json')
    assert core['compiled'] and core['all141CoreObjectsRecompiled'] and len(core['objectBindings']) == 141
    assert sha(read(H / 'core/observer.wasm')) == core['wasmSha256'] == integrated['wasmSha256']
    for row in core['objectBindings']:
        assert sha(Path(row['path']).read_bytes()) == row['sha256']
    for name, digest in {**core['sourceHashes'], **core['headerHashes']}.items():
        assert sha((Path(core['sourceSnapshotRoot']) / name).read_bytes()) == digest
    for item in integrated['changedFiles']:
        assert sha(read(R / 'runtimes/th12' / item['path'])) == item['afterSha256']
    unit = load(H / 'component-verified.json')
    assert unit['verifiedControlledCameraPublicationComponent'] and unit['cases'] == 200
    assert unit['priorCopiedRightDifferences'] == 72 and unit['copiedScenes'] == 72 and unit['propagatedFailures'] == 72
    assert unit['nativeProofSha256'] == sha(read(H / 'native-component.json'))
    assert unit['toolSha256'] == sha(read(R / 'tools/th14-camera-publication-check-nov04.mjs'))
    component_build = load(H / 'core/component-build.json')
    assert unit['componentBuildSha256'] == sha((H / 'core/component-build.json').read_bytes())
    for name, key in [('component.wasm', 'candidateSha256'), ('prior-component.wasm', 'priorSha256')]:
        assert sha(read(H / 'core' / name)) == component_build[key]
    native = load(H / 'native-component.json')
    assert native['executedOriginalDrawBranchesAndWorkerCopy'] and native['controlledCases'] == 50
    assert native['publicationCases'] == 36 and not native['originalInstructionsModified']
    assert native['rendererFlushNotExecuted'] and native['syntheticCamerasAndCpuSchedule'] and not native['liveOriginalProcess']
    assert native['toolSha256'] == sha(read(R / 'tools/th14-camera-publication-native-nov04.py'))
    assert component_build['fixtureSha256'] == sha(read(R / 'runtimes/th12/th12_web/tests/cpp/th14-camera-publication-fixture-nov04.cpp'))
    regressions = load(OLD / 'regressions/end.json')
    assert regressions['finitePasses'] == 3 and regressions['callbacks'] == 199917
    verified_modes = []
    for row in regressions['results']:
        key = row['key']
        assert row['strictAndIndependentPassed']
        raw = load(H / 'revalidated-payloads' / key / 'raw-verified.json')
        for name in ('exceptions', 'timing', 'scene'):
            assert load(H / 'revalidated-payloads' / key / (name+'.json'))['passed']
        assert raw['verifiedFiniteEvidence'] and raw['callbacks'] == row['callbacks']
        assert raw['wasmSha256'] == core['wasmSha256'] and raw['verifierSha256'] == sha(read(R / 'tools/th14-verify-native-campaign.py'))
        for path, binding in raw['bindings'].items():
            actual = (R / path).read_bytes()
            assert len(actual) == binding['bytes'] and sha(actual) == binding['sha256'], path
        verified_modes.append(dict(key=key, callbacks=raw['callbacks'], vmRows=raw['vm303Rows'], combatCheckpoints=raw['combatCheckpoints']))
    syntax = load(OLD / 'syntax/report.json')
    assert syntax['passed'] and len(syntax['cases']) == 12
    for row in syntax['cases']:
        assert row['exitCode'] == 0
        before = OLD / 'source/th12_web/cpp/game' / row['source']
        after = H / 'source/th12_web/cpp/game' / row['source']
        assert sha(before.read_bytes()) == row['sourceSha256']
        assert before.read_bytes().replace(b'\r\n', b'\n') == after.read_bytes().replace(b'\r\n', b'\n')
    app_build = load(H / 'gles-build/build.json')
    app = load(H / 'gles-two-stage/report.json')
    reference = load(R / 'artifacts/th14/replay-cadence-reset-nov04/gles-two-stage/report.json')
    assert app_build['coreWasmSha256'] == core['wasmSha256']
    assert sha(read(H / 'gles-build/application.wasm')) == app['wasmSha256'] == app_build['wasmSha256']
    assert app['completed'] and not app['error'] and app['frames'] == app['applicationTicks'] == 2289
    assert app['actualProductionApplicationAndDevices'] and app['physicalAudioDevicesOpened'] == 0
    assert not app['appUiControlled'] and not app['browserRun'] and not app['browserAcceptance']
    assert app['glCalls']['SDL_GL_SwapWindow'] == app['frames']
    assert len(app['checks']) == 27 and all(row['passed'] for row in app['checks'])
    assert app['toolSha256'] == sha(read(R / 'tools/th14-native-application-process-host-oct27.py'))
    assert app_build['toolSha256'] == sha(read(R / 'tools/th14-build-native-application.py'))
    cadence = app['replayCadenceObservations']
    assert len(cadence) == 2289 and all(row['readOnly'] and row['words'][7] == 0 for row in cadence)
    active = [row for row in cadence if row['words'][3] and row['words'][4]]
    assert all(row['words'][0] == row['words'][1] for row in active)
    first = next(row for row in active if row['words'][2] == 2)
    assert first['hostFrame'] == 2217 and first['words'] == [8, 8, 2, 1, 1, 0, 1, 0]
    assert cadence[-1]['words'] == [89, 89, 2, 1, 1, 0, 1, 0]
    assert [(row['endFrame']-row['atFrame'], row['state'][1], row['state'][6]) for row in app['actions'][-6:]] == [(1449,2,0),(46,2,8),(10,2,88),(1,2,89),(1,2,89),(60,2,89)]
    assert (app['pcmFrames'], app['pcmSha256']) == (reference['pcmFrames'], reference['pcmSha256'])
    assert app['initialSave'] == app['finalSave'] == reference['initialSave']
    for relative, row in app_build['sourceBindings'].items():
        assert sha((R / relative).read_bytes()) == row['sha256']
    assert len(app['captures']) == 2
    for image, prior in zip(app['captures'], reference['captures']):
        assert image == prior
        raw = read(H / 'gles-two-stage' / image['file'])
        assert sha(raw) == image['sha256'] and raw == (R / 'artifacts/th14/replay-cadence-reset-nov04/gles-two-stage' / prior['file']).read_bytes()
    browser = load(H / 'browser-build/build.json')
    assert browser['compiled'] and browser['compiledUnits'] == browser['sourceUnits'] == 146
    assert not browser['browserAcceptance'] and not browser['browserRun']
    for name, digest in core['sourceHashes'].items():
        assert browser['sourceBindings'][name]['sha256'] == digest, name
    for item in integrated['changedFiles']:
        assert browser['sourceBindings'][item['path']]['sha256'] == item['afterSha256']
    assert sha(read(H / 'browser-build/th14-sdl.wasm')) == browser['wasmSha256']
    assert sha(read(H / 'browser-build/th14-sdl.mjs')) == browser['loaderSha256']
    for name, digest in integrated['protectedFiles'].items():
        assert sha(read(R / name)) == digest
    for name in ('th14-prepare-camera-publication-candidate-nov04.py', 'th14-build-camera-publication-candidate-nov04.py',
                 'th14-camera-publication-regressions-nov04.py', 'th14-integrate-camera-publication-nov04.py',
                 'th14-build-webgpu-reuse-worker-nov03.py'):
        read(R / 'tools' / name)
    result = dict(verifiedIntegratedCameraPublicationBoundary=True,
                  originalPublicationPcs=['0x40e365', '0x40e7f1'], originalWorkerCopy='0x40d435..0x40d447',
                  originalInstructionComponentCases=50, originalPublicationCases=36, controlledWasmCases=200,
                  priorCopiedRightDifferences=72, candidateCopiedRightDifferences=0, callbackFailureCases=72,
                  finiteRegressions=verified_modes, finiteCallbacks=199917, all141CoreObjectsRecompiled=True,
                  coreWasmSha256=core['wasmSha256'], otherTitleSyntaxCases=12,
                  applicationFrames=2289, applicationPresents=2289, applicationChecks=27,
                  applicationActiveCadenceSamples=len(active), applicationStage2FirstCounter=8, applicationPauseCounter=89,
                  twoCapturedFramesEqualFrozenReference=True, offlineMixedPcmFrames=app['pcmFrames'],
                  offlineMixedPcmHashEqualFrozenReference=True, physicalAudioDevicesOpened=0,
                  browserCompiledUnits=146, browserWasmSha256=browser['wasmSha256'], browserAcceptance=False,
                  nativeStateValuesProvidedToEngine=False, perRecordingClockChosen=False,
                  oldRecordingOrderRecovered=False, oldCameraOrRngFailuresClosed=False,
                  copyWordInterleavingsImplemented=False, ordinaryIndependentTimingAccepted=False,
                  completeGame=False, nativeEquivalent=False,
                  limitations=['The controlled instruction component uses synthetic cameras and skips the renderer flush implementation.',
                               'The new delivery point covers worker progress after a complete draw camera publication and before perspective; individual REP and perspective stores remain separately unproved.',
                               'Three retained finite records do not establish all modes, source replay EOF or the older failing recordings.',
                               'The offscreen Application uses declared platform inputs; its frozen image/PCM reference is not an original full-game recording.',
                               'Browser compilation does not accept browser gameplay, persistence, whole-game pixels/PCM or independent scheduling.'],
                  bindings=bindings, verifierSha256=sha(Path(__file__).read_bytes()))
    out = args.output.resolve()
    assert out.is_relative_to(R / 'docs/porting') or out.is_relative_to(H)
    data = (json.dumps(result, indent=2)+'\n').encode()
    if args.check:
        assert out.read_bytes() == data
    else:
        out.write_bytes(data)
    print(json.dumps({key: value for key, value in result.items() if key not in ('bindings', 'limitations', 'finiteRegressions')}))


if __name__ == '__main__':
    main()
