"""Generate a reviewable hardware instruction probe from the flat fixture."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
s=(ROOT/'tools/th14-gpu-stage-flat-probe-native.py').read_text(encoding='utf8')
s=once(s,'import importlib.util,','import importlib\nshader_probe=importlib.import_module("th14-native-fog-shader")\nimport importlib.util,')
s=once(s,"OUT=ROOT/'artifacts/th14/gpu-stage-flat-probe'","OUT=ROOT/'artifacts/th14/gpu-native-shader-probe'/shader_probe.MODE")
s=once(s,"'IDirect3DTexture9'):","'IDirect3DTexture9','IDirect3DVertexShader9'):")
s=once(s,'texture=P();window=None','texture=P();customshader=P();window=None')
anchor="call(device,'IDirect3DDevice9','SetFVF',[U],[0x142]);"
s=once(s,anchor,anchor+'bytecode=shader_probe.shader();shaderbuffer=C.create_string_buffer(bytecode);call(device,"IDirect3DDevice9","CreateVertexShader",[P,C.POINTER(P)],[shaderbuffer,C.byref(customshader)]);call(device,"IDirect3DDevice9","SetVertexShader",[P],[customshader]);')
anchor='stage(4,4);stage(24,2 if texture_transform else 0);'
code='''constant=[]
            for matrix in (scaledworlds[world],scaledviews[view],scaledprojections[projection]):constant.extend(matrix[row*4+col] for col in range(4) for row in range(4))
            inv=f32(1/f32(far-near));end=f32(far/f32(far-near)) if shader_probe.MODE=='rsq-rcp-divide-end' else f32(far*inv);constant.extend((-inv,end,far,inv))
            uniforms=(F*len(constant))(*constant);call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[0,C.byref(uniforms),13])
            '''
s=once(s,anchor,code+anchor)
s=once(s,'for p in (BASE,Path(__file__))','for p in (BASE,Path(__file__),Path(shader_probe.__file__))')
s=once(s,'report=dict(generated=True,','report=dict(generated=True,diagnosticMode=shader_probe.MODE,shaderSha256=sha(bytecode),shaderAssemblySha256=sha((OUT/"probe.asm").read_bytes()),')
s=once(s,"for obj,interface in ((texture,'IDirect3DTexture9')","for obj,interface in ((customshader,'IDirect3DVertexShader9'),(texture,'IDirect3DTexture9')")
s=s.replace('Separate hidden device; not native game draw-loop capture.','Locally authored vertex shader arithmetic probe; fixed-function alpha UV transformation is bypassed, only RGB fog arithmetic is being probed. Separate hidden device; not native game draw-loop capture.')
(ROOT/'tools/th14-gpu-native-shader-probe.py').write_text(s,encoding='utf8')
print('Prepared locally authored shader instruction probes')
