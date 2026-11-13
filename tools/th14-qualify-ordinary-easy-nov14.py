"""Combine five Easy clear/save cases with two retained early-end comparisons."""
from pathlib import Path
import hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-difficulties-nov14'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows = load(H / 'score-qualified/scores.json')
assert {r['selection'] for r in rows} == {0, 1, 3, 4, 5}
evidence = {}
for row in rows:
    codec_path = H / 'score-qualified' / (row['key'] + '-native-codec.json')
    codec = load(codec_path)
    assert codec['passed'] and codec['originalInstructionBytesPatched'] == 0
    assert codec['encodedSha256'] == row['encodedSha256']
    assert codec['decodedSha256'] == row['decodedSha256']
    row['nativeCodecVerified'] = True
    for p in [codec_path, R / row['writer'] / 'report.json', R / row['freshReader'] / 'report.json',
              R / row['writer'] / 'observations-summary.json']:
        evidence[p.relative_to(R).as_posix()] = sha(p)
early = load(H / 'toho-terminal-audit.json')
assert early['passed'] and early['monsterTerminal']['terminalGameplayWordsDifferent'] == 0
eligibility = load(H / 'easy-eligibility-audit.json')
assert eligibility['passed'] and eligibility['easyNoContinueClearUnlocksSelectedExtra']
for p in [H / 'toho-terminal-audit.json', H / 'easy-eligibility-audit.json']:
    evidence[p.relative_to(R).as_posix()] = sha(p)
result = dict(acceptanceStandard='observable-behavior-alignment', ordinaryEasyClears=5,
              freshApplicationReads=5, sixLoadoutEasyClearsAccepted=False,
              clearCallbacks=sum(r['callbacks'] for r in rows),
              nativeDecodedBytes=sum(r['decodedBytes'] for r in rows),
              recordChecksumsVerified=sum(r['recordChecksumsVerified'] for r in rows),
              cases=rows, marisaAEarlyComparisons=early,
              marisaAEasyClearStillMissing=True, actualApplicationAndCppThreads=True,
              graphicsRecordingBoundary=True, actualGpuWholeFlowAccepted=False,
              browserWholeFlowAccepted=False, declaredExternalStartupClock=True,
              arbitraryStartupSeedsAccepted=False, gameStateOrRngRestored=False,
              actualRetailScoreCodecInstructions=True, originalWholeGameUiSaveAccepted=False,
              audibleOutput=False, fullNewObservationTapesPersisted=False,
              sourceWasmSha256=sha(H / 'canonical-component/candidate.wasm'),
              productionGameCodeChanged=False, newRuntimeDeployed=False, completeGame=False,
              retainedTestExpectationFailure='artifacts/th14/ordinary-difficulties-nov14/reimua-easy-full-current/report.json',
              correctedExpectation='Easy no-continue clear unlocks selected Extra; retained native eligibility evidence confirms it.',
              evidence=evidence)
(H / 'qualified-easy.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('cases', 'marisaAEarlyComparisons', 'evidence')}))
