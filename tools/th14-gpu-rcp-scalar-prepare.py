"""Generate independent RCP scalar probes; no pixel-specific adjustment."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
helper=(ROOT/'tools/th14-native-fog-shader.py').read_text(encoding='utf8')
helper=once(helper,"MODE=sys.argv[1] if len(sys.argv)>1 else 'rsq-rcp-mad'","MODE='rcp-scalar'")
helper=once(helper,"assert MODE in (","assert MODE=='rcp-scalar' or MODE in (")
start=helper.index("    code='''");end=helper.index("    (out/'probe.asm')",start)
helper=helper[:start]+'''    code="""vs_2_0
dcl_position v0
dcl_color v1
dcl_texcoord v2
m4x4 r0, v0, c0
m4x4 r4, r0, c4
m4x4 oPos, r4, c8
mov oD0, v1
mov oT0, v2
rcp oFog, c14.x
"""
'''+helper[end:]
(ROOT/'tools/th14-native-rcp-scalar-shader.py').write_text(helper,encoding='utf8')
s=(ROOT/'tools/th14-gpu-native-shader-probe.py').read_text(encoding='utf8')
s=once(s,'import_module("th14-native-fog-shader")','import_module("th14-native-rcp-scalar-shader")')
s=once(s,'for profile,world,view,projection,texture_transform,fog,range_fog,point in itertools.product((11,14,21),range(3),range(2),range(2),range(2),(0,3),range(2),range(2)):','for profile,world,view,projection,texture_transform,fog,range_fog,point,scalar_index in itertools.product((11,),(0,),(0,),(0,),(0,),(3,),(1,),(1,),range(1025)):')
anchor="call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[0,C.byref(uniforms),13])"
s=once(s,anchor,anchor+"\n            scalar=struct.unpack('<f',struct.pack('<I',0x3f800000+scalar_index*8192))[0];scalar_uniform=(F*4)(scalar,0,0,0);call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[14,C.byref(scalar_uniform),1])")
s=once(s,'cases.append(dict(profile=profile,','cases.append(dict(scalarIndex=scalar_index,scalar=scalar,profile=profile,')
(ROOT/'tools/th14-gpu-rcp-scalar-native.py').write_text(s,encoding='utf8')
print('Prepared 1025 independent RCP scalar inputs in [1,2]')
