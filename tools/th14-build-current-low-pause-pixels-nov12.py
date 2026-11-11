"""Build current Application for an existing debugger-free GPU reference."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/current-low-pause-pixels-nov12'
O = H / 'component'
B = R / 'artifacts/th14/low-pause-present-capture-nov09/cpp-component'
P = R / 'artifacts/th14/current-low-pause-transition-nov12/component'
C = R / 'artifacts/th14/control-main-stop-nov12/current-core'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
assert not H.exists(), 'Keep existing evidence'
assert load(P.parent / 'cpp-terminal-receipt.json')['reaped']
parent, core = load(P / 'build.json'), load(C / 'build.json')
for name, digest in parent['sourceBindingsByMode']['candidate'].items():
    assert sha(R / name) == digest, name
for name, digest in parent['objectBindings'].items():
    assert sha(R / name) == digest, name
prior = load(B / 'build.json')
assert sha(B / 'fixture.cpp') == prior['fixtureSha256']
O.mkdir(parents=True)
source = (B / 'fixture.cpp').read_text(encoding='utf8')
source += '\nAPI(async_deliver_owned) void async_deliver_owned(u32 callback,u32 data){th14_async_invoke(callback,data);}\n'
(O / 'fixture.cpp').write_text(source, encoding='utf8', newline='\n')
(O / 'Th14WarmAttractCase.hpp').write_bytes((P / 'Th14WarmAttractCase.hpp').read_bytes())
rt = R / 'runtimes/th12'
cc = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc) == core['compilerSha256']
flags = core['flags'] + ['-I' + str(rt / 'th12_web/cpp/sdl'), '-I' + str(rt / 'portable/sdl'),
    '-I' + str(R / 'artifacts/th14/boot-main-intake-nov07/application-component/include')]
command = [str(cc), *flags, '-fno-access-control', '-mexec-model=reactor',
    '-Wl,--no-entry', '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
    '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824',
    '-Wl,-z,stack-size=1048576', str(O / 'fixture.cpp'),
    *[str(R / p) for p in parent['objectBindings']], '-o', str(O / 'candidate.wasm')]
(O / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
with (O / 'compile.log').open('wb') as log:
    result = subprocess.run(command, cwd=R, env=dict(os.environ, TEMP=str(O), TMP=str(O), TMPDIR=str(O)),
        stdout=log, stderr=subprocess.STDOUT, timeout=240)
assert result.returncode == 0, (O / 'compile.log').read_text(errors='replace')[-6000:]
bindings = {p: h for p, h in parent['sourceBindingsByMode']['candidate'].items()
            if not p.startswith('artifacts/th14/current-low-pause-transition-nov12/')}
for p in [Path(__file__), O / 'fixture.cpp', O / 'Th14WarmAttractCase.hpp']:
    bindings[p.relative_to(R).as_posix()] = sha(p)
report = dict(compiled=True, actualColdApplicationInitializeTickAndDraw=True,
    noDeclaredPerFileReadinessSchedule=True, sourceBindingsByMode={'candidate': bindings},
    objectBindings=parent['objectBindings'], fixtureSha256=sha(O / 'fixture.cpp'),
    fixturePath=(O / 'fixture.cpp').relative_to(R).as_posix(),
    wasmSha256=sha(O / 'candidate.wasm'), outputs={'candidate': {'wasmSha256': sha(O / 'candidate.wasm')}},
    normalAccessFor145LinkedProviders=True, fixtureIncludesCurrentCanonicalApplicationWithRelaxedAccess=True,
    gameObjectsReusedAndReverified=141, hostObjectsReusedAndReverified=4,
    parentProviderBuildSha256=sha(P / 'build.json'), parentFixtureSha256=sha(B / 'fixture.cpp'),
    compilerSha256=sha(cc), productionGameSource='e6b15d27768ee4da293c81c3c239e3d42880020b',
    originalGameStarted=False, newAssetsCopied=False, productionChanged=False, completeGame=False)
(O / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(compiled=True, wasmSha256=report['wasmSha256'], providers=145)))
