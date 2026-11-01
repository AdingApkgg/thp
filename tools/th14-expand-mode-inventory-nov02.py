"""Extend only Marisa B Normal from the frozen published mode inventory."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, subprocess

R = Path(__file__).resolve().parents[1]
BASE = '91a797541a5491d326a8c6e5d593e0890313879e'
NAME = 'docs/porting/th14-mode-acceptance-inventory-oct25.json'
BASE_SHA = '381c6179fc712352996e21d32d027231f20604a6084e485b377f42c4ee865046'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def expected():
    original = subprocess.check_output(['git', '-C', str(R / 'tools/tmp/github-source-release'), 'show', BASE + ':' + NAME])
    assert SHA(original) == BASE_SHA
    baseline = json.loads(original)
    assert baseline['pairsWithNaturalNativeRun'] == 30 and baseline['pairsWithAllStageEntriesObserved'] == 25
    tool = R / 'tools/th14-expanded-six-stage-evidence-nov02.py'
    spec = importlib.util.spec_from_file_location('six_stage_expansion', tool)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = R / 'artifacts/th14/six-stage-inputs-nov02/marisab-normal-kg'
    proved = module.evidence(case)
    published_proof_path = R / 'docs/porting/th14-marisab-normal-six-stage-nov02.json'
    assert proved == json.loads(published_proof_path.read_bytes())
    assert proved['verifiedExpandedFiniteSixStageReplay'] and proved['stagesObserved'] == [1, 2, 3, 4, 5, 6]
    result = copy.deepcopy(baseline)
    row = next(row for row in result['cases'] if row['key'] == 'marisab-normal')
    assert (row['character'], row['subtype'], row['difficulty']) == (1, 1, 1)
    assert not row['allStageEntriesObserved']
    assert all(run['stagesObserved'] == [1, 2] for run in row['retainedNaturalRuns'])
    relative = lambda path: path.relative_to(R).as_posix()
    digest = lambda path: SHA(path.read_bytes())
    native, model = case / 'native', case / 'model'
    comparison = dict(path=relative(model / 'report.json'), reportSha256=digest(model / 'report.json'),
                      callbacks=proved['callbacks'], wasmSha256=proved['wasmSha256'],
                      additionalObservedGateResults=dict(camera=True, hud=True, animation=True, combat=True),
                      reportedAdditionalGateFailures=[], independentRawProofPath=relative(case / 'raw-verified.json'),
                      independentRawProofSha256=digest(case / 'raw-verified.json'),
                      scope='Actual complete finite natural replay; all retained selected32/camera25/HUD2/VM303/combat and initial publications independently exact. Warm entry and observed platform timing only; no whole-mode, ordinary-GUI, pixel, PCM or independent-scheduling acceptance.')
    new_run = dict(path=relative(native), reportSha256=digest(native / 'report.json'),
                   initialSnapshotSha256=digest(native / 'untouched-first-player.json'),
                   selectedSha256=digest(native / 'selected-state.u32'), callbacks=proved['callbacks'],
                   stagesObserved=[1, 2, 3, 4, 5, 6], naturalReplayEndObserved=True,
                   clearCompletionNotAsserted=True, intactOriginalReplayDeclared=True,
                   instructionBytesPatched=0, rngOrCounterWrites=0, replaySha256=proved['replaySha256'],
                   selected32ComparisonReports=[comparison], preferredComparisonPath=comparison['path'],
                   partialSelected32ComparisonReports=[], actualNativeMusicAndEffectsMasterLevelsZero=True,
                   sourceCoreCommit=BASE, publicEvidence='docs/porting/th14-marisab-normal-six-stage-nov02.json')
    row['retainedNaturalRuns'].insert(0, new_run)
    row['allStageEntriesObserved'] = True
    assert not row['wholeModeEquivalent']
    result.update(schema='th14/mode-acceptance-inventory/4', date='2026-11-02',
                  pairsWithAllStageEntriesObserved=26, toolSha256=SHA(Path(__file__).read_bytes()))
    assert sum(row['allStageEntriesObserved'] for row in result['cases']) == 26
    assert len(result['cases']) == result['modePairs'] == result['pairsWithNaturalNativeRun'] == 30
    assert [row for row in result['cases'] if row['key'] != 'marisab-normal'] == [row for row in baseline['cases'] if row['key'] != 'marisab-normal']
    for path in [native / 'report.json', native / 'untouched-first-player.json', model / 'report.json',
                 model / 'camera-report.json', model / 'hud-report.json', model / 'live-report.json',
                 model / 'combat-snapshots.json', case / 'raw-verified.json', published_proof_path]:
        result['reportBindings'][relative(path)] = digest(path)
    result['additionalExtensions'] = [dict(baseSourceCommit=BASE, baseInventorySha256=BASE_SHA,
        baseInventoryToolSha256=baseline['toolSha256'], updatedModeOnly='marisab-normal',
        otherTwentyNineModesFrozenUnchanged=True, oldObservedStages=[1, 2], newObservedStages=[1, 2, 3, 4, 5, 6],
        fullCapturedRunCompared=True, allRetainedFieldsIndependentlyExact=True,
        sourceCoreCommit=BASE, publicEvidenceSha256=digest(published_proof_path),
        wholeModeEquivalent=False, completeGame=False)]
    assert not result['completeGame'] and not result['nativeEquivalent']
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = expected()
    output = R / NAME
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(dict(verifiedSingleModeInventoryExtension=True, pairsWithNaturalNativeRun=30,
                          pairsWithAllStageEntriesObserved=26, otherTwentyNineModesFrozenUnchanged=True,
                          wholeModeEquivalent=False, completeGame=False)))
