"""Execute retail geometry/material on retained background VM input.

The existing retail quad oracle declares D3D, batch flush/enqueue and cookie
services. This fixture reuses its initialization, without its synthetic sweep.
The retained VM is supplied only to the reference interpreter, never the game.
"""
from pathlib import Path
import ast, hashlib, json, struct, sys

R = Path(__file__).resolve().parents[1]
O = R / 'artifacts/th14/background-draw-contract-v2-nov13'
assert not O.exists()
O.mkdir()
sys.path.insert(0, str(R / 'tools'))
helper = R / 'tools/th14-gpu-original-quads-geometry-native.py'
tree = ast.parse(helper.read_text(encoding='utf8'))
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
cut = next(i for i, n in enumerate(main.body) if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == 'quads' for t in n.targets))
bootstrap = ast.Module(body=[n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign))]
                       + main.body[:cut], type_ignores=[])
scope = dict(__file__=str(helper), __name__='background_contract')
exec(compile(ast.fix_missing_locations(bootstrap), str(helper), 'exec'), scope)
m, put, get, run = [scope[n] for n in ('m', 'put', 'get', 'run')]
VM, SPRITE, MANAGER = [scope[n] for n in ('VM', 'SPRITE', 'MANAGER')]
source = R / 'artifacts/th14/current-startup-prefix-nov10/native/transition-before-readback.json'
raw = bytes.fromhex(json.loads(source.read_bytes())['geometryHex'])[4*0x5cc:5*0x5cc]
assert len(raw) == 0x5cc
assert struct.unpack_from('<I', raw, 0x594)[0] == 0
phases_path = R / 'artifacts/th14/compositor-filter-nov13/background-uv-phase-qualified.json'
phases = json.loads(phases_path.read_bytes())
inputs = [('native', struct.unpack_from('<I', raw, 0x88)[0])]
inputs += [(x['name'], x['inputUvWords'][0]) for x in phases['rows']]
rows = []
for name, bits in inputs:
    # Clear manager/device cache using the shared oracle setup, then restore the
    # measured VM. The sprite service identity is relocated to mapped storage.
    scope['setup'](0, 0, 0, 0, 0, 0)
    # Camera offset is a declared input, not recovered from the VM snapshot.
    scope['floats'](MANAGER + 0xd0, [0, 0])
    m.mem_write(VM, raw)
    put(VM + 0x2c, SPRITE)
    put(VM + 0x88, bits)
    put(VM + 0x8c, bits)
    scope['events'].clear()
    scope['draws'].clear()
    run(0x478f60, (VM,))
    rows.append(dict(name=name, uvWord=bits, draws=list(scope['draws']),
                     events=list(scope['events']), status=m.reg_read(scope['UC_X86_REG_EAX'])))
report = dict(rows=rows, actualRetailDrawDispatcher=True,
              controlledCameraOffset=[0, 0], controlledCameraViewport=[0, 0, 640, 480],
              declaredServices=['D3D device', 'batch enqueue/flush', 'cookie', 'relocated sprite texture identity'],
              retainedVmOnlyInReference=True, actualGameOrProductionRendererAccepted=False,
              bindings={str(p.relative_to(R)).replace('\\', '/'):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (helper, source, phases_path, Path(__file__))},
              completeGame=False)
(O / 'result.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
