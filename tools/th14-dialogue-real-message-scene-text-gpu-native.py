"""Offscreen Direct3D9 pixel reference for the shared TH14 renderer.

No game files are modified and no native window is shown. This is a device
test with material values previously recovered from the retail executable,
not a capture of the whole original game.
"""
import ctypes as C, hashlib, itertools, json, re, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/dialogue-real-message-scene-text';OUT.mkdir(parents=True,exist_ok=True)
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
    prepared_bytes=(OUT/'prepared.json').read_bytes();prepared=json.loads(prepared_bytes);assert prepared['prepared'];scratch=json.loads((OUT/'scratch.json').read_bytes());assert hashlib.sha256((OUT/'scratch.json').read_bytes()).hexdigest()==prepared['scratchProofSha256']
    d3dx=C.WinDLL('d3dx9_43');upload=d3dx.D3DXLoadSurfaceFromMemory;upload.restype=I;upload.argtypes=[P,P,P,P,U,U,P,P,U,U]
    pixels=bytearray();cases=[];textures=[];rows=[];loaded=None
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
        for row_index,row in enumerate(scratch['rows']):
            call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,None])
            for obj in textures:method(obj,'IDirect3DTexture9','Release',[])(obj)
            textures=[]
            for record in prepared['textures']:
                raw=(OUT/record['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==record['sha256'];texture=P();call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[record['width'],record['height'],1,0,record['format'],1,C.byref(texture),None]);textures.append(texture)
                call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
                for y in range(record['height']):C.memmove(lock.bits+y*lock.pitch,raw[y*record['pitch']:(y+1)*record['pitch']],record['pitch'])
                call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
            selected=sorted(set([0,*[len(row['frames'])*i//5 for i in range(1,5)],len(row['frames'])-1]));out_frames=[]
            for frame,source_frame in enumerate(row['frames']):
                writes=[]
                for write in source_frame['writes']:
                    raw=(OUT/write['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==write['sha256'];source=C.create_string_buffer(raw);d=write['upload'];surface=P();call(textures[0],'IDirect3DTexture9','GetSurfaceLevel',[U,C.POINTER(P)],[0,C.byref(surface)])
                    destination=Rect(*d['destination']);source_rect=Rect(*d['source']);hr=upload(surface,None,C.byref(destination),source,d['format'],d['pitch'],None,C.byref(source_rect),d['filter'],d['colorKey']);assert hr>=0,hex(hr&0xffffffff);method(surface,'IDirect3DSurface9','Release',[])(surface)
                    call(textures[0],'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,16]);copied=b''.join(C.string_at(lock.bits+y*lock.pitch,2048) for y in range(1024));call(textures[0],'IDirect3DTexture9','UnlockRect',[U],[0]);writes.append(dict(**write,textureSha256=hashlib.sha256(copied).hexdigest()))
                out_frames.append(dict(**{k:v for k,v in source_frame.items() if k!='writes'},writes=writes))
                if frame not in selected:continue
                selected_frame=dict(index=len(cases),row=row_index,input=row['input'],frame=frame,crop=[0,0,640,480],offset=len(pixels),size=640*480*4,draws=source_frame['draws'])
                call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0xff42678b,1,0])
                call(device,'IDirect3DDevice9','BeginScene',[],[])
                for draw in selected_frame['draws']:
                    handle,depth,src,dst,equation,min_filter,mag_filter,u,v=draw['material']
                    call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,textures[handle-1]])
                    for key,value in ((14,depth),(19,src),(20,dst),(171,equation)):rs(key,value)
                    for key,value in ((5,min_filter),(6,mag_filter),(1,u),(2,v)):sampler(key,value)
                    vertices=(Vertex*4)(*(Vertex(*v) for v in draw['vertices']))
                    call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,C.byref(vertices),C.sizeof(Vertex)])
                call(device,'IDirect3DDevice9','EndScene',[],[])
                call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback])
                call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
                left,top,width,height=selected_frame['crop'];raw=b''.join(C.string_at(lock.bits+y*lock.pitch+left*4,width*4) for y in range(top,top+height))
                call(readback,'IDirect3DSurface9','UnlockRect',[],[])
                cases.append(dict(**{k:v for k,v in selected_frame.items() if k!='draws'},drawCount=len(selected_frame['draws']),pixelsSha256=hashlib.sha256(raw).hexdigest()));pixels+=raw
            rows.append(dict(**{k:v for k,v in row.items() if k!='frames'},frames=out_frames))
        (OUT/'native.bgra').write_bytes(pixels)
        report=dict(generated=True,completeGame=False,nativeEquivalent=False,width=640,height=480,behaviorFlags=64,vertexProcessing='Hardware',preparedSha256=hashlib.sha256(prepared_bytes).hexdigest(),cases=cases,rows=rows,resourceHashes=prepared['resourceHashes'],textures=prepared['textures'],nativeExecutableSha256=scratch['executableSha256'],nativeD3dxSha256=scratch['d3dxSha256'],hostD3dxSha256=hashlib.sha256(Path('C:/Windows/System32/d3dx9_43.dll').read_bytes()).hexdigest(),d3d9Sha256=hashlib.sha256(Path('C:/Windows/System32/d3d9.dll').read_bytes()).hexdigest(),sdkHeaderSha256=hashlib.sha256(SDK.read_bytes()).hexdigest(),pixelsSha256=hashlib.sha256(pixels).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope=prepared['scope']+' Actual host64 D3DX uploads every41 MSG/GDI scratch delivery and hashes the complete1024square atlas after each write; selected six full640x480 screen frames per route use actual recorded full-scene vertices/materials and hidden HAL. Controlled screen alpha1/no fog/depth test; original32bitCOM/wholeworld/otherdrivers excluded.')
        (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(f'Generated {len(cases)} actual D3D9 raster fixtures ({len(pixels)} bytes)')
    finally:
        for obj in textures:method(obj,'IDirect3DTexture9','Release',[])(obj)
        for obj,interface in ((readback,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
            if obj.value:method(obj,interface,'Release',[])(obj)
        if window:user.DestroyWindow(window)

if __name__=='__main__':main()
