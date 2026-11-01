"""Verify a naturally terminated original run without claiming all input stages."""
from pathlib import Path
import argparse, hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/marisaa-beam-writer-context-nov02'
SHA = lambda b: hashlib.sha256(b).hexdigest()

def evidence(case):
    case = case.resolve(strict=True)
    assert case.is_relative_to(H)
    bindings = {}
    def bind(path):
        path = path.resolve(strict=True)
        assert path.is_relative_to(R)
        key = path.relative_to(R).as_posix()
        if key not in bindings:
            with path.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            bindings[key] = dict(bytes=path.stat().st_size, sha256=digest)
        return bindings[key]['sha256']
    def load(path):
        bind(path)
        return json.loads(path.read_bytes())
    plan = load(case / 'plan.json')
    end = load(case / 'process-end.json')
    queued = load(case / 'queue-end.json')
    native = load(case / 'native/report.json')
    verified = load(case / 'raw-verified.json')
    quiet = load(case / 'native-silence-verified.json')
    assert end['exitCode'] == 0 and end['guardStop'] is None
    assert queued['strictPassed'] and queued['modelExitCode'] == queued['independentVerifierExitCode'] == 0
    assert native['childExited'] and not native['error'] and native['observedForcedReplayEndMenu']
    assert verified['verifiedFiniteEvidence'] and verified['originalNaturalReplayEndObserved'] and not verified['diagnosticPrefixOnly']
    assert verified['selection'] == plan['selection']
    assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid'] == native['pid']
    assert native['executableSha256'] == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert bind(case / 'native/observer-source.py') == plan['sourceSha256'] == native['sourceSha256']
    for name, expected in verified['bindings'].items():
        assert bind(R / name) == expected['sha256'] and (R / name).stat().st_size == expected['bytes'], name
    B = H / 'spawn-candidate-v2/observer-build.json'
    core = load(B)
    assert bind(B) == plan['modelBuildSha256']
    assert core['wasmSha256'] == verified['wasmSha256'] == bind(B.parent / 'observer.wasm')
    assert len(core['objectBindings']) == 141
    for row in core['objectBindings']: assert bind(Path(row['path'])) == row['sha256']
    source = Path(core['sourceSnapshotRoot'])
    for name, digest in {**core['sourceHashes'], **core['headerHashes']}.items(): assert bind(source / name) == digest
    guard = load(R / 'docs/porting/th14-spawn-beam-stack-compile-guard-nov02.json')
    assert guard['th14ObjectByteIdentical'] and guard['th14GameplayCoreUnchanged']
    guarded_name = 'th12_web/cpp/game/EnemyAnimations.cpp'
    for name in core['candidateChangedFiles']:
        path = R / 'runtimes/th12' / name
        if name == guarded_name:
            assert bind(path) == guard['rootSourceSha256']
        else: assert bind(path) == bind(source / name)
    after = H / 'shared-compile-audit/after.o'
    assert bind(after) == guard['newObjectSha256'] == guard['originalObjectSha256']
    index = list(core['sourceHashes']).index(guarded_name)
    assert guard['originalObjectSha256'] == core['objectBindings'][index]['sha256']
    assert plan['sourceCore'] == 'ebba4fe46764cb486e730f74783b39041420955f'
    observed = verified['stagesObserved']
    assert observed == sorted(set(observed)) and observed[0] == 1
    headers = plan['originalStagesFromReplayHeaderOnly']
    assert headers == [1, 2, 3, 4, 5, 6]
    bind(Path(__file__))
    return dict(verifiedFiniteNaturalRun=True, sourceCore=plan['sourceCore'], wasmSha256=core['wasmSha256'],
                sourceGuardHasByteIdenticalTh14Object=True, selection=verified['selection'],
                callbacks=native['callbacks'], stagesFromInputHeaders=headers, stagesActuallyObserved=observed,
                allTargetStageEntriesActuallyObserved=observed == headers,
                vm303Rows=verified['vm303Rows'], combatCheckpoints=verified['combatCheckpoints'],
                strictAndIndependentPassed=True, actualOriginalMasterLevelsZero=True,
                completeRecordedInputConsumptionNotProven=True, originalMenuEntryWasWarmCaseInitialization=True,
                otherHistoricalRngAndCameraFailuresNotClosed=True, wholeModeEquivalent=False,
                ordinaryOriginalGuiAccepted=False, independentSchedulingAccepted=False,
                originalWholePixelsOrPcmAccepted=False, browserAcceptance=False,
                completeGame=False, nativeEquivalent=False, bindings=bindings)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = evidence(args.case)
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') or output.is_relative_to(R / 'docs/porting')
    if args.check: assert json.loads(output.read_bytes()) == report
    else:
        assert not output.exists()
        output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'bindings'}))
