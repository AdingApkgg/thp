"""Offscreen Direct3D9 pixel reference for the shared TH14 renderer.

No game files are modified and no native window is shown. This is a device
test with material values previously recovered from the retail executable,
not a capture of the whole original game.
"""
import ctypes as C, hashlib, itertools, json, re, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/gpu-screen-grid';OUT.mkdir(parents=True,exist_ok=True)
SDK=Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h')
P=C.c_void_p;U=C.c_uint32;I=C.c_int32;F=C.c_float
class Present(C.Structure):
    _fields_=[(n,U) for n in ('width','height','format','count','multisample','quality','swap')]+[('window',P),('windowed',I),('depth',I)]+[(n,U) for n in ('depth_format','flags','refresh','interval')]
class Lock(C.Structure):_fields_=[('pitch',I),('bits',P)]
class Viewport(C.Structure):_fields_=[(n,U) for n in ('x','y','width','height')]+[('min',F),('max',F)]
class Vertex(C.Structure):_fields_=[(n,F) for n in ('x','y','z','rhw')]+[('color',U)]

def main():
    header=SDK.read_text(encoding='utf8');tables={}
    for name in ('IDirect3D9','IDirect3DDevice9','IDirect3DSurface9','IDirect3DTexture9'):
        body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
        methods=[a.strip() or b.strip() for a,b in re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body)]
        tables[name]={method:index for index,method in enumerate(methods)}
    assert tables['IDirect3DDevice9']['SetRenderState']==57
    def method(obj,interface,name,signature):
        address=C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]]
        return C.WINFUNCTYPE(I,P,*signature)(address)
    def call(obj,interface,name,types,values):
        result=method(obj,interface,name,types)(obj,*values)
        assert result>=0,(name,hex(result&0xffffffff));return result
    device=P();d3d=P();rt=P();readback=P();texture=P();window=None
    user=C.WinDLL('user32');user.CreateWindowExW.restype=P
    user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P]
    user.DestroyWindow.argtypes=[P];dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
    materials_path=ROOT/'artifacts/th14/gpu-original-quads/geometry/native.json';materials_bytes=materials_path.read_bytes();materials=json.loads(materials_bytes)
    recovered={r['blend']:{e[1]:e[2] for e in r['events'] if e[0]=='state'} for r in materials['materials'] if r['u']==r['v']==r['point']==0}
    pixels=bytearray();cases=[];texture_words=[((47+i*53)%256)<<24|((31+i*73)%256)<<16|((19+i*41)%256)<<8|((11+i*97)%256) for i in range(16)]
    try:
        window=user.CreateWindowExW(0,'STATIC','TH14 offscreen raster fixture',0,0,0,64,64,None,None,None,None);assert window
        d3d=P(dll.Direct3DCreate9(32));assert d3d
        pp=Present(640,480,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
        call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x40,C.byref(pp),C.byref(device)])
        call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[640,480,21,0,0,0,C.byref(rt),None])
        call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[640,480,21,2,C.byref(readback),None])
        call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[4,4,1,0,21,1,C.byref(texture),None])
        lock=Lock();call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
        for y in range(4):C.memmove(lock.bits+y*lock.pitch,struct.pack('<4I',*texture_words[y*4:y*4+4]),16)
        call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
        call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[None])
        vp=Viewport(0,0,640,480,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
        call(device,'IDirect3DDevice9','SetFVF',[U],[0x44]);call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,None])
        rs=lambda k,v:call(device,'IDirect3DDevice9','SetRenderState',[U,U],[k,v])
        sampler=lambda k,v:call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,v])
        for k,v in ((7,0),(14,0),(15,1),(22,1),(27,1),(28,0),(137,0),(161,0),(168,15),(194,0),(206,0)):rs(k,v)
        for k,v in ((1,2),(2,0),(3,0),(4,2),(5,0),(6,0)):
            call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[0,k,v])
        call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[1,1,1]);sampler(11,0)
        rs(24,1);rs(25,7)
        for key,value in ((19,5),(20,6),(171,1)):rs(key,value)
        prepared=json.loads((OUT/'prepared.json').read_text())
        for row in prepared['cases']:
            source=row
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0xff42678b,1,0])
            call(device,'IDirect3DDevice9','BeginScene',[],[])
            for draw in source['draws']:
                assert draw['stride']==20
                vertices=(Vertex*len(draw['vertices']))(*(Vertex(*v) for v in draw['vertices']))
                call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[draw['topology'],draw['count'],C.byref(vertices),C.sizeof(Vertex)])
            call(device,'IDirect3DDevice9','EndScene',[],[])
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback])
            call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            left,top,width,height=row['crop'];raw=b''.join(C.string_at(lock.bits+y*lock.pitch+left*4,width*4) for y in range(top,top+height))
            call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            cases.append(dict(**row,pixelsSha256=hashlib.sha256(raw).hexdigest()));pixels+=raw
        (OUT/'native.bgra').write_bytes(pixels)
        report=dict(generated=True,completeGame=False,nativeEquivalent=False,width=640,height=480,behaviorFlags=64,vertexProcessing="Hardware",preparedSha256=hashlib.sha256((OUT/"prepared.json").read_bytes()).hexdigest(),cases=cases,texture=texture_words,materialOracleSha256=hashlib.sha256(materials_bytes).hexdigest(),nativeExecutableSha256=materials['executableSha256'],d3d9Sha256=hashlib.sha256(Path('C:/Windows/System32/d3d9.dll').read_bytes()).hexdigest(),sdkHeaderSha256=hashlib.sha256(SDK.read_bytes()).hexdigest(),pixelsSha256=hashlib.sha256(pixels).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual HAL rasterization of controlled derived untextured rectangle, gradient, bordered rectangle, circle fan and line strip geometry at 640x480, cropped without rescaling; controlled blend/alpha and disabled fog/depth. Independent production geometry is compared separately. Original full draw loop is not executed')
        (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(f'Generated {len(cases)} actual D3D9 raster fixtures ({len(pixels)} bytes)')
    finally:
        for obj,interface in ((texture,'IDirect3DTexture9'),(readback,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
            if obj.value:method(obj,interface,'Release',[])(obj)
        if window:user.DestroyWindow(window)

if __name__=='__main__':main()
