"""18 real D3D9 HAL text draws from independent original geometry; no game window/audio."""
from pathlib import Path
import ctypes as C,hashlib,importlib.util,json,re,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-atlas-raster-nov12';O=H/'d3d9';O.mkdir(exist_ok=False)
base=R/'tools/th14-gpu-raster-native.py';spec=importlib.util.spec_from_file_location('types14',base);t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
P,U,I,F=t.P,t.U,t.I,t.F;sha=lambda b:hashlib.sha256(b).hexdigest()
ref=json.loads((H/'geometry/report.json').read_bytes());assert not ref['error'] and ref['cases']==18
meta=json.loads((R/'artifacts/archive-differential/th14.json').read_bytes());asset=(Path(meta['extraction'])/'ascii.anm').read_bytes();assert sha(asset)==ref['asciiSha256']
pages=[];off=0
while True:
    nxt=struct.unpack_from('<I',asset,off+36)[0];thtx=off+struct.unpack_from('<I',asset,off+28)[0]
    magic,zero,fmt,w,h,n=struct.unpack_from('<4s4HI',asset,thtx);assert magic==b'THTX' and fmt==5 and n==w*h*2
    pages.append((w,h,asset[thtx+16:thtx+16+n]));assert len(pages[-1][2])==n
    if not nxt:break
    off+=nxt
assert len(pages)==2
header=t.SDK.read_text(encoding='utf8');tables={}
for name in ['IDirect3D9','IDirect3DDevice9','IDirect3DSurface9','IDirect3DTexture9']:
    body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
    tables[name]={a.strip() or b.strip():i for i,(a,b) in enumerate(re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body))}
def method(obj,interface,name,signature):
    address=C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]]
    return C.WINFUNCTYPE(I,P,*signature)(address)
def call(obj,interface,name,sig,args):
    result=method(obj,interface,name,sig)(obj,*args);assert result>=0,(name,hex(result&0xffffffff));return result
device=P();d3d=P();rt=P();readback=P();textures=[];window=None;cases=[];total=0
user=C.WinDLL('user32');user.CreateWindowExW.restype=P;user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P];user.DestroyWindow.argtypes=[P]
dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
try:
    window=user.CreateWindowExW(0,'STATIC','TH14 hidden atlas fixture',0,0,0,64,64,None,None,None,None);assert window
    d3d=P(dll.Direct3DCreate9(32));assert d3d
    pp=t.Present(640,480,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
    call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x20,C.byref(pp),C.byref(device)])
    for w,h,pixels in pages:
        tex=P();call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[w,h,1,0,26,1,C.byref(tex),None]);textures.append(tex)
        lock=t.Lock();call(tex,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
        for y in range(h):C.memmove(lock.bits+y*lock.pitch,pixels[y*w*2:(y+1)*w*2],w*2)
        call(tex,'IDirect3DTexture9','UnlockRect',[U],[0])
    with (O/'native.bgra').open('wb') as output:
        size=None
        for index,row in enumerate(ref['rows']):
            w,h=row['width'],row['height']
            if size!=(w,h):
                if rt.value:method(rt,'IDirect3DSurface9','Release',[])(rt);rt=P()
                if readback.value:method(readback,'IDirect3DSurface9','Release',[])(readback);readback=P()
                call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[w,h,21,0,0,0,C.byref(rt),None])
                call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[w,h,21,2,C.byref(readback),None]);size=(w,h)
            call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[None])
            rs=lambda k,v:call(device,'IDirect3DDevice9','SetRenderState',[U,U],[k,v])
            for k,v in [(7,0),(14,0),(15,1),(22,1),(24,1),(25,7),(27,1),(28,0),(137,0),(161,0),(168,15),(194,0),(206,0)]:rs(k,v)
            call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[1,1,1])
            vp=t.Viewport(0,0,w,h,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0x7f42678b,1,0]);call(device,'IDirect3DDevice9','BeginScene',[],[])
            for draw in row['draws']:
                if draw['viewport']:vp=t.Viewport(*draw['viewport'])
                else:vp=t.Viewport(0,0,w,h,0,1)
                call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
                for k,v in draw['renderStates'].items():rs(int(k),v)
                for k,v in draw['samplers'].items():call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,int(k),v])
                for k,v in draw['stages'].items():call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[0,int(k),v])
                call(device,'IDirect3DDevice9','SetFVF',[U],[draw['fvf']]);call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,textures[draw['texture']-1]])
                vertices=C.create_string_buffer(bytes.fromhex(draw['verticesHex']));assert draw['topology']==4
                call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[4,draw['vertices']//3,C.byref(vertices),draw['stride']])
            call(device,'IDirect3DDevice9','EndScene',[],[]);call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback])
            lock=t.Lock();call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            pixels=b''.join(C.string_at(lock.bits+y*lock.pitch,w*4) for y in range(h));call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            output.write(pixels);cases.append(dict(index=index,width=w,height=h,font=row['font'],passIndex=row['passIndex'],offset=total,bytes=len(pixels),sha256=sha(pixels)));total+=len(pixels);assert total<=60000000
finally:
    for obj,interface in [(x,'IDirect3DTexture9') for x in textures]+[(readback,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')]:
        if obj.value:method(obj,interface,'Release',[])(obj)
    if window:assert user.DestroyWindow(window)
report=dict(cases=cases,bytes=total,rawSha256=sha((O/'native.bgra').read_bytes()),originalGeometryReportSha256=sha((H/'geometry/report.json').read_bytes()),assetSha256=sha(asset),toolSha256=sha(Path(__file__).read_bytes()),d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),allDeviceObjectsReleased=True,hiddenWindowDestroyed=True,declaredFogAndDepthDisabled=True,initialOtherDeviceStateDeclared=True,newGameRuns=0,audioDeviceOpened=False,completeGame=False)
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':len(cases),'bytes':total,'released':True}))
