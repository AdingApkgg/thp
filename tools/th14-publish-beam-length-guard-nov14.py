"""Publish only reviewed TH14 goal, fixture, tools and behavioral evidence."""
from pathlib import Path
import base64, hashlib, json, subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/beam-length-guard-nov14'
O = H / 'publication'
O.mkdir(exist_ok=False)
q = json.loads((H / 'qualified.json').read_bytes())
assert q['passed'] and q['nativeScoreDecoderVerified'] and q['affectedNormalClears'] == 2
assert not q['completeGame'] and q['silent']
files = ['runtimes/th12/th12_web/cpp/game/ShotCallbacksTh14.cpp', 'tools/th14-build-beam-length-guard-nov14.py', 'tools/th14-check-beam-length-guard-nov14.mjs', 'tools/th14-qualify-beam-length-guard-nov14.py', 'tools/th14-oracle-live-damage-window-nov14.py', 'tools/th14-oracle-live-beam-hits-nov14.py', 'tools/th14-publish-beam-length-guard-nov14.py', 'docs/porting/th14-shot-beam-hit-verified.json', 'GOAL.md', 'docs/porting/TH14_BEAM_LENGTH_GUARD_NOV14.md', 'docs/porting/th14-beam-length-guard-nov14.json', 'docs/porting/TH14_REMAINING_ACCEPTANCE.md']
snapshots = {name: (R / name).read_bytes() for name in files}
assert sum(map(len, snapshots.values())) < 500000
assert json.loads(snapshots[files[-2]]) == q

def api(path, method=None, payload=None):
    cmd = ['C:/Program Files/GitHub CLI/gh.exe', 'api', 'repos/AdingApkgg/thp/' + path]
    if method:
        cmd += ['--method', method]
    if payload is not None:
        p = O / 'request.json'
        p.write_text(json.dumps(payload), encoding='utf-8')
        cmd += ['--input', str(p)]
    result = subprocess.run(cmd, cwd=R, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')[:1500]
    return json.loads(result.stdout)

parent = api('git/ref/heads/main')['object']['sha']
assert parent == '1ba1ab1bf96a7337c81e8ea711ac7e4f41acfd6e', parent
base = api('git/commits/' + parent)['tree']['sha']
tree = []
for name, data in snapshots.items():
    digest = api('git/blobs', 'POST', dict(content=base64.b64encode(data).decode(), encoding='base64'))['sha']
    assert digest == hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    tree.append(dict(path=name, mode='100644', type='blob', sha=digest))
(O / 'reviewed-plan.json').write_text(json.dumps(dict(parent=parent, files={n: hashlib.sha256(b).hexdigest() for n, b in snapshots.items()}, rawAssetsSavesOrBinaries=False), indent=2) + '\n')
new_tree = api('git/trees', 'POST', dict(base_tree=base, tree=tree))['sha']
commit = api('git/commits', 'POST', dict(message='Bound invalid TH14 beam fallback lengths; preserve native valid geometry and Normal saves', tree=new_tree, parents=[parent]))['sha']
assert api('git/ref/heads/main')['object']['sha'] == parent
for name, data in snapshots.items():
    assert (R / name).read_bytes() == data
api('git/refs/heads/main', 'PATCH', dict(sha=commit, force=False))
assert api('git/ref/heads/main')['object']['sha'] == commit
for item in tree:
    actual = api('contents/' + item['path'] + '?ref=' + commit)
    assert actual['sha'] == item['sha'], item['path']
receipt = dict(commit=commit, parent=parent, files=files, allPublishedBlobHashesVerified=True,
               force=False, sourceAndEvidencePublished=True, productionGameLogicChanged=True,
               newRuntimeDeployed=False, completeGame=False)
(O / 'published.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
