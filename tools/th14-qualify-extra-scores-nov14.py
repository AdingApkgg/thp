"""Audit ordinary Extra scores against earned Normal saves and fresh readers."""
from pathlib import Path
import ast, hashlib, importlib.util, json, struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-extra-nov14'
O = H / 'score-qualified'
O.mkdir(exist_ok=True)
source = R / 'tools/th14-audit-root-full-extra-nov08.py'
fn = next(n for n in ast.parse(source.read_text()).body
          if isinstance(n, ast.FunctionDef) and n.name == 'decode_score')
spec = importlib.util.spec_from_file_location('mirror', R / 'tools/th-replay-container.py')
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)
scope = dict(struct=struct, mirror=mirror)
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), str(source), 'exec'), scope)
load = lambda p: json.loads(p.read_bytes())
sha = lambda b: hashlib.sha256(b).hexdigest()
normal = load(R / 'artifacts/th14/ordinary-loadouts-nov13/score-qualified/scores.json')
rows = []
for selection, role in enumerate(['reimua', 'reimub', 'marisaa', 'marisab', 'sakuyaa', 'sakuyab']):
    key = role + '-extra'
    writer, reader = H / (key + '-full-v2'), H / (key + '-fresh-v1')
    a, b = load(writer / 'report.json'), load(reader / 'report.json')
    assert all(x['passed'] and x['retired'] and not x['exception'] for x in (a, b))
    assert a['actualOrdinaryHeldInput'] and not a['recordedGameStateRestored']
    assert a['noRngStateWrites'] and not a['completionBoundaryInvokedDirectly']
    assert a['visitedStages'] == [7] and a['resultSeen'] and not a['endingSeen']
    for folder in (writer, reader):
        assert not load(folder / 'platform.json')['audibleOutput']
    assert load(writer / 'ordinary-initial-player.json')['initialSeedMatched']
    meta = load(R / 'artifacts/th14/royalflare-coverage-matrix-oct16/inputs' / (key + '-source.json'))
    assert (writer / 'observations.u32').stat().st_size // 456 == meta['stages'][0]['frames']
    encoded = (writer / 'save/scoreth14.dat').read_bytes()
    assert encoded == (reader / 'save/scoreth14.dat').read_bytes()
    decoded = scope['decode_score'](encoded)
    assert len(decoded) == 149076
    before_encoded = (R / normal[selection]['writer'] / 'save/scoreth14.dat').read_bytes()
    assert sha(before_encoded) == normal[selection]['encodedSha256']
    before = scope['decode_score'](before_encoded)
    for i in range(8):
        size = 0x5298 if i < 7 else 0x42c
        record = decoded[i * 0x5298:i * 0x5298 + size]
        assert struct.unpack_from('<I', record)[0] == (0x15243 if i < 7 else 0x15453)
        assert struct.unpack_from('<I', record, 8)[0] == size
        assert sum(record[8:]) == struct.unpack_from('<I', record, 4)[0]
    # Every ordinary difficulty rank is preserved, including the earned Normal result.
    for i in range(7):
        start = i * 0x5298 + 0x10
        assert decoded[start:start + 4 * 0x118] == before[start:start + 4 * 0x118]
    for i in range(6):
        if i != selection:
            start = i * 0x5298
            assert decoded[start:start + 0x5298] == before[start:start + 0x5298]
    offset = selection * 0x5298
    for base in (0x7c0, 0x7dc):
        assert struct.unpack_from('<I', decoded, offset + base + 4)[0] == 1
        assert struct.unpack_from('<I', before, offset + base + 16)[0] == 0
        assert struct.unpack_from('<I', decoded, offset + base + 16)[0] == 1
    assert decoded[7 * 0x5298 + 0x16:7 * 0x5298 + 0x1d] == before[7 * 0x5298 + 0x16:7 * 0x5298 + 0x1d]
    result = load(writer / 'natural-result-and-flush.json')
    rank = offset + 0x10 + 4 * 0x118
    score = struct.unpack_from('<I', decoded, rank)[0] * 10
    assert list(decoded[rank + 4:rank + 6]) == [8, 0]
    assert score == result['rank']['scoreUnits'] * 10 == int(meta['archiveRow'][1].replace(',', ''))
    fresh_observed = (reader / 'score-observed.bin').read_bytes()
    assert len(fresh_observed) == len(decoded)
    assert fresh_observed[rank:rank + 0x118] == decoded[rank:rank + 0x118]
    (O / (key + '-decoded.bin')).write_bytes(decoded)
    rows.append(dict(key=key, selection=selection, writer=writer.relative_to(R).as_posix(),
                     freshReader=reader.relative_to(R).as_posix(),
                     encodedSha256=sha(encoded), decodedSha256=sha(decoded),
                     encodedBytes=len(encoded), decodedBytes=len(decoded), recordChecksumsVerified=8,
                     normalSaveSourceSha256=sha(before_encoded), normalRanksPreserved=True,
                     unrelatedRolesPreserved=True, normalUnlockFlagsPreserved=True,
                     extraClearCount=1, extraNoContinueClearCount=1, finalScore=score,
                     callbacks=meta['stages'][0]['frames'], silent=True))
(O / 'scores.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows))
