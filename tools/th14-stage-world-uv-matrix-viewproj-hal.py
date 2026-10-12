"""Replay recorded retail Stage direct draws on an independent hidden D3D9 HAL."""
import importlib.util,json,hashlib,struct,ctypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'world-uv-native-viewproj'
BASE=ROOT/'tools/th14-gpu-raster-native.py'
spec=importlib.util.spec_from_file_location('stage_stream_types',BASE);t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
C,P,U,I,F=t.C,t.P,t.U,t.I,t.F
sha=lambda b:hashlib.sha256(b).hexdigest()

MODE='viewproj'
def main():
    prepared_bytes=(INPUT/'prepared.json').read_bytes();prepared=json.loads(prepared_bytes)
    header=t.SDK.read_text(encoding='utf8');tables={}
    for name in ('IDirect3D9','IDirect3DDevice9','IDirect3DSurface9','IDirect3DTexture9','IDirect3DPixelShader9','IDirect3DVertexShader9'):
        body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
        tables[name]={a.strip() or b.strip():i for i,(a,b) in enumerate(t.re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body))}
    def method(obj,interface,name,signature):
        address=C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]]
        return C.WINFUNCTYPE(I,P,*signature)(address)
    def call(obj,interface,name,signature,values):
        result=method(obj,interface,name,signature)(obj,*values);assert result>=0,(name,hex(result&0xffffffff))
    device=P();d3d=P();rt=P();depth=P();readback=P();pixel_shader=P();vertex_shader=P();matrices={};textures={};window=None;pixels=bytearray();frames=[]
    user=C.WinDLL('user32');user.CreateWindowExW.restype=P;user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P];user.DestroyWindow.argtypes=[P]
    dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
    try:
        window=user.CreateWindowExW(0,'STATIC','TH14 Stage direct stream HAL',0,0,0,640,480,None,None,None,None);assert window
        d3d=P(dll.Direct3DCreate9(32));assert d3d
        pp=t.Present(640,480,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
        call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x40,C.byref(pp),C.byref(device)])
        call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[640,480,116,0,0,0,C.byref(rt),None])
        call(device,'IDirect3DDevice9','CreateDepthStencilSurface',[U,U,U,U,U,I,C.POINTER(P),P],[640,480,80,0,0,1,C.byref(depth),None])
        call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[640,480,116,2,C.byref(readback),None])
        call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[depth])

        shader_source=b'ps_2_0\ndcl t0.xy\ndcl_2d s0\ndef c0,0,1,0,1\ntexld r1,t0,s0\nmov r0.xy,t0\nmov r0.zw,c0\nmov oC0,r0\n'
        (OUT/'probe.asm').write_bytes(shader_source)
        compiler=C.WinDLL('d3dcompiler_47');compiler.D3DAssemble.argtypes=[P,C.c_size_t,C.c_char_p,P,P,U,C.POINTER(P),C.POINTER(P)];compiler.D3DAssemble.restype=I
        blob=P();errors=P();source=C.create_string_buffer(shader_source)
        def blob_method(obj,index,result,*sig):return C.WINFUNCTYPE(result,P,*sig)(C.cast(obj,C.POINTER(C.POINTER(P))).contents[index])
        try:
            hr=compiler.D3DAssemble(source,len(shader_source),b'world-uv-probe.asm',None,None,0,C.byref(blob),C.byref(errors))
            if hr<0:raise RuntimeError(C.string_at(blob_method(errors,3,P)(errors),blob_method(errors,4,C.c_size_t)(errors)).decode())
            code=C.string_at(blob_method(blob,3,P)(blob),blob_method(blob,4,C.c_size_t)(blob));(OUT/'probe.pso').write_bytes(code);buffer=C.create_string_buffer(code)
            call(device,'IDirect3DDevice9','CreatePixelShader',[P,C.POINTER(P)],[buffer,C.byref(pixel_shader)])
            blob_method(blob,2,U)(blob);blob=P()
            vertex_source=b'vs_2_0\ndcl_position v0\ndcl_texcoord v1\nm4x4 oPos,v0,c0\nmov oT0,v1\n'
            (OUT/'probe.vs.asm').write_bytes(vertex_source);source=C.create_string_buffer(vertex_source)
            hr=compiler.D3DAssemble(source,len(vertex_source),b'world-uv-matrix.asm',None,None,0,C.byref(blob),C.byref(errors));assert hr>=0,hex(hr&0xffffffff)
            vertex_code=C.string_at(blob_method(blob,3,P)(blob),blob_method(blob,4,C.c_size_t)(blob));(OUT/'probe.vso').write_bytes(vertex_code);buffer=C.create_string_buffer(vertex_code)
            call(device,'IDirect3DDevice9','CreateVertexShader',[P,C.POINTER(P)],[buffer,C.byref(vertex_shader)])

        finally:
            for obj in (errors,blob):
                if obj.value:blob_method(obj,2,U)(obj)
        lock=t.Lock()
        for n in prepared['textures']:
            texture=P();call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[n['width'],n['height'],1,0,n['format'],1,C.byref(texture),None])
            textures[n['handle']]=texture;raw=(INPUT/n['file']).read_bytes();assert sha(raw)==n['sha256']
            call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
            for y in range(n['height']):C.memmove(lock.bits+y*lock.pitch,raw[y*n['pitch']:(y+1)*n['pitch']],n['pitch'])
            call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
        def rs(key,value):call(device,'IDirect3DDevice9','SetRenderState',[U,U],[key,value])
        def ts(stage,key,value):call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[stage,key,value])
        def ss(sampler,key,value):call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[sampler,key,value])
        floatword=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]

        f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
        def multiply(a,b):
            result=[]
            for col in range(4):
                for row in range(4):
                    terms=[a[k*4+row]*b[col*4+k] for k in range(4)]
                    if MODE=='double':v=f32(sum(terms))
                    elif MODE=='pair':v=f32(f32(f32(terms[0])+f32(terms[1]))+f32(f32(terms[2])+f32(terms[3])))
                    else:
                        v=f32(terms[0])
                        for tvalue in terms[1:]:v=f32(v+f32(tvalue))
                    result.append(v)
            return result
        def execute(c):
            kind=c['kind']
            if kind=='renderState':rs(c['key'],c['value'])
            elif kind=='samplerState':ss(c['sampler'],c['key'],c['value'])
            elif kind=='textureStageState':ts(c['stage'],c['key'],c['value'])
            elif kind=='texture':call(device,'IDirect3DDevice9','SetTexture',[U,P],[c['sampler'],textures.get(c['handle'])])
            elif kind=='fvf':call(device,'IDirect3DDevice9','SetFVF',[U],[c['value']])
            elif kind=='transform':
                matrices[c['key']]=[struct.unpack('<f',struct.pack('<I',w))[0] for w in c['words']]
                words=(U*16)(*c['words']);call(device,'IDirect3DDevice9','SetTransform',[U,P],[c['key'],C.byref(words)])
            elif kind=='viewport':
                words=(U*6)(*c['words']);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(words)])
            elif kind=='clear':
                words=(U*len(c['rectangles']))(*c['rectangles']) if c['rectangles'] else None
                value=F.from_buffer_copy(struct.pack('<I',c['depthWord'])).value
                call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[len(c['rectangles'])//4,C.byref(words) if words else None,c['flags'],c['color'],value,c['stencil']])
            elif kind=='draw':
                words=(U*len(c['words']))(*c['words']);call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[c['topology'],c['count'],C.byref(words),c['stride']])
            else:assert kind in ('controlledScreenQueue','controlledScreenFlush'),kind
        for frame in prepared['frames']:
            selected_draw={(3,599):68,(3,1199):45}.get((frame['stage'],frame['frame']))
            if selected_draw is None:continue
            for k,v in ((7,1),(14,1),(15,1),(19,5),(20,6),(22,1),(23,8),(24,1),(25,7),(27,1),(28,1),(34,0xffa0a0a0),(35,0),(36,floatword(1000)),(37,floatword(5000)),(38,floatword(1)),(48,0),(137,0),(140,3),(161,0),(168,15),(171,1),(194,0),(206,0)):rs(k,v)
            for k,v in ((1,4),(2,2),(3,3),(4,4),(5,2),(6,3),(11,0),(24,2)):ts(0,k,v)
            ts(1,1,1)
            for k,v in ((1,1),(2,1),(5,2),(6,2),(7,0),(11,0)):ss(0,k,v)
            vp=t.Viewport(0,0,640,480,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,3,0,1,0])
            for c in frame['initialState']:execute(c)
            call(device,'IDirect3DDevice9','BeginScene',[],[])

            draw_index=0
            for c in frame['commands']:
                if c['kind']=='draw':
                    if draw_index==selected_draw:
                        for k,v in ((7,0),(14,0),(15,0),(27,0),(28,0)):rs(k,v)

                        combined=multiply(multiply(matrices[3],matrices[2]),matrices[256]) if MODE=='viewproj' else multiply(matrices[3],multiply(matrices[2],matrices[256]))
                        constants=(F*16)(*[combined[row+col*4] for row in range(4) for col in range(4)])
                        assert matrices[16]==[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
                        call(device,'IDirect3DDevice9','SetVertexShader',[P],[vertex_shader]);call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[0,C.byref(constants),4])
                        call(device,'IDirect3DDevice9','SetPixelShader',[P],[pixel_shader]);execute(c)

                    draw_index+=1
                elif c['kind']=='clear':execute(dict(c,color=0))
                else:execute(c)
            call(device,'IDirect3DDevice9','EndScene',[],[])
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback]);call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            raw=b''.join(C.string_at(lock.bits+y*lock.pitch,640*16) for y in range(480));call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            frames.append(dict(stage=frame['stage'],frame=frame['frame'],offset=len(pixels),bytes=len(raw),sha256=sha(raw),directDraws=1,originalDrawIndex=selected_draw,controlledScreenQuadsExcluded=frame['controlledScreenQuadsExcluded']))
            pixels.extend(raw);print('HAL Stage stream',frame['stage'],frame['frame'],frame['directDraws'],flush=True)
        (OUT/'native.rgba32f').write_bytes(pixels)
        report=dict(generated=True,completeGame=False,nativeEquivalent=False,behaviorFlags=0x40,width=640,height=480,format=116,bytesPerPixel=16,frames=frames,bytes=len(pixels),pixelsSha256=sha(pixels),preparedSha256=sha(prepared_bytes),toolSha256=sha(Path(__file__).read_bytes()),typesSha256=sha(BASE.read_bytes()),d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),sdkSha256=sha(t.SDK.read_bytes()),scope='Two captured world quads, authored vs2 combined-matrix vertex shader and original matrix inputs. Mode viewproj. This is not the FFP reference. Authored ps2 shader outputs interpolated UV and coverage alpha1 to RGBA32F, clears all other pixels to zero. Depth/alpha/blend/fog disabled, other draws excluded. This is an independent varying probe, not original game rendering.')
        (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print('Generated independent HAL frames',len(frames),len(pixels),'bytes')
    finally:
        if vertex_shader.value:method(vertex_shader,'IDirect3DVertexShader9','Release',[])(vertex_shader)
        if pixel_shader.value:method(pixel_shader,'IDirect3DPixelShader9','Release',[])(pixel_shader)
        for texture in textures.values():
            if texture.value:method(texture,'IDirect3DTexture9','Release',[])(texture)
        for obj,interface in ((readback,'IDirect3DSurface9'),(depth,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
            if obj.value:method(obj,interface,'Release',[])(obj)
        if window:user.DestroyWindow(window)
if __name__=='__main__':main()
