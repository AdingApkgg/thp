"""Bind a new intact six-stage input to actual terminal capture and raw verification."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys

R = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
ALLOWED = {'marisab-normal-kg': [1, 1, 1, 1], 'marisaa-normal-kg': [1, 0, 1, 1],
           'marisaa-hard-kg': [1, 0, 2, 1], 'marisab-lunatic-myon': [1, 1, 3, 1],
           'marisaa-easy-kg': [1, 0, 0, 1]}


def evidence(case):
    case = case.resolve(strict=True)
    assert case.is_relative_to(R / 'artifacts/th14/six-stage-inputs-nov02') and case.name in ALLOWED
    bindings = {}

    def raw(path):
        path = path.resolve(strict=True)
        assert path.is_relative_to(R)
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    # Terminal receipts are prerequisites. Neither a live prefix nor merely
    # finding six headers in an input can satisfy this proof.
    queued, terminal = load(case / 'queue-end.json'), load(case / 'process-end.json')
    assert queued['strictPassed'] and queued['modelExitCode'] == queued['independentVerifierExitCode'] == 0
    assert terminal['exitCode'] == 0 and terminal['guardStop'] is None
    N, M = case / 'native', case / 'model'
    native, compared, plan = load(N / 'report.json'), load(M / 'report.json'), load(case / 'plan.json')
    assert native['childExited'] and not native['error'] and native['observedForcedReplayEndMenu']
    assert not compared['diagnosticPrefixOnly'] and compared['callbacks'] == native['callbacks']
    assert compared['selection'] == plan['selection'] == ALLOWED[case.name]
    assert native['executableSha256'] == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert native['sourceSha256'] == plan['sourceSha256'] == SHA(raw(R / 'tools/th14-native-campaign-observer-oct25.py'))
    assert native['sourceSha256'] == 'ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
    assert native['instructionBytesPatched'] == native['rngOrCounterWrites'] == 0 and not native['inputInjected']
    assert native['gameStateWordWrites'] == 1 and native['caseInitialization']['attractBitClearOnly']
    assert compared['noNativePublicationValuesProvidedToEngine'] and compared['noPerFrameStateOverrides']
    assert compared['hostNormalBoundaryMode'] == 'none'
    assert compared['normalBoundaryObservation'] is compared['normalVmBoundaryObservation'] is None
    build_path = R / 'artifacts/th14/option-recall-once-nov02/candidate/observer-build.json'
    build = load(build_path)
    assert SHA(raw(build_path)) == plan['modelBuildSha256']
    assert compared['wasmSha256'] == build['wasmSha256'] == SHA(raw(build_path.parent / 'observer.wasm'))
    assert build['wasmSha256'] == 'f3af4e5e1aaea287869f2b67a23f9f3e27137274883b2a32506523f40d9be43d'
    snapshot = Path(build['sourceSnapshotRoot'])
    for inventory in ['sourceHashes', 'headerHashes']:
        for name, digest in build[inventory].items():
            assert SHA(raw(snapshot / name)) == digest
    compiler = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert SHA(raw(compiler)) == build['compilerSha256']
    assets = R / native['observerOptions']['assets']
    asset = load(assets / 'manifest.json')
    assert SHA(raw(assets / 'manifest.json')) == plan['assetManifestSha256']
    assert asset['passed'] and asset['changedEntries'] == ['demo0.rpy'] and asset['unchangedEntries'] == 226
    replay = Path(asset['replayPath'])
    metadata_path = replay.with_name(replay.stem + '-source.json')
    metadata = load(metadata_path)
    assert metadata['actualNativeCodecVerified'] and metadata['expectedSelection'] == ALLOWED[case.name][:3]
    assert [entry['stage'] for entry in metadata['stages']] == [1, 2, 3, 4, 5, 6]
    assert metadata['sha256'] == asset['replaySha256'] == native['sourceFullReplaySha256'] == SHA(raw(replay))
    assert SHA(raw(metadata_path)) == plan['metadataSha256'] and metadata['sha256'] == plan['replaySha256']
    assert SHA(raw(case.parent / 'source-page.html')) == metadata['sourcePageSha256']
    decoder = case.parent / ('decode-native.py' if replay.stem in ['th14_ud0812', 'th14_ud07e5'] else 'decode-additional-native.py')
    codec_path = case.parent / ('codec-verified.json' if replay.stem in ['th14_ud0812', 'th14_ud07e5'] else 'additional-codec-verified.json')
    codec = load(codec_path)
    assert codec['passed'] and codec['toolSha256'] == SHA(raw(decoder)) == metadata['nativeCodecObserverSha256']
    assert next(row for row in codec['rows'] if row['sha256'] == metadata['sha256']) == metadata
    quiet = load(case / 'native-silence-verified.json')
    assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid'] == native['pid']
    assert quiet['nativeExecutableSha256'] == native['executableSha256']
    assert quiet['toolSha256'] == SHA(raw(R / 'tools/th14-native-silent-levels-nov02.py'))
    assert not quiet['gameOrConfigOrAudioValuesWritten'] and not quiet['threadsSuspended']
    assert all((row['musicConfig'], row['effectsConfig'], row['musicMaster'], row['effectsMaster']) == (0, 0, 0, 0) for row in quiet['samples'])
    # Re-run the independent decoder, not just its report's green flag. This
    # checks every retained selected state, camera/HUD word, 303-word VM row,
    # raw combat schema and initial publication in the declared full campaign.
    verifier = R / 'tools/th14-verify-native-campaign.py'
    raw(verifier)
    fresh_path = case / 'publication-raw-recomputed.json'
    with (case / 'publication-raw-recomputed.log').open('wb') as log:
        checked = subprocess.run([sys.executable, '-X', 'utf8', str(verifier), '--native', str(N),
            '--model', str(M), '--build', str(build_path), '--output', str(fresh_path)],
            cwd=R, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    assert checked.returncode == 0, 'Independent terminal evidence recheck failed'
    verified = load(fresh_path)
    assert verified == load(case / 'raw-verified.json')
    assert verified['verifiedFiniteEvidence'] and verified['originalNaturalReplayEndObserved']
    assert verified['stagesObserved'] == [1, 2, 3, 4, 5, 6] and not verified['diagnosticPrefixOnly']
    assert verified['selection'] == ALLOWED[case.name] and verified['wasmSha256'] == build['wasmSha256']
    for name, binding in verified['bindings'].items():
        assert SHA(raw(R / name)) == binding['sha256']
    return dict(verifiedExpandedFiniteSixStageReplay=True, case=case.name, selection=ALLOWED[case.name],
                sourceCoreCommit='91a797541a5491d326a8c6e5d593e0890313879e', wasmSha256=build['wasmSha256'],
                sourcePage=metadata['sourcePage'], sourceReplay=metadata['download'], replaySha256=metadata['sha256'],
                callbacks=native['callbacks'], originalNaturalReplayEndObserved=True, stagesObserved=[1, 2, 3, 4, 5, 6],
                allRetainedSelected32Camera25Hud2Vm303CombatAndInitialPublicationsIndependentlyExact=True,
                vmRows=verified['vm303Rows'], combatCheckpoints=verified['combatCheckpoints'],
                independentlyRecomputedAtPublication=True, actualOriginalMusicAndEffectsMastersZero=True,
                nativeInputAttractBitClearOnly=True, noRngCounterHealthInputOrInstructionWrites=True,
                noAdditionalModelVmClockHooks=True, originalWarmReplayScopeOnly=True,
                ordinaryOriginalGuiAccepted=False, independentSchedulingAccepted=False,
                originalWholePixelsOrPcmAccepted=False, browserAcceptance=False,
                wholeModeEquivalentAccepted=False, completeGame=False, nativeEquivalent=False,
                bindings=bindings, verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') or output.is_relative_to(R / 'docs/porting')
    result = evidence(args.case)
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: value for key, value in result.items() if key != 'bindings'}))
