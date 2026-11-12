"""Incrementally build the TH14 initialization fix with verified browser objects."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13'
P = R / 'artifacts/th14/player-initialization-oracle-nov13/browser'
O = H / 'browser'
O.mkdir()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
parent = load(P / 'build.json')
edit = load(H / 'candidate-edits.json')
bindings = {name: sha(R / name) for name in parent['sourceBindings']}
assert {n for n in bindings if bindings[n] != parent['sourceBindings'][n]} == {edit['path']}
assert bindings[edit['path']] == edit['afterSha256']
profile = load(R / 'tools/th14-gles-profile.json')
assert profile['flags'] == parent['flags'] and '-fno-access-control' not in profile['flags']
sdk = R / 'tools/emsdk'
compiler = sdk / 'upstream/emscripten/emcc.py'
env = dict(os.environ, EMSDK=str(sdk), EMSDK_PYTHON=sys.executable,
           EMCC_CORES='1', EM_CONFIG=str(sdk / '.emscripten'))
compiler_version = subprocess.check_output([sys.executable, str(compiler), '--version'],
                                          cwd=R, env=env, timeout=30).decode('utf8')
objects = {}
changed = 0
with tempfile.TemporaryDirectory(dir=O, prefix='emsdk-') as temp:
    env.update(TMP=temp, TMPDIR=temp, TEMP=temp)
    for name, digest in parent['objects'].items():
        before, target = P / name, O / name
        assert sha(before) == digest, name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.name == 'th12_web_cpp_game_PlayerFrame.cpp.o':
            cmd = [sys.executable, str(compiler),
                   *[f for f in parent['flags'] if f != '--profiling-funcs'],
                   '-c', str(R / edit['path']), '-o', str(target)]
            with (O / 'compile.log').open('wb') as log:
                subprocess.run(cmd, cwd=R / 'runtimes/th12', env=env, stdout=log,
                               stderr=subprocess.STDOUT, check=True, timeout=180)
            changed += 1
        else:
            os.link(before, target)
        objects[name] = sha(target)
    assert len(objects) == 146 and changed == 1
    cmd = [sys.executable, str(compiler), *parent['flags'],
           *[str(O / name) for name in objects], *parent['linkFlags'],
           '-o', str(O / 'th14-sdl.mjs')]
    with (O / 'link.log').open('wb') as log:
        subprocess.run(cmd, cwd=R / 'runtimes/th12', env=env, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=240)
for name, row in parent['runtimeFiles'].items():
    assert sha(P / name) == row['sha256']
    if name not in ['th14-sdl.mjs', 'th14-sdl.wasm']:
        shutil.copyfile(P / name, O / name)
for name, digest in bindings.items():
    assert sha(R / name) == digest, name
files = {name: dict(bytes=(O / name).stat().st_size, sha256=sha(O / name))
         for name in parent['runtimeFiles']}
report = dict(parent, module=str(O / 'th14-sdl.wasm'), sourceBindings=bindings,
              objects=objects, runtimeFiles=files, sha256=files['th14-sdl.wasm']['sha256'],
              loaderSha256=files['th14-sdl.mjs']['sha256'], unitsRecompiled=1,
              objectsVerifiedReused=145, normalAccessControl=True,
              parentBuildSha256=sha(P / 'build.json'), sourceChanges=[edit],
              compilerScriptSha256=sha(compiler), compilerVersion=compiler_version,
              toolSha256=sha(Path(__file__)), deployed=False, completeGame=False)
(O / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['sha256', 'loaderSha256', 'unitsRecompiled',
                                      'objectsVerifiedReused', 'deployed']}))
