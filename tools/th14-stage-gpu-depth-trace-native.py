"""Generate an independent per-draw D16 readback trace with official NVAPI IDs."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'depth-trace';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
inputs=json.loads((INPUT/'pixel-trace/inputs.json').read_bytes())
(OUT/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
base=ROOT/'tools/th14-stage-gpu-pixel-trace-hal.py';text=base.read_text().replace("OUT=INPUT/'pixel-trace'","OUT=INPUT/'depth-trace'")
anchor="    device=P();d3d=P();rt=P();depth=P();readback=P();textures={};window=None;pixels=bytearray();frames=[]"
assert anchor in text
text=text.replace(anchor,anchor+'''
    depth_texture=P();depth_surface=P();depth_readback=P();nv_registered=[]
    nv_reference=json.loads((INPUT/'depth-reference/reference.json').read_bytes())
    assert sha((INPUT/'depth-reference/nvapi_interface.h').read_bytes())==nv_reference['sha256']
    nv=C.CDLL('C:/Windows/System32/nvapi64.dll');nv.nvapi_QueryInterface.restype=P;nv.nvapi_QueryInterface.argtypes=[U]
    def api(name,sig):
        address=nv.nvapi_QueryInterface(int(nv_reference['ids'][name],16));assert address,name
        return C.CFUNCTYPE(I,*sig)(address)
    nv_init=api('NvAPI_Initialize',[]);nv_unload=api('NvAPI_Unload',[])
    nv_register=api('NvAPI_D3D9_RegisterResource',[P]);nv_unregister=api('NvAPI_D3D9_UnregisterResource',[P])
    nv_copy=api('NvAPI_D3D9_StretchRectEx',[P,P,P,P,P,U]);assert nv_init()==0
''')
anchor="        lock=t.Lock()";assert text.count(anchor)==1
text=text.replace(anchor,'''
        call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[640,480,1,1,114,0,C.byref(depth_texture),None])
        call(depth_texture,'IDirect3DTexture9','GetSurfaceLevel',[U,C.POINTER(P)],[0,C.byref(depth_surface)])
        call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[640,480,114,2,C.byref(depth_readback),None])
        for resource in (depth,depth_texture):assert nv_register(resource)==0;nv_registered.append(resource)
'''+anchor)
anchor="            call(readback,'IDirect3DSurface9','UnlockRect',[],[]);call(device,'IDirect3DDevice9','BeginScene',[],[])"
assert text.count(anchor)==1
text=text.replace(anchor,'''
            call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            assert nv_copy(device,depth,None,depth_texture,None,0)==0
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[depth_surface,depth_readback]);call(depth_readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            words=[struct.unpack('<I',C.string_at(lock.bits+y*lock.pitch+x*4,4))[0] for x,y in active_trace['points']]
            values=[struct.unpack('<f',struct.pack('<I',w))[0] for w in words]
            integers=[round(v*65535) for v in values]
            assert all(0<=v<=65535 for v in integers)
            active_trace.setdefault('depthSamples',[]).append(dict(floatWords=words,d16=integers))
            call(depth_readback,'IDirect3DSurface9','UnlockRect',[],[]);call(device,'IDirect3DDevice9','BeginScene',[],[])
''')
text=text.replace("No retail framebuffer or native depth-value readback.","Includes original D16 storage copied to R32F via installed NVAPI after each draw; final color frames must still match the unchanged HAL reference. No retail process framebuffer.")
anchor="    finally:\n";assert text.count(anchor)==1
text=text.replace(anchor,anchor+'''
        for resource in reversed(nv_registered):nv_unregister(resource)
        for resource,interface in ((depth_readback,'IDirect3DSurface9'),(depth_surface,'IDirect3DSurface9'),(depth_texture,'IDirect3DTexture9')):
            if resource.value:method(resource,interface,'Release',[])(resource)
        nv_unload()
''')
generated=ROOT/'tools/th14-stage-gpu-depth-trace-hal.py';generated.write_text(text)
runpy.run_path(str(generated),run_name='__main__')
report=dict(generated=True,completeGame=False,nativeEquivalent=False,generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),referenceSha256=sha((INPUT/'depth-reference/reference.json').read_bytes()),nvapiSha256=sha(Path('C:/Windows/System32/nvapi64.dll').read_bytes()),traceSha256=sha((OUT/'trace.json').read_bytes()),inputsSha256=sha((OUT/'inputs.json').read_bytes()))
(OUT/'generation.json').write_text(json.dumps(report,indent=2)+'\n')
