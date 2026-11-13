"""Qualify finite Hard/Lunatic clears and ranked GameOver continuation."""
from pathlib import Path
import hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-difficulties-nov14'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
build = load(H / 'canonical-component/build.json')
for name, digest in {**build['sourceBindingsByMode']['candidate'], **build['objectBindings']}.items():
    assert sha(R / name) == digest, name
wasm = sha(H / 'canonical-component/candidate.wasm')
groups, evidence = {}, {}
for mode, expected in [('hard', {0, 1, 3, 4, 5}), ('lunatic', {0, 1, 2, 4, 5}), ('continue', {2})]:
    directory = H / (mode + '-score-qualified')
    rows = load(directory / 'scores.json')
    assert {r['selection'] for r in rows} == expected
    for row in rows:
        codec_path = directory / (row['key'] + '-native-codec.json')
        codec = load(codec_path)
        assert codec['passed'] and codec['originalInstructionBytesPatched'] == 0
        assert codec['encodedSha256'] == row['encodedSha256']
        assert codec['decodedSha256'] == row['decodedSha256']
        assert codec['toolSha256'] == sha(R / 'tools/th14-campaign-score-native-codec-nov14.py')
        row['nativeCodecVerified'] = True
        for rel in (row['writer'], row['freshReader']):
            folder = R / rel
            report = load(folder / 'report.json')
            assert report['passed'] and report['retired'] and not report['exception']
            assert report['sourceWasmSha256'] == wasm
            assert report['driverSha256'] == sha(folder / 'executed-driver.mjs')
            assert not load(folder / 'platform.json')['audibleOutput']
            evidence[(folder / 'report.json').relative_to(R).as_posix()] = sha(folder / 'report.json')
        evidence[codec_path.relative_to(R).as_posix()] = sha(codec_path)
    groups[mode] = rows
early = load(H / 'higher-early-native-audit.json')
assert len(early) == 2 and all(not x['currentClearAccepted'] for x in early)
assert [len(x['differentTerminalFields']) for x in early] == [9, 1]
evidence['artifacts/th14/ordinary-difficulties-nov14/higher-early-native-audit.json'] = sha(H / 'higher-early-native-audit.json')
clear_rows = groups['hard'] + groups['lunatic']
result = dict(acceptanceStandard='observable-behavior-alignment', ordinaryHardClears=5,
              ordinaryLunaticClears=5, clearFreshApplicationReads=10,
              clearCallbacks=sum(r['callbacks'] for r in clear_rows),
              nativeDecodedBytes=sum(r['decodedBytes'] for rows in groups.values() for r in rows),
              recordChecksumsVerified=sum(r['recordChecksumsVerified'] for rows in groups.values() for r in rows),
              ordinaryRankedGameOverContinueTitleAndFreshRead=True,
              allSixHigherDifficultyClearsAccepted=False, cases=groups,
              earlyOrdinaryVersusNativeReplayDiagnostics=early,
              hardMarisaATerminalDifferenceCauseEstablished=False,
              lunaticMarisaBTerminalScoreUnitDifferenceRetained=True,
              actualApplicationAndCppThreads=True, graphicsRecordingBoundary=True,
              actualGpuWholeFlowAccepted=False, browserWholeFlowAccepted=False,
              declaredExternalStartupClock=True, arbitraryStartupSeedsAccepted=False,
              gameStateOrRngRestored=False, actualRetailScoreCodecInstructions=True,
              originalWholeGameUiSaveAccepted=False, audibleOutput=False,
              sourceWasmSha256=wasm, productionGameCodeChanged=False,
              newRuntimeDeployed=False, completeGame=False,
              retainedContinueTestFailure='artifacts/th14/ordinary-difficulties-nov14/marisaa-easy-gameover-continue-title-v1/report.json',
              continuedBombExpectation='Three after the completed death/respawn callback; earlier neutral-input evidence already covered transient two.',
              evidence=evidence)
(H / 'qualified-higher-and-continue.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('cases', 'earlyOrdinaryVersusNativeReplayDiagnostics', 'evidence')}))
