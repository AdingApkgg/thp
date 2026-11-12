"""Rebuild only the changed TH14 renderer and verify retained production inputs."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/helper-clear-oracle-nov13'
P = R / 'artifacts/th14/upstream-helper-integration-nov12'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
changed = 'runtimes/th12/portable/sdl/Renderer.cpp'
parent = load(P / 'browser-final/build.json')
for name, expected in parent['sourceBindings'].items():
    if name != changed:
        assert sha(R / name) == expected, name
assert sha(R / changed) == load(H / 'source-adoption.json')['afterSha256']
sdk = (R / 'runtimes/th12/tools/emsdk').resolve()
cc = sdk / 'upstream/emscripten/emcc.py'
O = H / 'production-browser'
O.mkdir(exist_ok=False)
(O / 'objects').mkdir()
env = {**os.environ, 'EM_CONFIG': str(sdk / '.emscripten'), 'EMSDK_PYTHON': sys.executable,
       'EMCC_CORES': '2', 'TEMP': str(O), 'TMP': str(O), 'TMPDIR': str(O)}

def run(command, directory, log, timeout=180):
    with log.open('wb') as stream:
        result = subprocess.run(command, cwd=directory, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(log.read_text()[-4000:])

objects = {}
flags = [f for f in parent['flags'] if f != '--profiling-funcs']
for name, expected in parent['objects'].items():
    old = P / 'browser-final' / name
    assert sha(old) == expected
    target = O / name
    if target.name == 'portable_sdl_Renderer.cpp.o':
        run([sys.executable, str(cc), *flags, '-c', str(R / changed), '-o', str(target)], R / 'runtimes/th12', O / 'renderer.log')
    else:
        os.link(old, target)
    objects[name] = sha(target)
link_flags = [str(R / 'runtimes/th12/portable/sdl/Th14WebGpuLibrary.js') if f == 'portable/sdl/Th14WebGpuLibrary.js' else f for f in parent['linkFlags']]
run([sys.executable, str(cc), *parent['flags'], *[str(O / n) for n in objects], *link_flags, '-o', str(O / 'th14-sdl.mjs')], R / 'runtimes/th12', O / 'link.log', 300)
profile = load(R / 'tools/th14-gles-profile.json')
for name in profile['helpers']:
    (O / name).write_bytes((R / 'runtimes/th12/portable/sdl' / name).read_bytes())
(O / 'eagler-host.mjs').write_bytes((R / 'runtimes/th12/th12_web/sdl-runtime/eagler-host.mjs').read_bytes())
files = {name: {'bytes': (O / name).stat().st_size, 'sha256': sha(O / name)} for name in ['th14-sdl.mjs', 'th14-sdl.wasm', 'eagler-host.mjs', *profile['helpers']]}
browser = {**parent, 'module': str(O / 'th14-sdl.wasm'), 'objects': objects,
           'sourceBindings': {name: sha(R / name) for name in parent['sourceBindings']},
           'runtimeFiles': files, 'sha256': sha(O / 'th14-sdl.wasm'), 'loaderSha256': sha(O / 'th14-sdl.mjs'),
           'freshlyCompiledUnits': 1, 'reusedVerifiedUnits': 145, 'sourceRoot': str(R), 'completeGame': False}
(O / 'build.json').write_text(json.dumps(browser, indent=2) + '\n')
print(json.dumps({'browserBuilt': True, 'wasmSha256': browser['sha256'], 'fresh': 1, 'verifiedReused': 145}), flush=True)

# The correction is under PORT_TITLE == 14. Check the three actual other-title
# renderer objects against the already qualified compiler/profile results.
L = H / 'legacy-control'
L.mkdir()
rows = []
for row in load(P / 'legacy-final/checked.json')['rows']:
    if row['source'] != changed:
        continue
    title = row['title']
    old = R / row['objects'][1]['object']
    assert sha(old) == row['objects'][1]['objectSha256']
    legacy_flags = [f for f in flags if not f.startswith('-DTH14')]
    legacy_flags = [f'-DPORT_TITLE={title}' if f == '-DPORT_TITLE=14' else f for f in legacy_flags]
    legacy_flags += ['-ffile-prefix-map=' + str(R) + '=/thp']
    target = L / f'{title}-Renderer.o'
    run([sys.executable, str(cc), *legacy_flags, '-c', str(R / changed), '-o', str(target)], R / 'runtimes/th12', L / f'{title}.log')
    rows.append({'title': title, 'expectedSha256': sha(old), 'actualSha256': sha(target), 'byteIdentical': sha(old) == sha(target)})
(L / 'report.json').write_text(json.dumps({'rows': rows, 'passed': len(rows) == 3 and all(row['byteIdentical'] for row in rows)}, indent=2) + '\n')
assert len(rows) == 3 and all(row['byteIdentical'] for row in rows)
print(json.dumps({'otherTitleRendererPairsByteIdentical': len(rows)}), flush=True)

# The ordinary-entry fixture and 144 unaffected normal providers are reused only
# after hashing every source/object. The new host Renderer shares its EM layout.
A = H / 'application/component'
A.mkdir(parents=True)
old_app = P / 'application-production/component'
app = load(old_app / 'build.json')
for name, expected in {**app['sourceBindingsByMode']['candidate'], **app['objectBindings']}.items():
    assert sha(R / name) == expected, name
provider = load(P / 'current-provider-bindings.json')
compiler = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(compiler) == provider['compilerSha256']
app_flags = provider['flags'] + ['-D__EMSCRIPTEN__=1', '-I' + str(P / 'final-source/runtimes/th12/th12_web/cpp/sdl'),
                                '-I' + str(R / 'runtimes/th12/portable/sdl'), '-I' + str(R / 'artifacts/th14/boot-main-intake-nov07/application-component/include')]
new_object = A / 'Renderer.cpp.o'
run([str(compiler), *app_flags, '-c', str(R / changed), '-o', str(new_object)], R, A / 'renderer.log')
app_objects = {n: d for n, d in app['objectBindings'].items() if Path(n).name != 'Renderer.cpp.o'}
assert len(app_objects) == 144
app_objects[new_object.relative_to(R).as_posix()] = sha(new_object)
for name in ['fixture.cpp', 'Th14WarmAttractCase.hpp']:
    (A / name).write_bytes((old_app / name).read_bytes())
run([str(compiler), *app_flags, '-fno-access-control', '-mexec-model=reactor', '-Wl,--no-entry', '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
     '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824', '-Wl,-z,stack-size=1048576', str(A / 'fixture.cpp'), *[str(R / n) for n in app_objects], '-o', str(A / 'candidate.wasm')], R, A / 'link.log')
bindings = {n: d for n, d in app['sourceBindingsByMode']['candidate'].items() if n != (P / 'final-source' / changed).relative_to(R).as_posix()}
bindings[changed] = sha(R / changed)
for name in ['fixture.cpp', 'Th14WarmAttractCase.hpp']:
    bindings[(A / name).relative_to(R).as_posix()] = sha(A / name)
new_app = {**app, 'sourceBindings': bindings, 'sourceBindingsByMode': {'candidate': bindings}, 'objectBindings': app_objects,
           'fixturePath': (A / 'fixture.cpp').relative_to(R).as_posix(), 'fixtureSha256': sha(A / 'fixture.cpp'),
           'wasmSha256': sha(A / 'candidate.wasm'), 'feedbackFixRendererSource': changed, 'normalProviders': 145, 'completeGame': False}
(A / 'build.json').write_text(json.dumps(new_app, indent=2) + '\n')
print(json.dumps({'applicationBuilt': True, 'wasmSha256': new_app['wasmSha256'], 'freshNormalHostUnits': 1, 'verifiedReusedProviders': 144}), flush=True)
