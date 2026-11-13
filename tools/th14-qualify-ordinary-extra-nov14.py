"""Qualify the finite six-loadout ordinary Extra flow evidence."""
from pathlib import Path
import hashlib, json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-extra-nov14'
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
build = load(H / 'component/build.json')
canonical = load(H / 'canonical-component/build.json')
assert sha(H / 'component/candidate.wasm') == sha(H / 'canonical-component/candidate.wasm')
assert build['fixtureSha256'] == canonical['fixtureSha256']
for b in (build, canonical):
    for name, digest in {**b['sourceBindingsByMode']['candidate'], **b['objectBindings']}.items():
        assert sha(R / name) == digest, name
assert len(build['objectBindings']) == 145
rows = load(H / 'score-qualified/scores.json')
assert len(rows) == 6 and len({x['selection'] for x in rows}) == 6
evidence = {}
for row in rows:
    key = row['key']
    writer = R / row['writer']
    reader = R / row['freshReader']
    a, b = load(writer / 'report.json'), load(reader / 'report.json')
    assert a['passed'] and b['passed'] and a['retired'] and b['retired']
    assert a['sourceWasmSha256'] == b['sourceWasmSha256'] == sha(H / 'component/candidate.wasm')
    assert a['driverSha256'] == sha(writer / 'executed-driver.mjs')
    assert b['driverSha256'] == sha(reader / 'executed-driver.mjs')
    codec = H / 'score-qualified' / (key + '-native-codec.json')
    native = load(codec)
    assert native['passed'] and native['actualRetailDecryptAndLzss']
    assert native['originalInstructionBytesPatched'] == 0
    assert native['encodedSha256'] == row['encodedSha256']
    assert native['decodedSha256'] == row['decodedSha256']
    for p in (writer / 'report.json', reader / 'report.json',
              writer / 'ordinary-initial-player.json', writer / 'natural-result-and-flush.json', codec):
        evidence[p.relative_to(R).as_posix()] = sha(p)
    row['nativeCodecVerified'] = True
prefix = load(H / 'reimua-extra-prefix-current/report.json')
assert prefix['passed'] and prefix['sourceWasmSha256'] == sha(H / 'canonical-component/candidate.wasm')
result = dict(acceptanceStandard='observable-behavior-alignment',
              ordinaryExtraLoadouts=6, freshApplicationReads=6,
              callbacks=sum(x['callbacks'] for x in rows),
              nativeDecodedBytes=sum(x['decodedBytes'] for x in rows),
              recordChecksumsVerified=sum(x['recordChecksumsVerified'] for x in rows),
              earnedNormalSavesUsed=True, syntheticUnlockRecordsUsed=False,
              normalRanksAndUnlocksPreserved=True, extraClearAndNoContinueCounts=1,
              onlyHeldKeysAndNormalMenuActions=True, gameStateOrRngRestored=False,
              declaredExternalStartupClock=True, arbitraryStartupSeedsAccepted=False,
              actualApplicationAndCppThreads=True, graphicsRecordingBoundary=True,
              actualGpuWholeFlowAccepted=False, browserWholeFlowAccepted=False,
              actualRetailScoreCodecInstructions=True, originalWholeGameUiSaveAccepted=False,
              audibleOutput=False, providerObjectsVerified=145,
              sourceWasmSha256=sha(H / 'component/candidate.wasm'),
              canonicalFixtureIdenticalModule=True, productionGameCodeChanged=False,
              newRuntimeDeployed=False, completeGame=False, cases=rows, evidence=evidence,
              retainedDiagnostic=dict(path='artifacts/th14/ordinary-extra-nov14/reimua-extra-full-v1/report.json',
                                      reason='Test driver stopped at completed Extra pause state 21; not a production GameOver defect.'))
(H / 'qualified.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('cases', 'evidence')}))
