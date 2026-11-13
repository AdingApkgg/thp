"""Verify an ordinary ranked GameOver, Continue, title save and fresh read."""
from pathlib import Path
import ast, hashlib, importlib.util, json, struct

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-difficulties-nov14'
O = H / 'continue-score-qualified'
O.mkdir(exist_ok=True)
load = lambda p: json.loads(p.read_bytes())
sha = lambda b: hashlib.sha256(b).hexdigest()
writer = H / 'marisaa-easy-gameover-continue-title-v2'
reader = H / 'marisaa-easy-gameover-continue-fresh-v2'
a, b = load(writer / 'report.json'), load(reader / 'report.json')
assert all(r['passed'] and r['retired'] and not r['exception'] for r in (a, b))
assert a['ordinaryGameOverContinuePauseTitleAccepted'] and not a['naturalFullCampaignAccepted']
assert a['visitedStages'] == [1, 2, 3] and a['noRngStateWrites'] and not a['recordedGameStateRestored']
for folder, report in ((writer, a), (reader, b)):
    assert not load(folder / 'platform.json')['audibleOutput']
    assert sha((folder / 'executed-driver.mjs').read_bytes()) == report['driverSha256']
continued = load(writer / 'continued-in-place.json')
assert continued['outcome'][2:7] == [2, 0, 3, 0, 400]
advanced = load(writer / 'continue-gameplay-advanced.json')
assert advanced['behavior'][1] == continued['stoppedStage'] == 3
assert advanced['behavior'][5] > continued['stoppedControl'] == 13734
assert advanced['behavior'][8] == 1
encoded = (writer / 'save/scoreth14.dat').read_bytes()
assert encoded == (reader / 'save/scoreth14.dat').read_bytes()
source = R / 'tools/th14-audit-root-full-extra-nov08.py'
fn = next(n for n in ast.parse(source.read_text()).body
          if isinstance(n, ast.FunctionDef) and n.name == 'decode_score')
spec = importlib.util.spec_from_file_location('mirror', R / 'tools/th-replay-container.py')
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)
scope = dict(struct=struct, mirror=mirror)
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), str(source), 'exec'), scope)
decoded = scope['decode_score'](encoded)
assert len(decoded) == 149076
for i in range(8):
    size = 0x5298 if i < 7 else 0x42c
    record = decoded[i * 0x5298:i * 0x5298 + size]
    assert struct.unpack_from('<I', record)[0] == (0x15243 if i < 7 else 0x15453)
    assert struct.unpack_from('<I', record, 8)[0] == size
    assert sum(record[8:]) == struct.unpack_from('<I', record, 4)[0]
offset = 2 * 0x5298
for base in (0x7c0, 0x7dc):
    assert struct.unpack_from('<5I', decoded, offset + base) == (0, 0, 0, 0, 0)
assert not any(decoded[7 * 0x5298 + 0x16:7 * 0x5298 + 0x1d])
rank = offset + 0x10
assert struct.unpack_from('<I', decoded, rank)[0] == 8243413
assert list(decoded[rank + 4:rank + 6]) == [3, 0]
fresh = (reader / 'score-observed.bin').read_bytes()
assert fresh[rank:rank + 0x118] == decoded[rank:rank + 0x118]
key = 'marisaa-easy-continue'
(O / (key + '-decoded.bin')).write_bytes(decoded)
row = dict(key=key, selection=2, writer=writer.relative_to(R).as_posix(),
           freshReader=reader.relative_to(R).as_posix(), encodedSha256=sha(encoded),
           decodedSha256=sha(decoded), encodedBytes=len(encoded), decodedBytes=len(decoded),
           recordChecksumsVerified=8, rankScore=82434130, rankStage=3, rankContinues=0,
           gameOverScoreRankPreservedAfterContinue=True, continuedActiveLives=2,
           continuedActiveBombs=3, continuedPower=400, returnedToTitle=True,
           callbacks=load(writer / 'observations-summary.json')['callbacks'],
           clearCountsAndExtraUnlockRemainZero=True, silent=True, completeGame=False)
(O / 'scores.json').write_text(json.dumps([row], indent=2) + '\n')
print(json.dumps(row))
