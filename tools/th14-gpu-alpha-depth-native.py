"""Actual D3D9 pixels with alpha discard, blending and D16/D24S8 depth writes.

Uses only a hidden fixture window. Original game files remain read-only.
"""
import importlib.util, itertools, json, hashlib, struct
from pathlib import Path
BASE=Path(__file__).with_name('th14-gpu-raster-native.py')
spec=importlib.util.spec_from_file_location('th14_gpu_types',BASE)
types=importlib.util.module_from_spec(spec);spec.loader.exec_module(types)
C,P,U,I,F=types.C,types.P,types.U,types.I,types.F
ROOT=types.ROOT;OUT=ROOT/'artifacts/th14/gpu-alpha-depth';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    out=OUT
    materials_bytes=(ROOT/'artifacts/th14/render-native.json').read_bytes();materials=json.loads(materials_bytes)
    recovered={r['blend']:{e[1]:e[2] for e in r['events'] if e[0]=='state'} for r in materials['materials'] if r['u']==r['v']==r['point']==0}
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
    device=P();d3d=P();rt=P();readback=P();texture=P();depth16=P();depth24=P();window=None
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
        call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[32,32,21,0,0,0,C.byref(rt),None])
        call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[32,32,21,2,C.byref(readback),None])
        call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[4,4,1,0,21,1,C.byref(texture),None])
        lock=types.Lock();call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
        for y in range(4):C.memmove(lock.bits+y*lock.pitch,struct.pack('<4I',*words[y*4:y*4+4]),16)
        call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
        call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt])
        for fmt,obj in ((80,depth16),(75,depth24)):
            call(device,'IDirect3DDevice9','CreateDepthStencilSurface',[U,U,U,U,U,I,C.POINTER(P),P],[32,32,fmt,0,0,1,C.byref(obj),None])
        vp=types.Viewport(0,0,32,32,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
        call(device,'IDirect3DDevice9','SetFVF',[U],[0x144]);call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,texture])
        rs=lambda k,v:call(device,'IDirect3DDevice9','SetRenderState',[U,U],[k,v])
        for k,v in ((7,0),(14,0),(15,1),(22,1),(27,1),(28,0),(137,0),(161,0),(168,15),(194,0),(206,0)):rs(k,v)
        stage=lambda k,v:call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[0,k,v])
        for k,v in ((1,4),(2,2),(3,0),(5,2),(6,0)):stage(k,v)
        call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[1,1,1])
        for k,v in ((1,3),(2,3),(5,2),(6,2),(11,0)):
            call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,v])
        colors=[0xc8b56e29,0x795ac4e8,0xea28cf7b,0x467c318e]
        V=types.Vertex;vertices=(V*4)(V(3.5,4.5,0,1,colors[0],-.25,-.125),V(25.5,4.5,0,1,colors[1],1.25,-.125),V(3.5,26.5,0,1,colors[2],-.25,1.125),V(25.5,26.5,0,1,colors[3],1.25,1.125))
        for format,compare,write,depth,reference,low,point in itertools.product(range(2),range(1,9),range(2),range(5),(0,1,2,128),range(2),range(2)):
            words=[(i%4 if low else (47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256) for i in range(16)]
            call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
            for y in range(4):C.memmove(lock.bits+y*lock.pitch,struct.pack('<4I',*words[y*4:y*4+4]),16)
            call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
            state={19:5,20:6,171:1}
            for k,v in state.items():rs(k,v)
            for k in (5,6):call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,1 if point else 2])
            stage(4,4);rs(15,1);rs(25,7);rs(24,reference);rs(7,1);rs(14,write);rs(23,compare);rs(27,1)
            call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,texture])
            call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[depth24 if format else depth16])
            z0=struct.unpack('<f',struct.pack('<f',.6))[0];bits=struct.unpack('<I',struct.pack('<f',z0))[0]
            z=(.25,z0,struct.unpack('<f',struct.pack('<I',bits-1))[0],struct.unpack('<f',struct.pack('<I',bits+1))[0],.75)[depth]
            for v in vertices:v.z=z
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,3,0xff42678b,.75,0])
            call(device,'IDirect3DDevice9','BeginScene',[],[])
            call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,C.byref(vertices),C.sizeof(V)])
            rs(27,0);rs(15,0);rs(14,0);rs(23,4)
            call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,None])
            back=(V*4)(V(-.5,-.5,z0,1,0xffdda336,0,0),V(31.5,-.5,z0,1,0xffdda336,0,0),V(-.5,31.5,z0,1,0xffdda336,0,0),V(31.5,31.5,z0,1,0xffdda336,0,0))
            call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,C.byref(back),C.sizeof(V)])
            call(device,'IDirect3DDevice9','EndScene',[],[])
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback])
            call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            raw=b''.join(C.string_at(lock.bits+y*lock.pitch,128) for y in range(32))
            call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            cases.append(dict(format=format,compare=compare,write=write,depth=depth,reference=reference,low=low,point=point,z=z,backZ=z0,pixelsSha256=sha(raw)));pixels+=raw
        (out/'native.bgra').write_bytes(pixels)
        report=dict(generated=True,completeGame=False,nativeEquivalent=False,materialOracleSha256=sha(materials_bytes),nativeExecutableSha256=materials["executableSha256"],width=32,height=32,cases=cases,textureFormula="A=low?i%4:(47+53*i)%256;R=(31+73*i)%256;G=(19+41*i)%256;B=(11+97*i)%256",pixelsSha256=sha(pixels),tools={p.name:sha(p.read_bytes()) for p in (BASE,Path(__file__))},d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),sdkHeaderSha256=sha(types.SDK.read_bytes()),scope='Actual D3D9 HAL fixture: alpha discard before depth writes, D16/D24S8 x8 depth compares x2 write states x5 front depths x4 alpha references x2 alpha ranges x2 filters, opaque second layer at0.6. Separate hidden device; not native game draw-loop capture.')
        (out/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(f'Generated {len(cases)} actual D3D9 alpha fixtures ({len(pixels)} bytes)')
    finally:
        for obj,interface in ((depth16,'IDirect3DSurface9'),(depth24,'IDirect3DSurface9'),(texture,'IDirect3DTexture9'),(readback,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
            if obj.value:method(obj,interface,'Release',[])(obj)
        if window:user.DestroyWindow(window)
if __name__=='__main__':
    main()
