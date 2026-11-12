"""Check the TH14-only Player initialization edit against other title objects."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13'
O = H / 'other-title-controls'
S = O / 'runtimes/th12/th12_web/cpp/game'
S.mkdir(parents=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
game = R / 'runtimes/th12/th12_web/cpp/game'
provider_path = H / 'candidate-providers/build.json'
provider = json.loads(provider_path.read_bytes())
edit = json.loads((H / 'candidate-edits.json').read_bytes())
assert sha(H / 'baseline-PlayerFrame.cpp') == edit['beforeSha256']
assert sha(game / 'PlayerFrame.cpp') == edit['afterSha256']
for name, digest in provider['sourceBindings'].items():
    assert sha(R / name) == digest, name
    if name.startswith('runtimes/th12/portable/'):
        target = O / name
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(R / name, target)
for p in game.iterdir():
    if p.is_file() and p.suffix in ['.cpp', '.hpp', '.h', '.inc']:
        os.link(p, S / p.name)
cc = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc) == provider['compilerSha256']
flags = [f for f in provider['flags'] if not f.startswith(('-I', '-DPORT_TITLE='))]
assert '-fno-access-control' not in flags
results = {}
for mode, source in [('baseline', H / 'baseline-PlayerFrame.cpp'),
                     ('candidate', game / 'PlayerFrame.cpp')]:
    temp = S / 'PlayerFrame.cpp.tmp'
    temp.write_bytes(source.read_bytes())
    os.replace(temp, S / 'PlayerFrame.cpp')
    for title in [12, 13, 16]:
        obj = O / f'{mode}-{title}-PlayerFrame.cpp.o'
        cmd = [str(cc), *flags, f'-DPORT_TITLE={title}', '-I' + str(S),
               '-c', str(S / 'PlayerFrame.cpp'), '-o', str(obj)]
        with obj.with_suffix('.log').open('wb') as log:
            subprocess.run(cmd, cwd=R, env=dict(os.environ, TEMP=str(O),
                           TMP=str(O), TMPDIR=str(O)), stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=120)
        results[mode, title] = sha(obj)
pairs = [dict(title=t, baselineSha256=results['baseline', t],
              candidateSha256=results['candidate', t],
              identical=results['baseline', t] == results['candidate', t])
         for t in [12, 13, 16]]
report = dict(passed=all(p['identical'] for p in pairs), pairs=pairs,
              sameSourcePathForBothPhases=True, normalAccessControl=True,
              compilerSha256=sha(cc), providerBuildSha256=sha(provider_path),
              toolSha256=sha(Path(__file__)), completeGame=False)
(O / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(passed=report['passed'], pairs=len(pairs))))
assert report['passed']
