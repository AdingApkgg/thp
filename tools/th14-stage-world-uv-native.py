"""Authored pixel shader reads FFP interpolated UV for two recorded world quads."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'world-uv';OUT.mkdir(exist_ok=True)
base=ROOT/'tools/th14-stage-gpu-stream-hal.py';s=base.read_text().replace("OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay'","INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'world-uv'")
s=s.replace("(OUT/'prepared.json')","(INPUT/'prepared.json')").replace("(OUT/n['file'])","(INPUT/n['file'])")
s=s.replace("'IDirect3DTexture9'):","'IDirect3DTexture9','IDirect3DPixelShader9'):")
s=s.replace('readback=P();textures={}', 'readback=P();pixel_shader=P();textures={}')
s=s.replace('[640,480,21,0,0,0,C.byref(rt),None]','[640,480,116,0,0,0,C.byref(rt),None]').replace('[640,480,21,2,C.byref(readback),None]','[640,480,116,2,C.byref(readback),None]')
anchor='        lock=t.Lock()';assert s.count(anchor)==1
s=s.replace(anchor,'''
        shader_source=b'ps_2_0\\ndcl t0.xy\\ndcl_2d s0\\ndef c0,0,1,0,1\\ntexld r1,t0,s0\\nmov r0.xy,t0\\nmov r0.zw,c0\\nmov oC0,r0\\n'
        (OUT/'probe.asm').write_bytes(shader_source)
        compiler=C.WinDLL('d3dcompiler_47');compiler.D3DAssemble.argtypes=[P,C.c_size_t,C.c_char_p,P,P,U,C.POINTER(P),C.POINTER(P)];compiler.D3DAssemble.restype=I
        blob=P();errors=P();source=C.create_string_buffer(shader_source)
        def blob_method(obj,index,result,*sig):return C.WINFUNCTYPE(result,P,*sig)(C.cast(obj,C.POINTER(C.POINTER(P))).contents[index])
        try:
            hr=compiler.D3DAssemble(source,len(shader_source),b'world-uv-probe.asm',None,None,0,C.byref(blob),C.byref(errors))
            if hr<0:raise RuntimeError(C.string_at(blob_method(errors,3,P)(errors),blob_method(errors,4,C.c_size_t)(errors)).decode())
            code=C.string_at(blob_method(blob,3,P)(blob),blob_method(blob,4,C.c_size_t)(blob));(OUT/'probe.pso').write_bytes(code);buffer=C.create_string_buffer(code)
            call(device,'IDirect3DDevice9','CreatePixelShader',[P,C.POINTER(P)],[buffer,C.byref(pixel_shader)])
        finally:
            for obj in (errors,blob):
                if obj.value:blob_method(obj,2,U)(obj)
'''+anchor)
anchor="        for frame in prepared['frames']:\n";assert s.count(anchor)==1
s=s.replace(anchor,anchor+"            selected_draw={(3,599):68,(3,1199):45}.get((frame['stage'],frame['frame']))\n            if selected_draw is None:continue\n")
s=s.replace("[0,None,3,0xff42678b,1,0]","[0,None,3,0,1,0]")
anchor="            for c in frame['commands']:execute(c)\n";assert s.count(anchor)==1
s=s.replace(anchor,'''
            draw_index=0
            for c in frame['commands']:
                if c['kind']=='draw':
                    if draw_index==selected_draw:
                        for k,v in ((7,0),(14,0),(15,0),(27,0),(28,0)):rs(k,v)
                        call(device,'IDirect3DDevice9','SetPixelShader',[P],[pixel_shader]);execute(c)
                    draw_index+=1
                elif c['kind']=='clear':execute(dict(c,color=0))
                else:execute(c)
''')
s=s.replace('640*4) for y','640*16) for y').replace("directDraws=frame['directDraws']","directDraws=1,originalDrawIndex=selected_draw")
s=s.replace("(OUT/'native.bgra')","(OUT/'native.rgba32f')").replace("width=640,height=480,frames=frames","width=640,height=480,format=116,bytesPerPixel=16,frames=frames")
s=s.replace("scope=prepared['scope']","scope='Two captured world quads, FFP vertices and original matrices. Authored ps2 shader outputs interpolated UV and coverage alpha1 to RGBA32F, clears all other pixels to zero. Depth/alpha/blend/fog disabled, other draws excluded. This is an independent varying probe, not original game rendering.'")
anchor="    finally:\n        for texture";assert s.count(anchor)==1
s=s.replace(anchor,"    finally:\n        if pixel_shader.value:method(pixel_shader,'IDirect3DPixelShader9','Release',[])(pixel_shader)\n        for texture")
generated=ROOT/'tools/th14-stage-world-uv-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();(OUT/'generation.json').write_text(json.dumps(dict(generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),shaderSha256=sha((OUT/'probe.pso').read_bytes()),assemblySha256=sha((OUT/'probe.asm').read_bytes()),compilerSha256=sha(Path('C:/Windows/System32/d3dcompiler_47.dll').read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes())),indent=2)+'\n')
