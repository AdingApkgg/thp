"""Build the single changed TH14 provider against the verified ordinary fixture."""
from pathlib import Path
import hashlib, json, os, subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/beam-length-guard-nov14'
B = R / 'artifacts/th14/ordinary-difficulties-nov14/canonical-component'
O = H / 'component'
O.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
change = json.loads((H / 'source-change.json').read_bytes())
j = json.loads((B / 'build.json').read_bytes())
bindings = j['sourceBindingsByMode']['candidate']
assert bindings[change['source']] == change['beforeSha256']
assert sha(H / 'ShotCallbacksTh14-before.cpp') == change['beforeSha256']
for name, digest in {**bindings, **j['objectBindings']}.items():
    assert sha(R / name) == (change['afterSha256'] if name == change['source'] else digest), name
command = json.loads((B / 'command.json').read_bytes())
fixture = R / 'runtimes/th12/th12_web/tests/cpp/th14-ordinary-campaign-flow-fixture.cpp'
prefix = command[:command.index(str(fixture))]
prefix = [x for x in prefix if not x.startswith('-Wl,') and x not in ('-mexec-model=reactor', '-fno-access-control')]
obj = O / 'ShotCallbacksTh14.cpp.o'
compile_command = prefix + ['-c', str(R / change['source']), '-o', str(obj)]
(O / 'compile-command.json').write_text(json.dumps(compile_command, indent=2) + '\n')
env = dict(os.environ, TEMP=str(O), TMP=str(O))
with (O / 'compile.log').open('wb') as log:
    result = subprocess.run(compile_command, stdout=log, stderr=subprocess.STDOUT, env=env)
assert result.returncode == 0, (O / 'compile.log').read_text(errors='replace')[-2500:]
old_object = next(n for n in j['objectBindings'] if n.endswith('/ShotCallbacksTh14.cpp.o'))
command = [str(obj) if x == str(R / old_object) else str(O / 'candidate.wasm')
           if x == str(B / 'candidate.wasm') else x for x in command]
with (O / 'build.log').open('wb') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env)
assert result.returncode == 0, (O / 'build.log').read_text(errors='replace')[-2500:]
objects = dict(j['objectBindings'])
del objects[old_object]
objects[obj.relative_to(R).as_posix()] = sha(obj)
bindings[change['source']] = change['afterSha256']
j.update(sourceBindingsByMode={'candidate': bindings}, objectBindings=objects,
         outputs={'candidate': {'wasmSha256': sha(O / 'candidate.wasm')}},
         sourceChanges=[change], recompiledGameProviders=1, reusedProviderObjects=144,
         productionGameCodeChanged=True, deployed=False)
(O / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
(O / 'build.json').write_text(json.dumps(j, indent=2) + '\n')
print(json.dumps(j['outputs']))
