"""Bind the current engine to a retained low-pause reference's observer.

Only a new C++/Wasm run is prepared. No native game or asset copy is created.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/current-low-pause-transition-nov12'
O = H / 'component'
P = R / 'artifacts/th14/control-main-stop-nov12'
B = R / 'artifacts/th14/current-audio-full-normal-nov09/component'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
assert not H.exists(), 'Preserve previous results'
core = load(P / 'current-core/build.json')
previous = load(B / 'build.json')
assert core['normalEngineAccessControl']
for name, digest in core['sourceBindings'].items():
    assert sha(R / name) == digest, name
objects = {}
for row in core['currentProviders']:
    assert sha(Path(row['object'])) == row['objectSha256']
    objects[Path(row['object']).relative_to(R).as_posix()] = row['objectSha256']
assert len(objects) == 141
host = P / 'first-present/probe-v2/candidate'
host_bindings = load(host / 'actual-link-object-bindings.json')['actualLinkObjectBindings']
for name in ['AudioDevice', 'FontDevice', 'GraphicsDevice', 'Renderer']:
    p = host / 'objects' / (name + '.o')
    key = p.relative_to(R).as_posix()
    assert sha(p) == host_bindings[key]
    objects[key] = sha(p)
rt = R / 'runtimes/th12'
frozen = R / 'artifacts/th14/initial-overlay-publication-nov11/source'
for name in ['th12_web/cpp/sdl/AudioDevice.cpp', 'th12_web/cpp/sdl/FontDevice.cpp',
             'th12_web/cpp/sdl/GraphicsDevice.cpp', 'portable/sdl/Renderer.cpp']:
    assert (rt / name).read_bytes() == (frozen / name).read_bytes(), name
fixture = B / 'fixture.cpp'
assert sha(fixture) == previous['fixtureSha256']
source = fixture.read_text(encoding='utf8')
source += '\nAPI(async_deliver_owned) void async_deliver_owned(u32 callback,u32 data){th14_async_invoke(callback,data);}\n'
O.mkdir(parents=True)
(O / 'fixture.cpp').write_text(source, encoding='utf8', newline='\n')
header = P / 'first-present/probe-v2/Th14WarmAttractCase.hpp'
(O / 'Th14WarmAttractCase.hpp').write_bytes(header.read_bytes())
cc = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc) == core['compilerSha256']
flags = core['flags'] + ['-I' + str(rt / 'th12_web/cpp/sdl'), '-I' + str(rt / 'portable/sdl'),
    '-I' + str(R / 'artifacts/th14/boot-main-intake-nov07/application-component/include')]
command = [str(cc), *flags, '-fno-access-control', '-mexec-model=reactor',
    '-Wl,--no-entry', '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
    '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824',
    '-Wl,-z,stack-size=1048576', str(O / 'fixture.cpp'),
    *[str(R / name) for name in objects], '-o', str(O / 'candidate.wasm')]
(O / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
with (O / 'compile.log').open('wb') as log:
    result = subprocess.run(command, cwd=R, env=dict(os.environ, TEMP=str(O), TMP=str(O), TMPDIR=str(O)),
        stdout=log, stderr=subprocess.STDOUT, timeout=240)
assert result.returncode == 0, (O / 'compile.log').read_text(errors='replace')[-6000:]
bindings = dict(core['sourceBindings'])
for directory in [rt / 'th12_web/cpp/sdl', rt / 'portable/sdl']:
    for p in directory.iterdir():
        if p.is_file() and p.suffix in ['.cpp', '.hpp']:
            bindings[p.relative_to(R).as_posix()] = sha(p)
for p in [Path(__file__), O / 'fixture.cpp', O / 'Th14WarmAttractCase.hpp',
          rt / 'th12_web/tests/cpp/th14-native-title-live-observer.hpp']:
    bindings[p.relative_to(R).as_posix()] = sha(p)
report = dict(previous, compiled=True, actualColdApplicationInitializeTickAndDraw=True,
    noDeclaredPerFileReadinessSchedule=True, sourceBindingsByMode={'candidate': bindings},
    objectBindings=objects, fixtureSha256=sha(O / 'fixture.cpp'),
    fixturePath=(O / 'fixture.cpp').relative_to(R).as_posix(),
    wasmSha256=sha(O / 'candidate.wasm'), outputs={'candidate': {'wasmSha256': sha(O / 'candidate.wasm')}},
    gameObjectsReusedAndReverified=141, hostObjectsReusedAndReverified=4,
    canonicalCurrentApplicationIncluded=True, normalAccessFor145LinkedProviders=True,
    fixtureIncludesApplicationWithExistingRelaxedObserverAccess=True,
    parentFixtureSha256=sha(fixture), compilerSha256=sha(cc),
    productionGameSource='e6b15d27768ee4da293c81c3c239e3d42880020b',
    nativeRunStarted=False, productionChanged=False, completeGame=False)
(O / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(compiled=True, wasmSha256=report['wasmSha256'], providers=145)))
