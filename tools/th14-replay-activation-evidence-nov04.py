"""Recheck actual original-component, Wasm and Application replay cadence evidence."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT/'artifacts/th14/replay-cadence-reset-nov04'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
load = lambda path: json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    bound = {}
    def bind(path):
        path = path.resolve()
        assert path.is_relative_to(ROOT)
        raw = path.read_bytes()
        bound[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw
    unit = load(HOME/'verified.json')
    original = load(HOME/'native.json')
    assert unit['passed'] and original['passed']
    assert unit['gateCases'] == len(original['cases']) == 4416
    assert unit['dispatcherCases'] == len(original['dispatch']) == 9
    assert unit['counterAssertions'] == 25
    assert unit['priorAlwaysSingleUpdateGateMismatches'] > 0
    assert unit['nativeProofSha256'] == SHA(bind(HOME/'native.json'))
    assert unit['wasmSha256'] == SHA(bind(HOME/'cadence.wasm'))
    assert original['playbackInitialCallbackFrame'] == 0
    for relative, digest in unit['sourceHashes'].items():
        assert SHA(bind(ROOT/'runtimes/th12/th12_web'/relative)) == digest
    for tool, key in [('th14-replay-activation-check-nov04.mjs','toolSha256'),
                      ('th14-replay-activation-native-nov04.py','nativeToolSha256')]:
        assert SHA(bind(ROOT/'tools'/tool)) == unit[key]
    bind(HOME/'verified.json')

    build_path = HOME/'core/observer-build.json'
    build = load(build_path)
    assert build['all141CoreObjectsRecompiled'] and len(build['objectBindings']) == 141
    assert SHA(bind(HOME/'core/observer.wasm')) == build['wasmSha256']
    for obj in build['objectBindings']:
        assert SHA(Path(obj['path']).read_bytes()) == obj['sha256']
    for relative, digest in {**build['sourceHashes'], **build['headerHashes']}.items():
        assert SHA((Path(build['sourceSnapshotRoot'])/relative).read_bytes()) == digest
        if relative != 'th12_web/cpp/game/ResourceCrypt.cpp':
            assert SHA((ROOT/'runtimes/th12'/relative).read_bytes()) == digest
    bind(build_path)

    regressions = []
    for index, expected_callbacks in [(1,122537), (2,38403)]:
        end_path = HOME/f'regressions/case-{index}/end.json'
        end = load(end_path)
        assert end['casesCompleted'] == 1
        result = end['results'][0]
        assert result['strictPassed'] and result['independentVerifierExitCode'] == 0
        assert result['callbacks'] == expected_callbacks and not result['guardStop']
        case = ROOT/result['caseDirectory']
        for name in ['exceptions.json','timing.json','scene.json']:
            assert load(case/name)['passed']
            bind(case/name)
        raw = load(case/'raw-verified.json')
        assert raw['verifiedFiniteEvidence'] and raw['callbacks'] == expected_callbacks
        assert raw['wasmSha256'] == build['wasmSha256']
        assert raw['allSelected32Equal'] and raw['allCamera25Equal'] and raw['allHud2Equal']
        assert raw['allVm303AndRegistryOrderEqual'] and raw['allCapturedCombatWordsEqual']
        regressions.append(dict(key=result['key'],callbacks=expected_callbacks,
            vmRows=raw['vm303Rows'],combatCheckpoints=raw['combatCheckpoints']))
        bind(case/'raw-verified.json')
        bind(end_path)

    assert unit['nativeStageActivationCases']==len(original['activation'])==56
    assert unit['wasmStageActivationCases']==42 and unit['activationFpsCases']==len(original['activationFps'])==1020
    assert unit['priorActivationCounterMismatches']==35 and unit['priorActivationFpsMismatches']==0 and unit['priorCallbackMismatches']==986
    assert unit['arbitraryPhaseFpsDefectClaimRetracted'] and unit['existingStageLocalFpsIndexValidatedAfterActivation']
    assert unit['priorControlWasmSha256']==SHA(bind(HOME/'prior-no-reset.wasm'))
    assert all(x['afterCallbackFrame']==0 and x['afterStageFrame']==0 and x['pointersReset']for x in original['activation'])
    app_build = load(HOME/'gles-build/build.json')
    app = load(HOME/'gles-two-stage/report.json')
    assert app_build['coreWasmSha256'] == build['wasmSha256']
    assert SHA(bind(HOME/'gles-build/application.wasm')) == app['wasmSha256'] == app_build['wasmSha256']
    assert app['completed'] and not app['error'] and app['frames'] == 2289
    assert app['toolSha256']==SHA(bind(ROOT/'tools/th14-native-application-process-host-oct27.py'))
    assert app_build['toolSha256']==SHA(bind(ROOT/'tools/th14-build-native-application.py'))
    assert app['actualProductionApplicationAndDevices'] and app['physicalAudioDevicesOpened'] == 0
    assert app['glCalls']['SDL_GL_SwapWindow'] == app['frames']
    assert len(app['checks'])==27 and all(row['passed'] for row in app['checks'])
    rows=app['replayCadenceObservations'];assert len(rows)==app['frames']
    assert all(row['readOnly']and row['words'][7]==0 for row in rows)
    active=[row for row in rows if row['words'][3]and row['words'][4]]
    assert all(row['words'][0]==row['words'][1]for row in active)
    first=next(row for row in active if row['words'][2]==2)
    assert first['hostFrame']==2217 and first['words']==[8,8,2,1,1,0,1,0]
    assert rows[-1]['words']==[89,89,2,1,1,0,1,0]
    assert [(x['endFrame']-x['atFrame'],x['state'][1],x['state'][6])for x in app['actions'][-6:]]==[(1449,2,0),(46,2,8),(10,2,88),(1,2,89),(1,2,89),(60,2,89)]
    for relative, row in app_build['sourceBindings'].items():
        assert SHA((ROOT/relative).read_bytes()) == row['sha256']
    for image in app['captures']:
        assert SHA(bind(HOME/'gles-two-stage'/image['file'])) == image['sha256']
    for path in ['gles-build/build.json','gles-two-stage/report.json',
                 'application-two-stage-scenario.json','application-argv.json']:
        bind(HOME/path)

    browser = load(HOME/'browser-build/build.json')
    assert browser['compiled'] and browser['compiledUnits'] == browser['sourceUnits'] == 146
    for relative in ['th12_web/cpp/game/Replay.hpp','th12_web/cpp/game/Replay.cpp',
                     'th12_web/cpp/game/ReplayCadenceTh14.hpp','th12_web/cpp/sdl/Application.cpp']:
        assert browser['sourceBindings'][relative]['sha256'] == SHA(bind(ROOT/'runtimes/th12'/relative))
    assert browser['wasmSha256'] == SHA(bind(HOME/'browser-build/th14-sdl.wasm'))
    assert browser['loaderSha256'] == SHA(bind(HOME/'browser-build/th14-sdl.mjs'))
    bind(HOME/'browser-build/build.json')
    for path, digest in [
        ('runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp','a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'),
        ('artifacts/th14/vm-return-worker-oct29/work-state.json','2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c')]:
        assert SHA((ROOT/path).read_bytes()) == digest

    report = dict(verifiedFiniteReplayActivationReset=True,completeGame=False,nativeEquivalent=False,
        nativeExecutableSha256=original['nativeExecutableSha256'],nativeGateCases=4416,
        nativeDispatcherCases=9,wasmCounterAssertions=25,nativeStageActivationCases=56,
        wasmStageActivationCases=42,activationFpsCases=1020,
        priorActivationCounterMismatches=35,priorActivationFpsMismatches=0,priorCallbackMismatches=986,
        previousCrossStageCounterClaimRetracted=True,arbitraryPhaseFpsDefectClaimRetracted=True,
        isolatedFpsCursorCandidateRejectedBeforeProduction=True,
        coreObjectsRecompiled=141,coreWasmSha256=build['wasmSha256'],regressions=regressions,
        applicationFrames=2289,applicationPresents=2289,applicationChecks=27,
        firstStage2ActiveHostFrame=2217,firstStage2ActiveCallbackFrame=8,finalPausedCallbackFrame=89,
        applicationPausedHostFrames=60,activeCadenceSamples=len(active),allActiveCountersEqualStageCursor=True,
        physicalAudioDevicesOpened=0,browserUnitsCompiled=146,
        browserWasmSha256=browser['wasmSha256'],browserLoaderSha256=browser['loaderSha256'],
        browserAcceptance=False,ordinaryOriginalGuiFastPlaybackAccepted=False,
        fullOriginalFastPlaybackComparisonAccepted=False,
        limitations=['Original activation executes with controlled input reset, position restore and motion refresh services.',
            'Actual Application uses declared EGL/WASI platform clocks and normalized input; it is not original GUI or browser acceptance.',
            'Full original fast-playback rendering, audio, callback enable/disable lifetimes and transitions still need direct comparison.',
            'The two replay regression recordings do not close other modes or retained RNG/camera timing failures.'],
        bindings=bound,verifierSha256=SHA(Path(__file__).read_bytes()))
    target = ROOT/'docs/porting/th14-replay-activation-reset-nov04.json'
    data = (json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    if args.check:
        assert target.read_bytes() == data
    else:
        target.write_bytes(data)
    print(json.dumps(dict(verifiedFiniteReplayActivationReset=True,nativeGateCases=4416,
        applicationFrames=2289,regressionCallbacks=160940,browserUnits=146)))


if __name__ == '__main__':
    main()
