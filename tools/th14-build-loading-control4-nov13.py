"""Build the normal-access loading component with an explicit initial flag."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
parent = ROOT / 'tools/th14-build-loading-control-nov11.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest() == 'be2f2cb74da8cba56cd70625d3da81b022adf84d766d9330f0c3dde117ee32b5'
source = parent.read_text()
for old, new in {
    'API(begin) u32 begin(float rate){': 'API(begin) u32 begin(float rate,u32 initialFlags){',
    ' control.flags=0;a.th14_control.publish(control);': ' control.flags=initialFlags;a.th14_control.publish(control);',
}.items():
    assert source.count(old) == 1, old
    source = source.replace(old, new)
exec(compile(source, str(parent), 'exec'), globals())
