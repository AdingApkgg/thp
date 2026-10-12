"""Actual D3D9 world-space perspective, texture transform and vertex fog pixels.

Uses only a hidden fixture window. Original game files remain read-only.
"""
import importlib.util, itertools, json, hashlib, struct
from pathlib import Path
BASE=Path(__file__).with_name('th14-gpu-raster-native.py')
spec=importlib.util.spec_from_file_location('th14_gpu_types',BASE)
types=importlib.util.module_from_spec(spec);spec.loader.exec_module(types)
C,P,U,I,F=types.C,types.P,types.U,types.I,types.F
ROOT=types.ROOT;OUT=ROOT/'artifacts/th14/gpu-fog-factor';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    out=OUT
    header=types.SDK.read_text(encoding='utf8');tables={}
    for name in ('IDirect3D9','IDirect3DDevice9','IDirect3DSurface9','IDirect3DTexture9'):
        body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
        methods=[a.strip() or b.strip() for a,b in types.re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body)]
        tables[name]={method:index for index,method in enumerate(methods)}
    assert tables['IDirect3DDevice9']['SetRenderState']==57
    def method(obj,interface,name,signature):
        address=C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]]
        return C.WINFUNCTYPE(I,P,*signature)(address)
    def call(obj,interface,name,signature,values):
        result=method(obj,interface,name,signature)(obj,*values)
        assert result>=0,(name,hex(result&0xffffffff))
    device=P();d3d=P();rt=P();readback=P();texture=P();window=None
    user=C.WinDLL('user32');user.CreateWindowExW.restype=P
    user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P]
    user.DestroyWindow.argtypes=[P];dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
    pixels=bytearray();cases=[]
    words=[((47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256) for i in range(16)]
    try:
        window=user.CreateWindowExW(0,'STATIC','TH14 offscreen alpha fixture',0,0,0,64,64,None,None,None,None);assert window
        d3d=P(dll.Direct3DCreate9(32));assert d3d
        pp=types.Present(32,32,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
        call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x20,C.byref(pp),C.byref(device)])
        call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[32,32,116,0,0,0,C.byref(rt),None])
        call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[32,32,116,2,C.byref(readback),None])
        call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[4,4,1,0,21,1,C.byref(texture),None])
        lock=types.Lock();call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
        for y in range(4):C.memmove(lock.bits+y*lock.pitch,struct.pack('<4I',*words[y*4:y*4+4]),16)
        call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
        call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[None])
        vp=types.Viewport(0,0,32,32,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
        call(device,'IDirect3DDevice9','SetFVF',[U],[0x142]);call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,texture])
        rs=lambda k,v:call(device,'IDirect3DDevice9','SetRenderState',[U,U],[k,v])
        for k,v in ((7,0),(14,0),(15,1),(22,1),(27,0),(28,0),(137,0),(161,0),(168,15),(194,0),(206,0)):rs(k,v)
        stage=lambda k,v:call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[0,k,v])
        for k,v in ((1,2),(2,3),(3,0),(5,2),(6,0)):stage(k,v)
        call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[1,1,1])
        for k,v in ((1,1),(2,1),(5,2),(6,2),(11,0)):
            call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,v])
        rs(60,0xffffffff)
        colors=[0xc8b56e29,0x795ac4e8,0xea28cf7b,0x467c318e]
        class V(C.Structure):_fields_=[('x',F),('y',F),('z',F),('color',U),('u',F),('v',F)]
        vertices=(V*4)(V(-.65,.65,1,colors[0],-.25,-.125),V(.65,.65,1,colors[1],1.25,-.125),V(-.65,-.65,2,colors[2],-.25,1.125),V(.65,-.65,2,colors[3],1.25,1.125))
        worlds=[[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],[0,1,0,0,-1,0,0,0,0,0,1,0,.125,-.125,.5,1],[.75,0,0,0,0,1.25,0,0,0,0,1,0,-.125,.125,.25,1]]
        views=[[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],[1,0,0,0,0,1,0,0,0,0,1,0,0,.125,.5,1]]
        f32=lambda v:F(v).value
        projections=[[1,0,0,0,0,1,0,0,0,0,f32(1/f32(9.9)),0,0,0,f32(-f32(.1)/f32(9.9)),1],[1,0,0,0,0,1,0,0,0,0,f32(10/f32(9.9)),1,0,0,f32(-1/f32(9.9)),0]]
        texmatrix=[.75,0,0,0,0,.5,0,0,.125,.25,1,0,0,0,0,1]
        floatword=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
        for world,view,projection,texture_transform,fog,range_fog,point in itertools.product(range(3),range(2),range(2),range(2),range(4),range(2),range(2)):
            for kind,values in ((256,worlds[world]),(2,views[view]),(3,projections[projection]),(16,texmatrix)):
                matrix=(F*16)(*values);call(device,'IDirect3DDevice9','SetTransform',[U,P],[kind,C.byref(matrix)])
            stage(4,4);stage(24,2 if texture_transform else 0);rs(25,7);rs(24,1)
            for k,v in ((28,int(fog!=0)),(34,0xff000000),(35,0),(36,floatword(.75)),(37,floatword(2.5)),(38,floatword(.6)),(48,range_fog),(140,fog)):rs(k,v)
            for k in (5,6):call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,1 if point else 2])
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0xff42678b,1,0])
            call(device,'IDirect3DDevice9','BeginScene',[],[])
            call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,C.byref(vertices),C.sizeof(V)])
            call(device,'IDirect3DDevice9','EndScene',[],[])
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback])
            call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            raw=b''.join(C.string_at(lock.bits+y*lock.pitch,512) for y in range(32))
            call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            cases.append(dict(world=world,view=view,projection=projection,textureTransform=texture_transform,fog=fog,range=range_fog,point=point,pixelsSha256=sha(raw)));pixels+=raw
        (out/'native.rgba32f').write_bytes(pixels)
        report=dict(generated=True,completeGame=False,nativeEquivalent=False,worldMatrices=worlds,viewMatrices=views,projectionMatrices=projections,textureMatrix=texmatrix,width=32,height=32,outputFormat="A32B32G32R32F",outputByteOrder="RGBA float32 little endian",cases=cases,texture=words,pixelsSha256=sha(pixels),tools={p.name:sha(p.read_bytes()) for p in (BASE,Path(__file__))},d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),sdkHeaderSha256=sha(types.SDK.read_bytes()),scope='Actual D3D9 HAL fixture: world-space orthographic/perspective projection, world/view/texture matrices and four vertex-fog modes with range/depth fog. Separate hidden device; not native game draw-loop capture.')
        (out/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(f'Generated {len(cases)} actual D3D9 alpha fixtures ({len(pixels)} bytes)')
    finally:
        for obj,interface in ((texture,'IDirect3DTexture9'),(readback,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
            if obj.value:method(obj,interface,'Release',[])(obj)
        if window:user.DestroyWindow(window)
if __name__=='__main__':
    main()
