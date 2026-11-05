"""Apply unchanged actual-read gates to the declared read-only slot observer."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
parent=R/'tools/th14-supervisor-rng-read-evidence-nov05.py';raw=parent.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='51579ba130141877818c5bceea565bed968d806b06a98ddfece5e70b12f7ab85'
prep=json.loads((R/'artifacts/th14/shot-lifetime-native-nov05/observer-slots-v2/prepared.json').read_bytes())
assert prep['criticalMutationCallAstUnchanged'] and prep['hardwareWatchProfileUnchanged']
assert not prep['additionalGameMemoryWrites'] and not prep['additionalSuspendsOrResumes']
source=raw.decode();before='artifacts/th14/supervisor-pass-rng-nov05/observer-fixed-target/prepared.json'
assert source.count(before)==1
source=source.replace(before,'artifacts/th14/shot-lifetime-native-nov05/observer-slots-v2/prepared.json')
exec(compile(source,str(__file__),'exec'),dict(__name__='__main__',__file__=str(__file__)))
