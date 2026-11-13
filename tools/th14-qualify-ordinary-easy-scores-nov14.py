"""Audit the five declared ordinary Easy clear saves and fresh reads.

Marisa A early-ending inputs remain outside this clear-save qualification.
"""
from pathlib import Path
import ast, hashlib, importlib.util, json, struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-difficulties-nov14'
O = H / 'score-qualified'
O.mkdir(exist_ok=True)
load = lambda p: json.loads(p.read_bytes())
sha = lambda b: hashlib.sha256(b).hexdigest()
source = R / 'tools/th14-audit-root-full-extra-nov08.py'
fn = next(n for n in ast.parse(source.read_text()).body
          if isinstance(n, ast.FunctionDef) and n.name == 'decode_score')
spec = importlib.util.spec_from_file_location('mirror', R / 'tools/th-replay-container.py')
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)
scope = dict(struct=struct, mirror=mirror)
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), str(source), 'exec'), scope)
build = load(H / 'canonical-component/build.json')
for name, digest in {**build['sourceBindingsByMode']['candidate'], **build['objectBindings']}.items():
    assert sha((R / name).read_bytes()) == digest, name
wasm = sha((H / 'canonical-component/candidate.wasm').read_bytes())
rows = []
for selection, role in enumerate(['reimua', 'reimub', 'marisaa', 'marisab', 'sakuyaa', 'sakuyab']):
    if selection == 2:
        continue
    key = role + '-easy'
    writer = H / (key + ('-full-alternate-v2' if selection == 2 else '-full-v2'))
    reader = H / (key + '-fresh-v2')
    a, b = load(writer / 'report.json'), load(reader / 'report.json')
    assert all(x['passed'] and x['retired'] and not x['exception'] for x in (a, b))
    assert a['sourceWasmSha256'] == b['sourceWasmSha256'] == wasm
    assert a['actualOrdinaryHeldInput'] and not a['recordedGameStateRestored']
    assert a['noRngStateWrites'] and not a['completionBoundaryInvokedDirectly']
    assert a['visitedStages'] == [1, 2, 3, 4, 5, 6] and a['endingSeen'] and a['resultSeen']
    for folder, report in ((writer, a), (reader, b)):
        assert not load(folder / 'platform.json')['audibleOutput']
        assert report['driverSha256'] == sha((folder / 'executed-driver.mjs').read_bytes())
    assert load(writer / 'ordinary-initial-player.json')['initialSeedMatched']
    meta_home = H / 'alternate-inputs' if selection == 2 else R / 'artifacts/th14/royalflare-coverage-matrix-oct16/inputs'
    meta = load(meta_home / (key + '-source.json'))
    assert sha((meta_home / (key + '.rpy')).read_bytes()) == meta['sha256']
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
        assert struct.unpack_from('<5I', decoded, offset + base) == (1, 0, 0, 0, 0)
    assert decoded[7 * 0x5298 + 0x16] == 1
    assert list(decoded[7 * 0x5298 + 0x17:7 * 0x5298 + 0x1d]) == [int(i == selection) for i in range(6)]
    rank = offset + 0x10
    result = load(writer / 'natural-result-and-flush.json')
    score = struct.unpack_from('<I', decoded, rank)[0] * 10
    archive = meta['archiveRow']
    if isinstance(archive, dict):
        archive = archive['cells']
    assert list(decoded[rank + 4:rank + 6]) == [8, 0]
    assert score == result['rank']['scoreUnits'] * 10 == int(archive[1].replace(',', ''))
    fresh = (reader / 'score-observed.bin').read_bytes()
    assert len(fresh) == len(decoded) and fresh[rank:rank + 0x118] == decoded[rank:rank + 0x118]
    tape = load(writer / 'observations-summary.json')
    assert tape['bytes'] == tape['callbacks'] * 456 and not tape['fullTapePersisted']
    (O / (key + '-decoded.bin')).write_bytes(decoded)
    rows.append(dict(key=key, selection=selection, writer=writer.relative_to(R).as_posix(),
                     freshReader=reader.relative_to(R).as_posix(),
                     encodedSha256=sha(encoded), decodedSha256=sha(decoded),
                     encodedBytes=len(encoded), decodedBytes=len(decoded), recordChecksumsVerified=8,
                     sourceReplaySha256=meta['sha256'], selectedEasyClearCount=1,
                     selectedEasyNoContinueCount=1, otherDifficultyClearCounts=0,
                     onlySelectedExtraUnlocked=True, finalScore=score,
                     callbacks=tape['callbacks'], observationsSha256=tape['sha256'],
                     fullObservationTapePersisted=False, silent=True))
(O / 'scores.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows))
