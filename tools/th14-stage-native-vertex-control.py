"""Replace world FFP vertex processing with authored float WVP VS2, fog off."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=BASE/'native-vertex-control';OUT.mkdir(exist_ok=True)
parent=ROOT/'tools/th14-stage-gpu-stream-hal.py';s=parent.read_text().replace("OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay'","INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'native-vertex-control'").replace("(OUT/'prepared.json').read_bytes()","(INPUT/'prepared.json').read_bytes()").replace("(OUT/n['file']).read_bytes()","(INPUT/n['file']).read_bytes()")
s=s.replace("'IDirect3DTexture9'):","'IDirect3DTexture9','IDirect3DVertexShader9'):")
s=s.replace("frames=[]\n", "frames=[];vertex_shaders={};matrices={};layout=0x102;uv_transform=True\n",1)
anchor='        lock=t.Lock()';assert anchor in s
s=s.replace(anchor,'''
        compiler=C.WinDLL('d3dcompiler_47');compiler.D3DAssemble.argtypes=[P,C.c_size_t,C.c_char_p,P,P,U,C.POINTER(P),C.POINTER(P)];compiler.D3DAssemble.restype=I
        def blob_method(obj,index,result,*sig):return C.WINFUNCTYPE(result,P,*sig)(C.cast(obj,C.POINTER(C.POINTER(P))).contents[index])
        for colored in (False,True):
            source_text='vs_2_0\\ndcl_position v0\\ndcl_texcoord v1\\n'+('dcl_color v2\\n' if colored else '')+'m4x4 oPos,v0,c0\\nmov r0,v1\\nmov r0.zw,c8\\nm4x4 oT0,r0,c4\\n'+('mov oD0,v2\\n' if colored else 'mov oD0,c9\\n')+'mov oD1,c10\\n'
            source=source_text.encode();(OUT/('colored.vs.asm' if colored else 'plain.vs.asm')).write_bytes(source);buffer=C.create_string_buffer(source);blob=P();errors=P()
            try:
                hr=compiler.D3DAssemble(buffer,len(source),b'world-vertex-control.asm',None,None,0,C.byref(blob),C.byref(errors))
                if hr<0:raise RuntimeError(C.string_at(blob_method(errors,3,P)(errors),blob_method(errors,4,C.c_size_t)(errors)).decode())
                code=C.string_at(blob_method(blob,3,P)(blob),blob_method(blob,4,C.c_size_t)(blob));(OUT/('colored.vso' if colored else 'plain.vso')).write_bytes(code);compiled=C.create_string_buffer(code);shader=P();call(device,'IDirect3DDevice9','CreateVertexShader',[P,C.POINTER(P)],[compiled,C.byref(shader)]);vertex_shaders[colored]=shader
            finally:
                for obj in (blob,errors):
                    if obj.value:blob_method(obj,2,U)(obj)
'''+anchor)
anchor='        def execute(c):\n';assert anchor in s
s=s.replace(anchor,'''
        f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
        def multiply(a,b):
            out=[]
            for col in range(4):
                for row in range(4):
                    v=f32(a[row]*b[col*4])
                    for k in range(1,4):v=f32(v+f32(a[k*4+row]*b[col*4+k]))
                    out.append(v)
            return out
'''+anchor+'            nonlocal layout,uv_transform\n')
s=s.replace("elif kind=='fvf':call(device,'IDirect3DDevice9','SetFVF',[U],[c['value']])","elif kind=='fvf':\n                layout=c['value'];call(device,'IDirect3DDevice9','SetFVF',[U],[layout])")
s=s.replace("elif kind=='textureStageState':ts(c['stage'],c['key'],c['value'])","elif kind=='textureStageState':\n                if c['stage']==0 and c['key']==24:uv_transform=c['value']!=0\n                ts(c['stage'],c['key'],c['value'])")
s=s.replace("elif kind=='transform':\n", "elif kind=='transform':\n                matrices[c['key']]=[struct.unpack('<f',struct.pack('<I',w))[0] for w in c['words']]\n")
anchor="            elif kind=='draw':\n";assert anchor in s
s=s.replace(anchor,anchor+'''
                rs(28,0)
                if layout in (0x102,0x142):
                    combined=multiply(matrices[3],multiply(matrices[2],matrices[256]));texture=matrices[16] if uv_transform else [float(i%5==0) for i in range(16)]
                    constants=(F*44)(*(combined[col*4+row] for row in range(4) for col in range(4)),*(texture[col*4+row] for row in range(4) for col in range(4)),1,0,1,0,1,1,1,1,0,0,0,0)
                    call(device,'IDirect3DDevice9','SetVertexShader',[P],[vertex_shaders[layout==0x142]]);call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[0,C.byref(constants),11])
                else:call(device,'IDirect3DDevice9','SetVertexShader',[P],[None])
''')
anchor="        for frame in prepared['frames']:\n";assert anchor in s
s=s.replace(anchor,anchor+"            matrices={k:[float(i%5==0) for i in range(16)] for k in (256,2,3,16)};layout=0x102;uv_transform=True\n")
s=s.replace('    finally:\n        for texture',"    finally:\n        for shader in vertex_shaders.values():\n            if shader.value:method(shader,'IDirect3DVertexShader9','Release',[])(shader)\n        for texture")
generated=ROOT/'tools/th14-stage-native-vertex-control-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();n=json.loads((OUT/'native.json').read_bytes());pixels=(OUT/'native.bgra').read_bytes();reference=(BASE/'variants/no-fog/native.bgra').read_bytes();assert len(pixels)==len(reference)==21*640*480*4
different=sum(a!=b for a,b in zip(pixels,reference));maximum=max(abs(a-b) for a,b in zip(pixels,reference));exact=sum(pixels[i:i+640*480*4]==reference[i:i+640*480*4] for i in range(0,len(pixels),640*480*4))
(OUT/'generation.json').write_text(json.dumps(dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(parent.read_bytes()),halSourceSha256=sha(generated.read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),pixelsSha256=sha(pixels),referencePixelsSha256=sha(reference),differentChannels=different,maxDelta=maximum,exactFrames=exact,scope='Controlled authored vs2 float P*(V*W), original UV matrix and diffuse output for all world draws; screen draws retain FFP. Both this run and the independent reference force fog off. Full color frames saved; no original pixel shader recovery or complete game claim.'),indent=2)+'\n');print(json.dumps(dict(exactFrames=exact,differentChannels=different,maxDelta=maximum)))
