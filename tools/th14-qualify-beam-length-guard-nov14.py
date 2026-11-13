"""Qualify the bounded-fallback candidate and two affected normal campaigns."""
from pathlib import Path
import ast, hashlib, importlib.util, json, struct, sys

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/beam-length-guard-nov14'
O = H / 'score-qualified'
O.mkdir(exist_ok=True)
load = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
change, build = load(H / 'source-change.json'), load(H / 'component/build.json')
assert sha(R / change['source']) == change['afterSha256']
for name, digest in {**build['sourceBindingsByMode']['candidate'], **build['objectBindings']}.items():
    assert sha(R / name) == digest, name
guard, native, other = (load(H / 'guard-tests.json'), load(R / 'docs/porting/th14-shot-beam-hit-verified.json'),
                       load(H / 'other-title-objects.json'))
assert guard['passed'] and guard['invalidFallbackCases'] == 30 and guard['normalIntersectionCases'] == 5
assert native['passed'] and native['hits'] == 4032 and native['negativeScratchEdges'] == 48
assert native['wasmSha256'] == guard['wasmSha256']
assert native['sourceHashes']['cpp/game/ShotCallbacksTh14.cpp'] == change['afterSha256']
assert other['passed'] and len(other['cases']) == 3
assert 'AssertionError' in (H / 'before-negative-control.log').read_text(encoding='utf-8', errors='replace')
source = R / 'tools/th14-audit-root-full-extra-nov08.py'
fn = next(n for n in ast.parse(source.read_text()).body
          if isinstance(n, ast.FunctionDef) and n.name == 'decode_score')
spec = importlib.util.spec_from_file_location('mirror', R / 'tools/th-replay-container.py')
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)
scope = dict(struct=struct, mirror=mirror)
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), str(source), 'exec'), scope)
cases, evidence = [], {}
for role, selection, expected, callbacks in [('marisaa', 2, 775709810, 107461), ('marisab', 3, 1019280950, 123424)]:
    root = R / 'artifacts/th14/ordinary-difficulties-nov14'
    writer, reader = root / (role + '-normal-beam-guard-v1'), root / (role + '-normal-beam-guard-fresh-v1')
    a, b = load(writer / 'report.json'), load(reader / 'report.json')
    assert all(x['passed'] and x['retired'] and not x['exception'] for x in (a, b))
    for folder, report in ((writer, a), (reader, b)):
        assert not load(folder / 'platform.json')['audibleOutput']
        assert report['sourceWasmSha256'] == build['outputs']['candidate']['wasmSha256']
        assert report['driverSha256'] == sha(folder / 'executed-driver.mjs')
        evidence[(folder / 'report.json').relative_to(R).as_posix()] = sha(folder / 'report.json')
    encoded = (writer / 'save/scoreth14.dat').read_bytes()
    assert encoded == (reader / 'save/scoreth14.dat').read_bytes()
    decoded = scope['decode_score'](encoded)
    assert len(decoded) == 149076
    for i in range(8):
        size = 0x5298 if i < 7 else 0x42c
        record = decoded[i * 0x5298:i * 0x5298 + size]
        assert struct.unpack_from('<I', record)[0] == (0x15243 if i < 7 else 0x15453)
        assert struct.unpack_from('<I', record, 8)[0] == size
        assert sum(record[8:]) == struct.unpack_from('<I', record, 4)[0]
    offset = selection * 0x5298
    for base in (0x7c0, 0x7dc):
        assert struct.unpack_from('<5I', decoded, offset + base) == (0, 1, 0, 0, 0)
    rank = offset + 0x10 + 0x118
    assert struct.unpack_from('<I', decoded, rank)[0] * 10 == expected
    assert list(decoded[rank + 4:rank + 6]) == [8, 0]
    fresh = (reader / 'score-observed.bin').read_bytes()
    assert fresh[rank:rank + 0x118] == decoded[rank:rank + 0x118]
    assert load(writer / 'observations-summary.json')['callbacks'] == callbacks
    key = role + '-normal'
    (O / (key + '-decoded.bin')).write_bytes(decoded)
    row = dict(key=key, selection=selection, writer=writer.relative_to(R).as_posix(),
               freshReader=reader.relative_to(R).as_posix(), finalScore=expected, callbacks=callbacks,
               encodedSha256=hashlib.sha256(encoded).hexdigest(), decodedSha256=hashlib.sha256(decoded).hexdigest(),
               encodedBytes=len(encoded), decodedBytes=len(decoded), scoreAndCountersPreserved=True)
    cases.append(row)
hard = load(R / 'artifacts/th14/ordinary-difficulties-nov14/marisaa-hard-beam-guard-v1/report.json')
assert hard['retired'] and not hard['exception'] and not hard['passed'] and hard['outcome'] == 'natural-game-over'
(O / 'scores.json').write_text(json.dumps(cases, indent=2) + '\n')
native_scores = '--require-native' in sys.argv
if native_scores:
    for row in cases:
        p = O / (row['key'] + '-native-codec.json')
        codec = load(p)
        assert codec['passed'] and codec['originalInstructionBytesPatched'] == 0
        assert codec['encodedSha256'] == row['encodedSha256']
        assert codec['decodedSha256'] == row['decodedSha256']
        evidence[p.relative_to(R).as_posix()] = sha(p)
        row['nativeCodecVerified'] = True
result = dict(passed=True, sourceChange=change, nativeValidHitCases=4032, nativeNegativeEdges=48,
    invalidFallbackCases=30, ordinaryIntersectionControls=5, oldCodeNegativeControlRejected=True,
    recompiledGameProviders=1, verifiedReusedProviders=144, otherTitleObjectsUnchanged=[12, 13, 16],
    affectedNormalClears=2, freshApplicationReads=2, callbacks=sum(x['callbacks'] for x in cases),
    nativeScoreDecoderVerified=native_scores, nativeDecodedBytes=298152 if native_scores else 0,
    cases=cases, hardStillEndedEarly=True, originalUndefinedStackBugPreservedExactly=False,
    coreSourceChanged=True, browserModuleBuilt=False, deployed=False, actualGpuAccepted=False,
    silent=True, completeGame=False, wasmSha256=build['outputs']['candidate']['wasmSha256'], evidence=evidence)
(H / 'qualified.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('cases', 'evidence')}))
