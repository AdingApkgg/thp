"""Reuse the bounded quiet lifecycle runner for the shot/VM snapshot profile."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/shot-lifetime-native-nov05'
prepared=json.loads((H/'observer-slots-v2/prepared.json').read_bytes())
component=json.loads((H/'lookup-component.json').read_bytes())
module=R/'tools/th14-shot-lifetime-readonly-nov05.py'
assert prepared['moduleSha256']==component['moduleSha256']==hashlib.sha256(module.read_bytes()).hexdigest()
assert component['passed'] and component['componentCases']==29
context_check=json.loads((H/'context-noop-component/report.json').read_bytes())
assert context_check['passed'] and context_check['fullInstallCases']==16
assert context_check['sourceSha256']==prepared['observerSha256']
if 'prefix' in sys.argv:
    assert json.loads((H/'preflight-slots-v2/verified.json').read_bytes())['nativeShotSnapshotsVerified']
parent=R/'tools/th14-run-player-pump-observer-nov05.py';raw=parent.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='bbc8748f71754ba2226ece2ac68c723178f9f3a338621ab34afb0ed505906a15'
source=raw.decode()
for before,after in [("H=R/'artifacts/th14/script-rng-read-generation-nov05'","H=R/'artifacts/th14/shot-lifetime-native-nov05'"),
    ("choices=['player-pump'],default='player-pump'","choices=['slots-v2'],default='slots-v2'")]:
    assert source.count(before)==1;source=source.replace(before,after)
exec(compile(source,str(__file__),'exec'),dict(__name__='__main__',__file__=str(__file__)))
