"""Derive a bounded, independently declared Z=0 input matrix from the atlas oracle."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-atlas-raster-nov12'
H.mkdir(exist_ok=False)
source=R/'tools/th14-ascii-atlas-geometry-native-nov12.py';raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='fa5bab3d438b0cbe6fa655c3a563054e1655a5620a0318fbaedfc0340305b6a2'
s=raw.decode();changes={
"R=Path(__file__).resolve().parents[1]":"R=Path(__file__).resolve().parents[3]",
"H=R/'artifacts/th14/ascii-atlas-geometry-nov12';O=H/'native'":"H=R/'artifacts/th14/ascii-atlas-raster-nov12';O=H/'geometry'",
"itertools.product(range(6),[(1.,1.),(.7,.3)],[False,True],[0,1,2],[(1,1),(0,0),(2,2)])":"itertools.product([0,4],[(.7,.3)],[True],[0,1,2],[(1,1)])",
"position=[16.25,28.5,-.125]":"position=[16.25,28.5,0.]",
"phase='';rows=[];error=''":"phase='';rows=[];error='';viewport=[]",
"global bound_texture,fvf":"global bound_texture,fvf,viewport",
"if name=='SetRenderState':":"if name=='SetViewport':viewport=list(struct.unpack('<4I2f',m.mem_read(args[1],24)))\n elif name=='SetRenderState':",
"events.append(dict(topology=topology":"events.append(dict(viewport=list(viewport),topology=topology",
"   device_states.clear();device_states.update(":"   run(0x40be30,SUP,(0,)) # Empty original traversal establishes full camera before first request.\n   device_states.clear();device_states.update("
}
for old,new in changes.items():
    assert s.count(old)==1,old
    s=s.replace(old,new)
p=H/'native-geometry-tool.py';p.write_text(s,encoding='utf8')
(H/'declared-inputs.json').write_text(json.dumps(dict(cases=18,widths=[640,960,1280],fonts=[0,4],scale=[.7,.3],shadow=True,passes=[0,1,2],alignment=[1,1],firstRequestZ=0,geometryOracleParentSha256=hashlib.sha256(raw).hexdigest(),geometryOracleSha256=hashlib.sha256(p.read_bytes()).hexdigest(),noNativeStateFedToCpp=True,maximumRawPixelOutputBytes=60000000,newOriginalGameRuns=0,completeGame=False),indent=2)+'\n')
print(str(p))
