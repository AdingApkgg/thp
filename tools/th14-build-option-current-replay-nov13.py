"""Link current normal providers to the retained low-pause replay observer."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13/current-replay'
O = H / 'component'
O.mkdir(parents=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
core_path = H.parent / 'candidate-providers/build.json'
core = load(core_path)
S = R / core['sourceSnapshotRoot']
for name, digest in core['sourceBindings'].items():
    assert sha(R / name) == sha(S / name) == digest, name
objects = {}
for row in core['currentProviders']:
    path = R / row['object']
    assert sha(path) == row['objectSha256']
    objects[row['object']] = row['objectSha256']
parent_path = R / 'artifacts/th14/player-initialization-oracle-nov13/application/component/build.json'
parent = load(parent_path)
for name in ['th12_web/cpp/sdl/AudioDevice.cpp', 'th12_web/cpp/sdl/FontDevice.cpp',
             'th12_web/cpp/sdl/GraphicsDevice.cpp', 'portable/sdl/Renderer.cpp']:
    key = 'runtimes/th12/' + name
    frozen = 'artifacts/th14/player-initialization-oracle-nov13/candidate-providers/source/' + key
    assert sha(R / key) == core['sourceBindings'][key] == parent['sourceBindings'][frozen]
for obj in list(parent['objectBindings'])[-4:]:
    assert sha(R / obj) == parent['objectBindings'][obj]
    objects[obj] = parent['objectBindings'][obj]
assert len(objects) == 145
prior = R / 'artifacts/th14/current-low-pause-transition-nov12'
old = load(prior / 'component/build.json')
assert sha(prior / 'component/fixture.cpp') == old['fixtureSha256']
for name in ['fixture.cpp', 'Th14WarmAttractCase.hpp']:
    (O / name).write_bytes((prior / 'component' / name).read_bytes())
for name in ['native-reference-metadata.json', 'native-terminal-receipt.json']:
    (H / name).write_bytes((prior / name).read_bytes())
cc = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc) == core['compilerSha256']
flags = core['flags'] + ['-I' + str(S / 'runtimes/th12/th12_web/cpp/sdl'),
                        '-I' + str(S / 'runtimes/th12/portable/sdl'),
                        '-I' + str(R / 'artifacts/th14/boot-main-intake-nov07/application-component/include')]
cmd = [str(cc), *flags, '-fno-access-control', '-mexec-model=reactor',
       '-Wl,--no-entry', '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
       '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824',
       '-Wl,-z,stack-size=1048576', str(O / 'fixture.cpp'),
       *[str(R / n) for n in objects], '-o', str(O / 'candidate.wasm')]
with (O / 'compile.log').open('wb') as log:
    subprocess.run(cmd, cwd=R, env=dict(os.environ, TEMP=str(O), TMP=str(O), TMPDIR=str(O)),
                   stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
bindings = {(S / n).relative_to(R).as_posix(): h for n, h in core['sourceBindings'].items()}
for p in [Path(__file__), O / 'fixture.cpp', O / 'Th14WarmAttractCase.hpp',
          R / 'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp']:
    bindings[p.relative_to(R).as_posix()] = sha(p)
report = dict(old, sourceBindingsByMode={'candidate': bindings}, objectBindings=objects,
              fixturePath=(O / 'fixture.cpp').relative_to(R).as_posix(),
              fixtureSha256=sha(O / 'fixture.cpp'), wasmSha256=sha(O / 'candidate.wasm'),
              outputs={'candidate': {'wasmSha256': sha(O / 'candidate.wasm')}},
              compilerSha256=sha(cc), command=cmd, productionGameSource=None,
              productionGameSourceBase='b8e36ef27d96238352f5edaf9b368ca23394ceb3',
              localSourceChanges=load(H.parent / 'candidate-edits.json'),
              gameObjectsReusedAndReverified=141, hostObjectsReusedAndReverified=4,
              normalAccessFor145LinkedProviders=True,
              fixtureIncludesApplicationWithExistingRelaxedObserverAccess=True,
              providerBuildSha256=sha(core_path), hostProviderBuildSha256=sha(parent_path),
              nativeRunStarted=False, completeGame=False)
(O / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
driver = (R / 'tools/th14-run-current-low-pause-transition-nov12.mjs').read_text()
driver = driver.replace('artifacts/th14/current-low-pause-transition-nov12',
                        'artifacts/th14/option-refresh-oracle-nov13/current-replay')
driver = driver.replace('th14-full-application-gles-transition-type0-nov09.mjs',
                        'th14-full-application-production-fences-nov12.mjs')
anchor = 'await Promise.all(pools.map(p=>p.shutdown()));clock.close();'
assert driver.count(anchor) == 1
driver = driver.replace(anchor, anchor + '\n await platform.closeServices();')
path = R / 'tools/th14-run-option-current-replay-nov13.mjs'
assert not path.exists()
path.write_text(driver, encoding='utf8', newline='\n')
(H / 'driver-prepared.json').write_text(json.dumps(dict(
    driverSha256=sha(path), parentDriverSha256=sha(R / 'tools/th14-run-current-low-pause-transition-nov12.mjs'),
    newCurrentSourceRun=True, newNativeRun=False, noPerFileReadinessSchedule=True,
    productionFenceAndDeliveryServices=True, completeGame=False), indent=2) + '\n')
print(json.dumps(dict(compiled=True, providers=145, wasmSha256=report['wasmSha256'],
                      driverSha256=sha(path))))
