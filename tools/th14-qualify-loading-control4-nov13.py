"""Audit the flags4 lifetime diagnosis and current actual-slot comparison."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / 'artifacts/th14/loading-control4-nov13'
bindings = {}


def raw(path):
    p = ROOT / path
    b = p.read_bytes()
    bindings[p.relative_to(ROOT).as_posix()] = dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    return b


def load(path):
    return json.loads(raw(path))


def local(path):
    return HOME.relative_to(ROOT) / path


def main():
    initial = load(local('cpp/result.json'))
    assert not initial['passed']
    assert [(r['name'], r['mismatchedFrames'], r['mismatchedWords']) for r in initial['cases'] if r['mismatchedFrames']] == [
        ('flags4-clear-and-finish', 90, 441)]
    rates = load(local('rate-run-v2/rate-bindings.json'))
    read_only = load(local('rate-diagnostic-v2/build.json'))
    assert read_only['readOnlyRatePointerObservation'] and not read_only['dereferenceObservedPointers']
    stale = []
    for row in rates:
        for at in range(0, len(row['words']), row['stride']):
            handle, script, owner, timer, alpha, duration, current, fractional = row['words'][at:at + 8]
            if script == 14 and alpha != owner:
                assert timer == owner and alpha != 0 and duration == 8
                stale.append(dict(case=row['name'], frame=row['frame'], handle=handle,
                                  managerRate=owner, scriptTimerRate=timer, alphaTimerRate=alpha))
    assert len(stale) == 7
    live = load(local('live-preparer-run/result.json'))
    assert not live['passed'] and all(r['mismatchedFrames'] == 0 for r in live['cases'][:5])
    assert (live['cases'][5]['mismatchedFrames'], live['cases'][5]['mismatchedWords']) == (75, 302)
    outcomes = {}
    for folder, frames, words in [('scoped-owner-run', 966, 2072862), ('legacy-control-run', 1127, 855162)]:
        report = load(local(folder + '/result.json'))
        assert report['passed'] and report['totalFrames'] == frames and report['totalWords'] == words
        assert report['normalAccessControl'] and report['wordsPerVm'] == 303
        assert report['graphicsOrAudioDevicesOpened'] == 0
        assert not report['physicalSchedulingAccepted'] and not report['completeGame']
        assert all(c['mismatchedFrames'] == c['mismatchedWords'] == 0 for c in report['cases'])
        outcomes[folder] = dict(cases=len(report['cases']), frames=frames, words=words)
    negative = load(local('legacy-negative-run/result.json'))
    assert not negative['passed'] and negative['negativeControl'] == 'ignore-control'
    failures = [dict(case=c['name'], frames=c['mismatchedFrames'], words=c['mismatchedWords'])
                for c in negative['cases'] if c['mismatchedFrames']]
    assert len(failures) == 3 and sum(c['words'] for c in failures) == 28410
    provider = load(local('provider/build.json'))
    assert provider['normalEngineAccessControl'] and len(provider['currentProviders']) == 141
    for p, digest in provider['sourceBindings'].items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest, p
    for row in provider['currentProviders']:
        assert hashlib.sha256((ROOT / row['object']).read_bytes()).hexdigest() == row['objectSha256']
    for folder in ['rate-diagnostic-v2', 'live-preparer', 'scoped-owner']:
        b = load(local(folder + '/build.json'))
        assert hashlib.sha256(raw(local(folder + '/probe.wasm'))).hexdigest() == b['wasmSha256']
        for p, digest in b['observerBindings'].items():
            assert hashlib.sha256(raw(p)).hexdigest() == digest, p
    native = load(local('native/native.json'))
    assert hashlib.sha256(raw(local('native/snapshots.u32'))).hexdigest() == native['snapshotsSha256']
    actual_rates = sorted(set(c['rate'] for c in native['cases']))
    assert actual_rates == [0.5, 1.0]
    prep = load(local('actual-slot-preparation/cpp-qualified.json'))
    assert prep['passed'] and not prep['differences'] and prep['normalAccessControl']
    assert prep['routes'] == 42 and prep['resources'] == 7 and prep['scripts'] == 1452
    assert prep['expandedTemplateWords'] == 439956 and prep['templateWords'] == 74220
    assert prep['descriptorWords'] == 59058 and prep['scriptBytes'] == 313680
    np = ROOT / 'artifacts/th14/actual-slot-anm-preparation-v4-expanded-nov10/native.json'
    assert hashlib.sha256(raw(np)).hexdigest() == prep['nativeProofSha256']
    pb = load(local('actual-slot-preparation/build.json'))
    assert hashlib.sha256(raw(local('actual-slot-preparation/loader.wasm'))).hexdigest() == pb['wasmSha256'] == prep['wasmSha256']
    assert pb['normalAccessControl'] and pb['gameObjectsReused'] == 141 and pb['engineUnitsChanged'] == 0
    for path in ['runtimes/th12/th12_web/cpp/game/GameSession.cpp',
                 'runtimes/th12/th12_web/cpp/game/GameSessionResources.cpp',
                 'runtimes/th12/th12_web/cpp/game/GameSession.hpp',
                 'runtimes/th12/th12_web/cpp/sdl/Application.cpp']:
        raw(path)
    protected = 'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp'
    assert hashlib.sha256(raw(protected)).hexdigest() == 'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
    raw(Path(__file__))
    result = dict(schema='thp/th14-loading-control4/1', terminal=True,
                  gameSourceCommit='84b8741af5b7ca617cc4046fe697d3cbfebbf4ad',
                  gameCodeChanged=False, fixtureOwnerLifetimeCorrected=True,
                  invalidOwnerLifetimeFailureRetained=dict(frames=90, words=441),
                  staleRatePointerObservations=stale,
                  liveTwoManagerRateDifferenceRetained=dict(frames=75, words=302),
                  productionCrossManagerTemplateReuseNotObserved=True,
                  templatePreparationRate=1, scopedTemplateDestroyedBeforeManager=True,
                  flags4ActualCaseRates=actual_rates,
                  inheritedNativeRateValuesAreNotActualCaseCoverage=True,
                  loadingCases=outcomes, negativeControlFailures=failures,
                  actualSlotPreparation=dict(resources=7, rates=6, routes=42, templates=1452,
                                             expandedTemplateWords=439956, templateAndRngWords=74220,
                                             descriptorWords=59058, scriptBytes=313680, differences=0),
                  normalGameObjectsVerifiedReused=141, graphicsOrAudioDevicesOpened=0,
                  newFullReplayRuns=0, loading24CallDifferenceClosed=False,
                  physicalSchedulingAccepted=False, browserUiAccepted=False,
                  completeGame=False, bindings=bindings)
    out = HOME / 'qualified.json'
    assert not out.exists()
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['bindings', 'staleRatePointerObservations']}))


if __name__ == '__main__':
    main()
