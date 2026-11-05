"""Relink the per-store observation host over 141 unchanged bound objects."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/natural-store-boundaries-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()
base_path = R / 'artifacts/th14/shot-lifetime-nov05/build-retry1/observer-build.json'
raw = base_path.read_bytes()
base = json.loads(raw)
assert base['wasmSha256'] == '1fcd416817b86822182429e12431f97475180f6c41a3a8a24e0641636076ecc6'
assert SHA((base_path.parent / 'observer.wasm').read_bytes()) == base['wasmSha256']
assert len(base['objectBindings']) == 141
for row in base['objectBindings']:
    assert SHA(Path(row['path']).read_bytes()) == row['sha256']
for name, digest in {**base['sourceHashes'], **base['headerHashes']}.items():
    assert SHA((Path(base['sourceSnapshotRoot']) / name).read_bytes()) == digest
for name, digest in base['fixtureDependencyHashes'].items():
    assert SHA(Path(name).read_bytes()) == digest
out = H / 'build-retry1'
assert not out.exists()
out.mkdir()
fixture = R / 'runtimes/th12/th12_web/tests/cpp/th14-natural-store-scheduler-nov05.cpp'
source = fixture.read_text(encoding='utf8')
needle = '#include "th14-shot-lifetime-observer-nov05.cpp"'
assert source.count(needle) == 1
source = source.replace(needle, '#include "'+Path(base['fixtureGraphRoot']).as_posix()+'"')
frozen = out / 'fixture.cpp'
frozen.write_text(source, encoding='utf8', newline='\n')
compiler = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert SHA(compiler.read_bytes()) == base['compilerSha256']
argv = [str(compiler), *base['flags'], *base['linkFlags'], str(frozen),
        *[row['path'] for row in base['objectBindings']], '-o', str(out / 'observer.wasm')]
(out / 'argv.json').write_text(json.dumps(argv,indent=2)+'\n')
with (out / 'link.log').open('wb') as log:
    process = subprocess.run(argv, cwd=R, env={**os.environ,'TEMP':str(out),'TMP':str(out)},
                             stdout=log, stderr=subprocess.STDOUT, timeout=180)
assert process.returncode == 0, 'Retain compiler diagnostics in build/link.log'
deps = dict(base['fixtureDependencyHashes'])
deps[frozen.as_posix()] = SHA(frozen.read_bytes())
report = dict(base)
report.update(fixtureGraphRoot=str(frozen), expandedFixtureSha256=SHA(frozen.read_bytes()),
    fixtureDependencyHashes=deps, wasmSha256=SHA((out / 'observer.wasm').read_bytes()),
    baseBuildSha256=SHA(raw), engineSourcesRecompiledForThisLink=0, engineObjectsReusedForThisLink=141,
    rootProductionSourcesModified=False, perStoreObservationHostAdded=True,
    observerSourceSha256=SHA(fixture.read_bytes()), buildToolSha256=SHA(Path(__file__).read_bytes()),
    independentSchedulingAccepted=False, completeGame=False)
(out / 'observer-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(compiled=True,engineObjectsReused=141,wasmSha256=report['wasmSha256'],
                     formalGameplayChanged=False,completeGame=False)))
