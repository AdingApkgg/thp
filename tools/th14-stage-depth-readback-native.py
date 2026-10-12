"""Probe installed NVAPI copies from our hidden D16 surface, never a retail process."""
import ctypes as C,hashlib,importlib.util,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay/depth-reference'
spec=importlib.util.spec_from_file_location('depth_types',ROOT/'tools/th14-gpu-raster-native.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
P,U,I,F=t.P,t.U,t.I,t.F
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    ref=json.loads((OUT/'reference.json').read_bytes());header=(OUT/'nvapi_interface.h').read_bytes();assert sha(header)==ref['sha256']
    ids={n:int(v,16) for n,v in ref['ids'].items()};tables={}
    for name in ('IDirect3D9','IDirect3DDevice9','IDirect3DSurface9','IDirect3DTexture9'):
        body=t.SDK.read_text().split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
        tables[name]={a.strip() or b.strip():i for i,(a,b) in enumerate(re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body))}
    def method(obj,interface,name,sig):return C.WINFUNCTYPE(I,P,*sig)(C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]])
    def call(obj,interface,name,sig,args):
        r=method(obj,interface,name,sig)(obj,*args);assert r>=0,(name,hex(r&0xffffffff));return r
    nvpath=Path('C:/Windows/System32/nvapi64.dll');nv=C.CDLL(str(nvpath));nv.nvapi_QueryInterface.restype=P;nv.nvapi_QueryInterface.argtypes=[U]
    def api(name,sig):
        addr=nv.nvapi_QueryInterface(ids[name]);assert addr,name;return C.CFUNCTYPE(I,*sig)(addr)
    init=api('NvAPI_Initialize',[]);unload=api('NvAPI_Unload',[]);register=api('NvAPI_D3D9_RegisterResource',[P]);unregister=api('NvAPI_D3D9_UnregisterResource',[P]);copy=api('NvAPI_D3D9_StretchRectEx',[P,P,P,P,P,U]);alias=api('NvAPI_D3D9_AliasSurfaceAsTexture',[P,P,C.POINTER(P),U])
    assert init()==0
    user=C.WinDLL('user32');user.CreateWindowExW.restype=P;user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P];user.DestroyWindow.argtypes=[P]
    dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
    window=None;d3d=P();device=P();depth=P();rt=P();resources=[];registered=[];rows=[]
    try:
        window=user.CreateWindowExW(0,'STATIC','TH14 D16 readback probe',0,0,0,64,64,None,None,None,None);assert window
        d3d=P(dll.Direct3DCreate9(32));pp=t.Present(64,64,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
        call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x40,C.byref(pp),C.byref(device)])
        call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[64,64,21,0,0,0,C.byref(rt),None])
        call(device,'IDirect3DDevice9','CreateDepthStencilSurface',[U,U,U,U,U,I,C.POINTER(P),P],[64,64,80,0,0,1,C.byref(depth),None])
        call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[depth]);vp=t.Viewport(0,0,64,64,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
        r=register(depth);rows.append(dict(operation='registerD16',status=r))
        if r==0:registered.append(depth)
        aliased=P();r=alias(device,depth,C.byref(aliased),0);rows.append(dict(operation='aliasD16',status=r))
        if aliased.value:resources.append((aliased,'IDirect3DTexture9'))
        for fmt in (114,21):
            tex=P();r=method(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P])(device,64,64,1,1,fmt,0,C.byref(tex),None);row=dict(operation='copyD16',destinationFormat=fmt,createHresult=r&0xffffffff,samples=[]);rows.append(row)
            if r<0:continue
            resources.append((tex,'IDirect3DTexture9'));r=register(tex);row['registerStatus']=r
            if r:continue
            registered.append(tex);surf=P();back=P();call(tex,'IDirect3DTexture9','GetSurfaceLevel',[U,C.POINTER(P)],[0,C.byref(surf)]);resources.append((surf,'IDirect3DSurface9'))
            r=method(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P])(device,64,64,fmt,2,C.byref(back),None);row['readbackCreateHresult']=r&0xffffffff
            if r<0:continue
            resources.append((back,'IDirect3DSurface9'))
            for value in (0,.25,.5,.75,1):
                call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,2,0,value,0]);r=copy(device,depth,None,tex,None,0);sample=dict(clearDepth=value,copyStatus=r);row['samples'].append(sample)
                if r:continue
                r=method(device,'IDirect3DDevice9','GetRenderTargetData',[P,P])(device,surf,back);sample['readbackHresult']=r&0xffffffff
                if r<0:continue
                lock=t.Lock();call(back,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16]);raw=b''.join(C.string_at(lock.bits+y*lock.pitch,64*4) for y in range(64));call(back,'IDirect3DSurface9','UnlockRect',[],[])
                sample['sha256']=sha(raw);sample['firstWord']=struct.unpack('<I',raw[:4])[0]
                if fmt==114:sample['firstFloat']=struct.unpack('<f',raw[:4])[0]
                (OUT/('probe-%d-%s.bin'%(fmt,str(value)))).write_bytes(raw)
        report=dict(queried=True,completeGame=False,nativeEquivalent=False,rows=rows,toolSha256=sha(Path(__file__).read_bytes()),interfaceSha256=sha(header),referenceSha256=sha((OUT/'reference.json').read_bytes()),nvapiSha256=sha(nvpath.read_bytes()),d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),scope='Hidden own 64x64 D16 surface clear and NVAPI capability/readback probe. No game draws or retail depth capture; failed conversions retained.')
        (OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows))
    finally:
        for obj in reversed(registered):unregister(obj)
        for obj,interface in reversed(resources):method(obj,interface,'Release',[])(obj)
        for obj,interface in ((depth,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
            if obj.value:method(obj,interface,'Release',[])(obj)
        if window:user.DestroyWindow(window)
        unload()
if __name__=='__main__':main()
