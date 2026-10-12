"""Extend the controlled clip readback to every vertex of the 21 selected draws."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay'
parent=ROOT/'tools/th14-stage-sampler-corners-native.py'
s=parent.read_text().replace("OUT=INPUT/'sampler-corners'","OUT=INPUT/'sampler-vertices'").replace("OUT=INPUT/'sampler-corners'","OUT=INPUT/'sampler-vertices'")
anchor="for c in cases:\n    for corner in range(4):expanded.append(dict(c,points=[[16,16]],corner=corner))"
assert anchor in s
s=s.replace(anchor,"""prepared=json.loads((INPUT/'prepared.json').read_bytes())
for c in cases:
    frame=next(f for f in prepared['frames'] if f['stage']==c['stage'] and f['frame']==c['frame'])
    draw=[d for d in frame['commands'] if d['kind']=='draw'][c['draw']]
    count=len(draw['words'])//(draw['stride']//4)
    assert count==draw['count']+2
    for corner in range(count):expanded.append(dict(c,points=[[16,16]],corner=corner))""")
s=s.replace("generated=ROOT/'tools/th14-stage-sampler-corners-hal.py'","generated=ROOT/'tools/th14-stage-sampler-vertices-hal.py'")
# The parent replacement targets its generated HAL output too.
s=s.replace("replace(\"OUT=INPUT/'sampler-matrix-float'\",\"OUT=INPUT/'sampler-vertices'\")","replace(\"OUT=INPUT/'sampler-matrix-float'\",\"OUT=INPUT/'sampler-vertices'\")")
assert "OUT=INPUT/'sampler-corners'" not in s
generated=ROOT/'tools/th14-stage-sampler-vertices-generator.py'
generated.write_text(s)
runpy.run_path(str(generated),run_name='__main__')
out=BASE/'sampler-vertices';g=json.loads((out/'generation.json').read_bytes())
g.update(wrapperSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),parentGeneratorSha256=hashlib.sha256(parent.read_bytes()).hexdigest(),scope='All submitted vertices in the 21 selected draws; independent constant-varying probe, not actual rasterized game geometry.')
(out/'generation.json').write_text(json.dumps(g,indent=2)+'\n')
