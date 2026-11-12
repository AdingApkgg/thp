"""Adapt the pinned offline auditors to the current 35k callback prefix."""
from pathlib import Path
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/option-refresh-oracle-nov13/current-replay'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_bytes())
build = load(H / 'component/build.json')
assert build['normalAccessFor145LinkedProviders']
for name, digest in {**build['sourceBindingsByMode']['candidate'], **build['objectBindings']}.items():
    assert sha(R / name) == digest, name
assert sha(H / 'component/candidate.wasm') == build['wasmSha256']
parent = R / 'tools/th14-audit-current-low-pause-transition-nov12.py'
source = parent.read_text()
changes = {
    "H = R / 'artifacts/th14/current-low-pause-transition-nov12'":
        "H = R / 'artifacts/th14/option-refresh-oracle-nov13/current-replay'",
    "assert 16400 <= cr['callbacks'] < 16500": "assert 35000 <= cr['callbacks'] < 35010",
    "'f49a6034b8f63ac9a1a882d724159dd93093a94ca2769dd3f2cd592a513c1cb4'":
        repr(build['wasmSha256']),
    "targets = {tuple(k) for k in build['targetInputKeys'] if k[0]==1 or (k[0]==2 and k[2]<=2146)}":
        "targets = {tuple(k) for k in build['targetInputKeys']}",
    "currentGameSource='e6b15d27768ee4da293c81c3c239e3d42880020b',":
        "currentGameSource=None,currentGameSourceBase='b8e36ef27d96238352f5edaf9b368ca23394ceb3',localSourceChanges=build['localSourceChanges'],",
}
for old, new in changes.items():
    assert source.count(old) == 1, old
    source = source.replace(old, new)
anchor = "assert all(x['result'] == 1 for x in platform['gpuContextCleanup'])"
assert source.count(anchor) == 1
source = source.replace(anchor, anchor + '''
delivery = platform['productionDelivery']
assert not delivery['activeRestore'] and not delivery['activeScene']
assert all(w['exited'] and not w['error'] for w in delivery['workers'])
''')
path = R / 'tools/th14-audit-option-current-replay-nov13.py'
assert not path.exists()
path.write_text(source, encoding='utf8', newline='\n')
vm_parent = R / 'tools/th14-audit-current-low-pause-shot-vm303-nov12.py'
vm = vm_parent.read_text()
vm_changes = {
    "H = R / 'artifacts/th14/current-low-pause-transition-nov12'":
        "H = R / 'artifacts/th14/option-refresh-oracle-nov13/current-replay'",
    "currentGameSource='e6b15d27768ee4da293c81c3c239e3d42880020b',":
        "currentGameSource=None,currentGameSourceBase=q['currentGameSourceBase'],localSourceChanges=q['localSourceChanges'],",
}
for old, new in vm_changes.items():
    assert vm.count(old) == 1, old
    vm = vm.replace(old, new)
vm_path = R / 'tools/th14-audit-option-current-replay-vm303-nov13.py'
assert not vm_path.exists()
vm_path.write_text(vm, encoding='utf8', newline='\n')
receipt = dict(setupBindingsVerified=True, currentLocalSourceVerified=True,
               wasmSha256=build['wasmSha256'], callbackLimit=35000,
               parentAuditSha256=sha(parent), auditorSha256=sha(path),
               parentVmAuditSha256=sha(vm_parent), vmAuditorSha256=sha(vm_path),
               completeGame=False)
(H / 'host-preflight.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
