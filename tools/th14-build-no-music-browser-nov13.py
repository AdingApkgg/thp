"""Rebuild the normal browser AudioDevice unit for the no-BGM fix."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

R = Path(__file__).resolve().parents[1]
P = R / 'artifacts/th14/native-viewer-application-nov13/browser-v2'
O = R / 'artifacts/th14/no-music-startup-nov13/browser'
O.mkdir(exist_ok=True)
assert not any(p.is_file() for p in O.rglob('*')), 'Do not restart an existing browser build'
OBJECT_PROVIDER = P.parent / 'browser'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
parent = json.loads((P / 'build.json').read_bytes())
bindings = {n: sha(R / n) for n in parent['sourceBindings']}
changed = {n for n, v in bindings.items() if v != parent['sourceBindings'][n]}
assert changed == {'runtimes/th12/th12_web/cpp/sdl/AudioDevice.cpp',
                   'tools/th14-build-gles.py', 'tools/th14-gles-profile.json'}, changed
profile = json.loads((R / 'tools/th14-gles-profile.json').read_bytes())
assert profile['flags'] == parent['flags']
sdk = R / 'tools/emsdk'
cc = sdk / 'upstream/emscripten/emcc.py'
env = {**os.environ, 'EMSDK': str(sdk), 'EMSDK_PYTHON': sys.executable,
       'EMCC_CORES': '1', 'EM_CONFIG': str(sdk / '.emscripten')}
objects, rebuilt = {}, []
link = [str(R / 'runtimes/th12/portable/sdl/Th14WebGpuLibrary.js')
        if f == 'portable/sdl/Th14WebGpuLibrary.js' else f for f in profile['linkFlags']]
with tempfile.TemporaryDirectory(dir=O, prefix='emsdk-') as temp:
    env.update(TEMP=temp, TMP=temp, TMPDIR=temp)
    for name, digest in parent['objects'].items():
        src, dst = OBJECT_PROVIDER / name, O / name
        assert sha(src) == digest, name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if Path(name).name == 'th12_web_cpp_sdl_AudioDevice.cpp.o':
            source = R / 'runtimes/th12/th12_web/cpp/sdl/AudioDevice.cpp'
            cmd = [sys.executable, str(cc), *[f for f in parent['flags'] if f != '--profiling-funcs'],
                   '-c', str(source), '-o', str(dst)]
            (O / 'audio-command.json').write_text(json.dumps(cmd, indent=2) + '\n')
            with (O / 'audio-build.log').open('wb') as log:
                result = subprocess.run(cmd, cwd=R / 'runtimes/th12', env=env,
                                        stdout=log, stderr=subprocess.STDOUT, timeout=180)
            assert result.returncode == 0, (O / 'audio-build.log').read_text(errors='replace')[-2500:]
            rebuilt.append(source.relative_to(R).as_posix())
        else:
            os.link(src, dst)
        objects[name] = sha(dst)
    assert len(objects) == 146 and len(rebuilt) == 1
    args = [*parent['flags'], *[str(O / n) for n in objects], *link, '-o', str(O / 'th14-sdl.mjs')]
    response = Path(temp) / 'link.rsp'
    response.write_text('\n'.join(json.dumps(x.replace('\\', '/')) for x in args), encoding='utf8')
    (O / 'link-arguments.json').write_text(json.dumps(args, indent=2) + '\n')
    with (O / 'link.log').open('wb') as log:
        result = subprocess.run([sys.executable, str(cc), '@' + str(response)], cwd=R / 'runtimes/th12',
                                env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240)
    assert result.returncode == 0, (O / 'link.log').read_text(errors='replace')[-2500:]
for name, row in parent['runtimeFiles'].items():
    assert sha(P / name) == row['sha256']
    if name not in ['th14-sdl.mjs', 'th14-sdl.wasm', 'shell.mjs']:
        shutil.copyfile(P / name, O / name)
spec = importlib.util.spec_from_file_location('normal_th14_builder', R / 'tools/th14-build-gles.py')
normal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normal)
wasm_hash = sha(O / 'th14-sdl.wasm')
shell_name = 'runtimes/th12/th12_web/sdl-runtime/shell.mjs'
(O / 'shell.mjs').write_text(normal.prepare_host_shell((R / shell_name).read_text(encoding='utf8'),
    dict(version='1.00b-thp-' + wasm_hash[:12], completeGame=False, nativeEquivalent=False, sha256=wasm_hash)),
    encoding='utf8', newline='\n')
bindings[shell_name] = sha(R / shell_name)
bindings[Path(__file__).relative_to(R).as_posix()] = sha(Path(__file__))
for name, digest in bindings.items():
    assert sha(R / name) == digest, name
files = {n: dict(bytes=(O / n).stat().st_size, sha256=sha(O / n)) for n in parent['runtimeFiles']}
j = dict(parent, module=str(O / 'th14-sdl.wasm'), sourceBindings=bindings, objects=objects,
         flags=profile['flags'], linkFlags=link, runtimeFiles=files, sha256=wasm_hash,
         loaderSha256=files['th14-sdl.mjs']['sha256'], unitsRecompiled=1, objectsVerifiedReused=145,
         sourceChanges=sorted(changed), normalAccessControl=True, browserUiAccepted=False,
         deployed=False, completeGame=False)
(O / 'build.json').write_text(json.dumps(j, indent=2) + '\n')
print(json.dumps({k: j[k] for k in ['sha256', 'loaderSha256', 'unitsRecompiled', 'objectsVerifiedReused']}))
