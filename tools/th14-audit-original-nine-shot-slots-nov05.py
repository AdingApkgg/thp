"""Apply the unchanged actual native slot/VM/quad checks to alternate profile A."""
from pathlib import Path
import hashlib

R = Path(__file__).resolve().parents[1]
parent = R / 'tools/th14-audit-native-shot-slots-nov05.py'
raw = parent.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '835473ad56cd297b1ccdeedab981d349735aa86b0e00a96ed1474c5d742b9c5a'
source = raw.decode()
before = "H=R/'artifacts/th14/shot-lifetime-native-nov05'"
after = "H=R/'artifacts/th14/original-nine-shot-native-nov05'"
assert source.count(before) == 1
source = source.replace(before, after)
assert source.replace(after, before).encode() == raw
# This capture's ordinary atomic delivery failed. Only the separately verified
# natural-overlap logical diagnostic has a passing model to compare to native.
assert source.count('comparison-on') == 2
source = source.replace('comparison-on', 'overlap-on')
exec(compile(source, str(__file__), 'exec'),
     dict(__file__=str(Path(__file__).resolve()), __name__='__main__'))
