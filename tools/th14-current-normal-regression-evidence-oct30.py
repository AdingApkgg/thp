"""Recheck the retained full ReimuB Normal regression against published3af.

No game is launched. The independent verifier recomputes the recorded fields;
source and object hashes bind that result to the current production core.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '3af854d7e4251890cb743157b00c862392e6d816'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def review():
    home = ROOT/'artifacts/th14/reimub-normal-current-oct30'
    bindings = {}

    def read(path):
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw

    def load(path):
        return json.loads(read(path))

    plan = load(home/'plan.json')
    proof = load(home/'verified.json')
    build_path = ROOT/plan['build']
    build = load(build_path)
    assert plan['sourcePublished'] == COMMIT
    assert plan['callbacks'] == proof['callbacks'] == proof['originalCapturedCallbacks'] == 122537
    assert proof['selection'] == plan['selection'] == [0, 1, 1, 1]
    assert proof['stagesObserved'] == [1, 2, 3, 4, 5, 6]
    assert proof['originalNaturalReplayEndObserved'] and not proof['diagnosticPrefixOnly']
    assert proof['hostNormalBoundaryMode'] == 'none'
    assert not proof['ordinaryIndependentThreadTimingAcceptance']
    assert proof['verifiedFiniteEvidence'] and not proof['completeGame'] and not proof['nativeEquivalent']
    assert all(proof[key] for key in ['allSelected32Equal', 'allCamera25Equal', 'allHud2Equal',
                                      'allVm303AndRegistryOrderEqual', 'allCapturedCombatWordsEqual'])
    assert (proof['vm303Rows'], proof['combatCheckpoints'], proof['nonemptyCombatCheckpoints'],
            proof['orderedPublications']) == (2586, 1294, 157, 3274)
    assert proof['verifierSha256'] == SHA(read(ROOT/'tools/th14-verify-native-campaign.py'))
    assert proof['comparisonToolSha256'] == SHA(read(ROOT/'tools/th14-compare-native-campaign.mjs'))
    assert proof['wasmSha256'] == build['wasmSha256'] == SHA(read(build_path.parent/'observer.wasm'))
    assert len(build['sourceHashes']) == len(build['objectBindings']) == 141
    assert build['unrelatedRootResourceCryptExcluded'] and not build['nativeRngCounterInputOrPointerValuesProvided']
    archive = subprocess.check_output(['git', '-C', str(ROOT/'tools/tmp/github-source-release'),
                                     'archive', '--format=tar', COMMIT, 'runtimes/th12/th12_web/cpp/game'])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        for key, digest in build['sourceHashes'].items():
            assert SHA(tree.extractfile('runtimes/th12/'+key).read()) == digest, key
    for row in build['objectBindings']:
        assert SHA(read(Path(row['path']))) == row['sha256']
    # Recompute from original/portable observations, rather than trust the saved booleans.
    with tempfile.TemporaryDirectory(prefix='proof-recheck-', dir=home) as temporary:
        output = Path(temporary)/'recomputed.json'
        subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/'tools/th14-verify-native-campaign.py'),
                        '--native', str(ROOT/plan['native']), '--model', str(ROOT/plan['output']),
                        '--build', str(build_path), '--output', str(output)], check=True,
                       stdout=subprocess.DEVNULL)
        assert json.loads(output.read_bytes()) == proof
    return dict(verifiedCurrentFullNormalRegression=True, sourceCommit=COMMIT,
                replaySha256=proof['sourceReplaySha256'], callbacks=122537,
                selection=[0, 1, 1, 1], stagesObserved=[1, 2, 3, 4, 5, 6],
                selectedStateWords=32, cameraWords=25, hudWords=2,
                allDeclaredStateAndSampledFieldsEqual=True, vmRows=2586, selectedWordsPerVm=303,
                combatCheckpoints=1294, nonemptyCombatCheckpoints=157,
                initialOrderedPublications=3274, publicationWindowCallbacks=1000,
                productionCoreSourceUnits=141, observerWasmSha256=proof['wasmSha256'],
                savedFullProofSha256=SHA(read(home/'verified.json')),
                independentRecomputationEqual=True, noEmulationRerun=True,
                originalWarmAttractClearCase=True, ordinaryOriginalMenuAccepted=False,
                ordinaryIndependentThreadTimingAccepted=False, originalWholePixelsOrPcmCompared=False,
                browserAcceptance=False, wholeModeEquivalenceAccepted=False,
                completeGame=False, nativeEquivalent=False,
                verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings,
                scope=proof['limitations'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT/'docs/porting') or output.is_relative_to(ROOT/'artifacts/th14')
    result = review()
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ['bindings', 'scope']}))


if __name__ == '__main__':
    main()
