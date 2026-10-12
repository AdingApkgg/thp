"""Actual hidden D3D9 HAL upload/draw of retail text scratch images.

Uses the host 64-bit D3DX9_43 API counterpart with exact captured upload
descriptors, not an execution of the original 32-bit COM/upload draw loop.
"""
import ctypes as C, hashlib, json, re, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/font-alignment-gpu';OUT.mkdir(parents=True,exist_ok=True)
SDK=Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h')
P=C.c_void_p;U=C.c_uint32;I=C.c_int32;F=C.c_float
class Present(C.Structure):
 _fields_=[(n,U) for n in ('width','height','format','count','multisample','quality','swap')]+[('window',P),('windowed',I),('depth',I)]+[(n,U) for n in ('depth_format','flags','refresh','interval')]
class Lock(C.Structure):_fields_=[('pitch',I),('bits',P)]
class Rect(C.Structure):_fields_=[(n,I) for n in ('left','top','right','bottom')]
class Viewport(C.Structure):_fields_=[(n,U) for n in ('x','y','width','height')]+[('min',F),('max',F)]
class Vertex(C.Structure):_fields_=[(n,F) for n in ('x','y','z','rhw')]+[('color',U)]+[(n,F) for n in ('u','v')]
def main():
 tables={};header=SDK.read_text(encoding='utf8')
 for name in ('IDirect3D9','IDirect3DDevice9','IDirect3DSurface9','IDirect3DTexture9'):
  body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
  methods=[a.strip() or b.strip() for a,b in re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body)]
  tables[name]={m:i for i,m in enumerate(methods)}
 def method(obj,interface,name,signature):return C.WINFUNCTYPE(I,P,*signature)(C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]])
 def call(obj,interface,name,types,values):
  result=method(obj,interface,name,types)(obj,*values);assert result>=0,(name,hex(result&0xffffffff));return result
 user=C.WinDLL('user32');user.CreateWindowExW.restype=P;user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P];user.DestroyWindow.argtypes=[P]
 dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
 d3dx=C.WinDLL('d3dx9_43');upload=d3dx.D3DXLoadSurfaceFromMemory;upload.restype=I;upload.argtypes=[P,P,P,P,U,U,P,P,U,U]
 proof_path=ROOT/'artifacts/th14/font-alignment-native.json';proof=json.loads(proof_path.read_text());assert len(proof['rows'])==240
 device=P();d3d=P();rt=P();readback=P();texture=P();surface=P();window=None;pixels=bytearray();texture_bytes=bytearray();cases=[];copies=[]
 try:
  window=user.CreateWindowExW(0,'STATIC','TH14 text upload fixture',0,0,0,64,64,None,None,None,None);assert window
  d3d=P(dll.Direct3DCreate9(32));assert d3d;pp=Present(640,96,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
  call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,64,C.byref(pp),C.byref(device)])
  call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[640,96,21,0,0,0,C.byref(rt),None])
  call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[640,96,21,2,C.byref(readback),None])
  call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[None]);vp=Viewport(0,0,640,96,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
  rs=lambda k,v:call(device,'IDirect3DDevice9','SetRenderState',[U,U],[k,v]);sampler=lambda k,v:call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,v])
  for k,v in ((7,0),(14,0),(15,1),(22,1),(27,1),(28,0),(137,0),(161,0),(168,15),(194,0),(206,0),(24,1),(25,7),(19,5),(20,6),(171,1)):rs(k,v)
  call(device,'IDirect3DDevice9','SetFVF',[U],[0x144])
  for k,v in ((1,4),(2,2),(3,0),(4,4),(5,2),(6,0)):call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[0,k,v])
  call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[1,1,1]);sampler(1,3);sampler(2,3);sampler(11,0)
  for text_index,row in enumerate(proof['rows']):
   raw=(ROOT/row['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];source=C.create_string_buffer(raw)
   d=row['upload'];assert d==dict(destination=[0,0,512,32],source=[0,0,512,32],format=26,pitch=2048,filter=1,colorKey=0)
   for fmt in (26,21):
    bpp=2 if fmt==26 else 4
    call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[520,40,1,0,fmt,1,C.byref(texture),None])
    lock=Lock();call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
    for y in range(40):C.memset(lock.bits+y*lock.pitch,0xa5,520*bpp)
    call(texture,'IDirect3DTexture9','UnlockRect',[U],[0]);call(texture,'IDirect3DTexture9','GetSurfaceLevel',[U,C.POINTER(P)],[0,C.byref(surface)])
    destination=Rect(*d['destination']);source_rect=Rect(*d['source']);hr=upload(surface,None,C.byref(destination),source,d['format'],d['pitch'],None,C.byref(source_rect),d['filter'],d['colorKey']);assert hr>=0,hex(hr&0xffffffff)
    call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,16]);copied=b''.join(C.string_at(lock.bits+y*lock.pitch,520*bpp) for y in range(40));call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
    copies.append(dict(textIndex=text_index,format=fmt,offset=len(texture_bytes),size=len(copied),sha256=hashlib.sha256(copied).hexdigest()));texture_bytes+=copied
    call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,texture])
    for filtering in (0,1):
     sampler(5,filtering+1);sampler(6,filtering+1)
     for scaling in (0,1):
      scale=1 if scaling==0 else .5;left=4 if scaling==0 else 4.375;top=3 if scaling==0 else 3.375;width=512*scale;height=32*scale;crop=[0,0,520 if scaling==0 else 264,40 if scaling==0 else 24]
      vertices=(Vertex*4)(Vertex(left,top,0,1,0xffffffff,0,0),Vertex(left+width,top,0,1,0xffffffff,512/520,0),Vertex(left,top+height,0,1,0xffffffff,0,32/40),Vertex(left+width,top+height,0,1,0xffffffff,512/520,32/40))
      call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0xff42678b,1,0]);call(device,'IDirect3DDevice9','BeginScene',[],[]);call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,C.byref(vertices),28]);call(device,'IDirect3DDevice9','EndScene',[],[])
      call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback]);call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16]);image=b''.join(C.string_at(lock.bits+y*lock.pitch,crop[2]*4) for y in range(crop[3]));call(readback,'IDirect3DSurface9','UnlockRect',[],[])
      foreground=sum(image[i:i+4]!=bytes((139,103,66,255)) for i in range(0,len(image),4))
      cases.append(dict(index=len(cases),textIndex=text_index,format=fmt,filter=filtering,scaling=scaling,crop=crop,offset=len(pixels),size=len(image),foregroundPixels=foreground,pixelsSha256=hashlib.sha256(image).hexdigest()));pixels+=image
    method(surface,'IDirect3DSurface9','Release',[])(surface);surface=P();method(texture,'IDirect3DTexture9','Release',[])(texture);texture=P()
  (OUT/'native.bgra').write_bytes(pixels);(OUT/'native-textures.bin').write_bytes(texture_bytes)
  report=dict(generated=True,completeGame=False,nativeEquivalent=False,cases=cases,copies=copies,rows=proof['rows'],width=640,height=96,behaviorFlags=64,nativeExecutableSha256=proof['executableSha256'],scratchProofSha256=hashlib.sha256(proof_path.read_bytes()).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sdkHeaderSha256=hashlib.sha256(SDK.read_bytes()).hexdigest(),d3d9Sha256=hashlib.sha256(Path('C:/Windows/System32/d3d9.dll').read_bytes()).hexdigest(),d3dxSha256=hashlib.sha256(Path('C:/Windows/System32/d3dx9_43.dll').read_bytes()).hexdigest(),pixelsSha256=hashlib.sha256(pixels).hexdigest(),texturesSha256=hashlib.sha256(texture_bytes).hexdigest(),scope='Actual HAL HardwareVP and host64 D3DX9_43 upload of240 complete retail alignment-wrapper/raster scratch images using exact captured filter1 descriptors;480 ARGB4444/BGRA8 texture readbacks with untouched borders and1920 controlled point/linear,1x/half-scale alpha-blended draws. Original32-bit upload/full draw loop, actual dialogue textures/frames, other machines and Unicode localization excluded.')
  (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(f'Generated {len(cases)} text GPU scenes and {len(copies)} real D3DX texture copies')
 finally:
  for obj,interface in ((surface,'IDirect3DSurface9'),(texture,'IDirect3DTexture9'),(readback,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
   if obj.value:method(obj,interface,'Release',[])(obj)
  if window:user.DestroyWindow(window)
if __name__=='__main__':main()
