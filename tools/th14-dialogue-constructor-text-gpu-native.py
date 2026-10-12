"""Offscreen Direct3D9 pixel reference for the shared TH14 renderer.

No game files are modified and no native window is shown. This is a device
test with material values previously recovered from the retail executable,
not a capture of the whole original game.
"""
import ctypes as C, hashlib, itertools, json, re, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/dialogue-constructor-text';OUT.mkdir(parents=True,exist_ok=True)
SDK=Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h')
P=C.c_void_p;U=C.c_uint32;I=C.c_int32;F=C.c_float
class Present(C.Structure):
    _fields_=[(n,U) for n in ('width','height','format','count','multisample','quality','swap')]+[('window',P),('windowed',I),('depth',I)]+[(n,U) for n in ('depth_format','flags','refresh','interval')]
class Lock(C.Structure):_fields_=[('pitch',I),('bits',P)]
class Rect(C.Structure):_fields_=[(n,I) for n in ('left','top','right','bottom')]
class Viewport(C.Structure):_fields_=[(n,U) for n in ('x','y','width','height')]+[('min',F),('max',F)]
class Vertex(C.Structure):_fields_=[(n,F) for n in ('x','y','z','rhw')]+[('color',U),('u',F),('v',F)]

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
    prepared_bytes=(OUT/'scratch.json').read_bytes();prepared=json.loads(prepared_bytes)
    d3dx=C.WinDLL('d3dx9_43');upload=d3dx.D3DXLoadSurfaceFromMemory;upload.restype=I;upload.argtypes=[P,P,P,P,U,U,P,P,U,U]
    archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());data=(Path(archive['extraction'])/'text.anm').read_bytes();metadata=[];offset=0
    while True:
        width,height,fmt=struct.unpack_from('<HHH',data,offset+10);assert struct.unpack_from('<H',data,offset+28)[0]==0;metadata.append(dict(width=width,height=height,format={1:21,3:23,5:26}[fmt],pitch=width*(4 if fmt==1 else 2)));stride=struct.unpack_from('<I',data,offset+36)[0]
        if not stride:break
        offset+=stride
    assert len(metadata)==4 and metadata[0]==dict(width=1024,height=1024,format=26,pitch=2048)
    pixels=bytearray();cases=[];textures=[];loaded=None
    try:
        window=user.CreateWindowExW(0,'STATIC','TH14 offscreen raster fixture',0,0,0,64,64,None,None,None,None);assert window
        d3d=P(dll.Direct3DCreate9(32));assert d3d
        pp=Present(640,480,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
        call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x40,C.byref(pp),C.byref(device)])
        call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[640,480,21,0,0,0,C.byref(rt),None])
        call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[640,480,21,2,C.byref(readback),None])
        lock=Lock()
        call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[None])
        vp=Viewport(0,0,640,480,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
        call(device,'IDirect3DDevice9','SetFVF',[U],[0x144])
        rs=lambda k,v:call(device,'IDirect3DDevice9','SetRenderState',[U,U],[k,v])
        sampler=lambda k,v:call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,v])
        for k,v in ((7,0),(14,0),(15,1),(22,1),(27,1),(28,0),(137,0),(161,0),(168,15),(194,0),(206,0)):rs(k,v)
        for k,v in ((1,4),(2,2),(3,0),(4,4),(5,2),(6,0)):
            call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[0,k,v])
        call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[1,1,1]);sampler(11,0)
        rs(24,1);rs(25,7)
        for index,row in enumerate(prepared['rows']):
            call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,None])
            for obj in textures:method(obj,'IDirect3DTexture9','Release',[])(obj)
            textures=[]
            for record in metadata:
                texture=P();call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[record['width'],record['height'],1,0,record['format'],1,C.byref(texture),None]);textures.append(texture)
                call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
                for y in range(record['height']):C.memset(lock.bits+y*lock.pitch,0,record['pitch'])
                call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
            copied=[]
            for write in row['writes']:
                raw=(OUT/write['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==write['sha256'];source=C.create_string_buffer(raw);d=write['upload'];surface=P()
                assert d['format']==26 and d['pitch']==2048 and d['filter']==1 and d['colorKey']==0
                call(textures[0],'IDirect3DTexture9','GetSurfaceLevel',[U,C.POINTER(P)],[0,C.byref(surface)])
                destination=Rect(*d['destination']);source_rect=Rect(*d['source']);hr=upload(surface,None,C.byref(destination),source,d['format'],d['pitch'],None,C.byref(source_rect),d['filter'],d['colorKey']);assert hr>=0,hex(hr&0xffffffff)
                method(surface,'IDirect3DSurface9','Release',[])(surface)
                call(textures[0],'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,16]);raw_copy=b''.join(C.string_at(lock.bits+y*lock.pitch,2048) for y in range(1024));call(textures[0],'IDirect3DTexture9','UnlockRect',[U],[0]);copied.append(dict(line=write['line'],textureSha256=hashlib.sha256(raw_copy).hexdigest(),bytes=len(raw_copy)))
            row={**row,'textOffset':row['offset'],'draws':row['frames'][-1]['draws'],'crop':[0,0,640,480],'index':index,'offset':len(pixels),'size':640*480*4,'textureCopies':copied}
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0xff42678b,1,0])
            call(device,'IDirect3DDevice9','BeginScene',[],[])
            for draw in row['draws']:
                handle,depth,src,dst,equation,min_filter,mag_filter,u,v=draw['material']
                call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,textures[handle-1]])
                for key,value in ((14,depth),(19,src),(20,dst),(171,equation)):rs(key,value)
                for key,value in ((5,min_filter),(6,mag_filter),(1,u),(2,v)):sampler(key,value)
                vertices=(Vertex*4)(*(Vertex(*v) for v in draw['vertices']))
                call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,C.byref(vertices),C.sizeof(Vertex)])
            call(device,'IDirect3DDevice9','EndScene',[],[])
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback])
            call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            left,top,width,height=row['crop'];raw=b''.join(C.string_at(lock.bits+y*lock.pitch+left*4,width*4) for y in range(top,top+height))
            call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            cases.append(dict(**{k:v for k,v in row.items() if k!='draws'},drawCount=len(row['draws']),pixelsSha256=hashlib.sha256(raw).hexdigest()));pixels+=raw
        (OUT/'native.bgra').write_bytes(pixels)
        report=dict(generated=True,completeGame=False,nativeEquivalent=False,width=640,height=480,behaviorFlags=64,vertexProcessing='Hardware',scratchProofSha256=hashlib.sha256(prepared_bytes).hexdigest(),cases=cases,resourceHashes=prepared['resourceHashes'],textures=metadata,nativeExecutableSha256=prepared['executableSha256'],nativeD3dxSha256=prepared['d3dxSha256'],d3d9Sha256=hashlib.sha256(Path('C:/Windows/System32/d3d9.dll').read_bytes()).hexdigest(),sdkHeaderSha256=hashlib.sha256(SDK.read_bytes()).hexdigest(),pixelsSha256=hashlib.sha256(pixels).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope=prepared['scope']+' Host64 D3DXLoadSurfaceFromMemory uploads captured scratch/rectangles to actual blank text.anm atlas dimensions and formats; four full-atlas hashes after successive writes plus selected animation frame12 HAL screen draw. Original32bitCOM/full loader/fullworld excluded.')
        (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(f'Generated {len(cases)} actual D3D9 raster fixtures ({len(pixels)} bytes)')
    finally:
        for obj in textures:method(obj,'IDirect3DTexture9','Release',[])(obj)
        for obj,interface in ((readback,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
            if obj.value:method(obj,interface,'Release',[])(obj)
        if window:user.DestroyWindow(window)

if __name__=='__main__':main()
