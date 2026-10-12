"""Create an independent current-source geometry recheck, preserving old evidence."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
out=ROOT/'artifacts/th14/gpu-original-quads/geometry'
out.mkdir(parents=True,exist_ok=True)
native=(ROOT/'tools/th14-render-native.py').read_text(encoding='utf-8-sig')
assert native.count("out=ROOT/'artifacts/th14/render-native.json'")==1
native=native.replace("out=ROOT/'artifacts/th14/render-native.json'","out=ROOT/'artifacts/th14/gpu-original-quads/geometry/native.json'")
(ROOT/'tools/th14-gpu-original-quads-geometry-native.py').write_text(native,encoding='utf8')
check=(ROOT/'tools/th14-render-check.mjs').read_text(encoding='utf-8-sig')
for old,new in [
 ('artifacts/th14/render-check','artifacts/th14/gpu-original-quads/geometry'),
 ('tools/th14-render-native.py','tools/th14-gpu-original-quads-geometry-native.py'),
 ('artifacts/th14/render-native.json','artifacts/th14/gpu-original-quads/geometry/native.json'),
 ('tools/th14-render-check.mjs','tools/th14-gpu-original-quads-geometry-check.mjs'),
 ('docs/porting/th14-render-verified.json','docs/porting/th14-gpu-original-quads-geometry-verified-oct11.json')]:
 assert old in check,old
 check=check.replace(old,new)
(ROOT/'tools/th14-gpu-original-quads-geometry-check.mjs').write_text(check,encoding='utf8')
print('Prepared independent current-source geometry oracle and checker')
