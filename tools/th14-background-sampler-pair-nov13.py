"""Independent D3D9/ANGLE sampling at identical measured type0 UV phases.

Authored full-screen geometry and texture-only shaders isolate the sampler;
this is not the retail draw loop or the production Renderer class.
"""
from pathlib import Path
import ctypes as C,hashlib,importlib.util,json,re,struct,sys
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/background-sampler-pair-nov13'
assert not O.exists();O.mkdir();sys.path.insert(0,str(R/'tools'))
sha=lambda b:hashlib.sha256(b).hexdigest();load=lambda p:json.loads(p.read_bytes())
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
t=module('d3d_types',R/'tools/th14-gpu-raster-native.py');g=module('gles_types',R/'tools/th14-native-gles-context.py')
P,U,I,F=t.P,t.U,t.I,t.F
archive=load(R/'artifacts/archive-differential/th14.json');effect=Path(archive['extraction'])/'effect.anm'
assert sha(effect.read_bytes())==next(x['sha256']for x in archive['decoded']if x['name']=='effect.anm')
chunks=__import__('th-anm-texture-table').chunks
for _,chunk in chunks(effect.read_bytes()):
 at=struct.unpack_from('<I',chunk,16)[0]
 if chunk[at:chunk.index(b'\0',at)]==b'effect/eff_switchbg.png':
  at=struct.unpack_from('<I',chunk,28)[0];fmt,w,h,n=struct.unpack_from('<HHHI',chunk,at+6)
  assert(fmt,w,h,n)==(5,256,256,131072);texture_bytes=chunk[at+16:at+16+n];break
else:raise AssertionError('Missing source texture')
phase=load(R/'artifacts/th14/compositor-filter-nov13/background-uv-phase-qualified.json')
phases={'native':phase['rows'][0]['nativeTargetUvWords'][0],**{x['name']:x['inputUvWords'][0]for x in phase['rows']}}
header=t.SDK.read_text(encoding='utf8');tables={}
for name in ['IDirect3D9','IDirect3DDevice9','IDirect3DTexture9','IDirect3DSurface9']:
 body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
 tables[name]={a.strip()or b.strip():i for i,(a,b)in enumerate(re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body))}
def method(obj,interface,name,sig):return C.WINFUNCTYPE(I,P,*sig)(C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]])
def call(obj,interface,name,sig,values):
 hr=method(obj,interface,name,sig)(obj,*values);assert hr>=0,(name,hex(hr&0xffffffff))
device=P();d3d=P();target=P();readback=P();texture=P();window=None;egl=None;program=buffer=vao=gltexture=0
user=C.WinDLL('user32');user.CreateWindowExW.restype=P;user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P];user.DestroyWindow.argtypes=[P]
def gl(name,result,*sig):return g.fn(egl.gles,name,result,*sig)
rows=[]
try:
 window=user.CreateWindowExW(0,'STATIC','TH14 isolated sampler',0,0,0,16,16,None,None,None,None);assert window
 dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;d3d=P(dll.Direct3DCreate9(32));assert d3d
 pp=t.Present(640,480,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
 call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x20,C.byref(pp),C.byref(device)])
 call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[640,480,21,0,0,0,C.byref(target),None])
 call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[640,480,21,2,C.byref(readback),None])
 call(device,'IDirect3DDevice9','CreateTexture',[U,U,U,U,U,U,C.POINTER(P),P],[256,256,1,0,26,1,C.byref(texture),None])
 lock=t.Lock();call(texture,'IDirect3DTexture9','LockRect',[U,P,P,U],[0,C.byref(lock),None,0])
 for y in range(256):C.memmove(lock.bits+y*lock.pitch,texture_bytes[y*512:(y+1)*512],512)
 call(texture,'IDirect3DTexture9','UnlockRect',[U],[0])
 call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,target]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[None])
 vp=t.Viewport(0,0,640,480,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
 call(device,'IDirect3DDevice9','SetFVF',[U],[0x144]);call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,texture])
 for k,v in [(7,0),(14,0),(15,0),(22,1),(27,0),(28,0),(137,0),(161,0),(168,15),(194,0),(206,0)]:call(device,'IDirect3DDevice9','SetRenderState',[U,U],[k,v])
 for stage,k,v in [(0,1,2),(0,2,2),(0,4,2),(0,5,2),(1,1,1)]:call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[stage,k,v])
 for k,v in [(1,1),(2,1),(7,0)]:call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,v])
 egl=g.Context('C:/Users/APKGG/AppData/Local/Programs/Trae')
 def shader(kind,source):
  handle=gl('glCreateShader',U,U)(kind);s=C.c_char_p(source.encode());gl('glShaderSource',None,U,I,C.POINTER(C.c_char_p),P)(handle,1,C.byref(s),None);gl('glCompileShader',None,U)(handle);ok=I();gl('glGetShaderiv',None,U,U,C.POINTER(I))(handle,0x8b81,C.byref(ok));assert ok.value;return handle
 vs=shader(0x8b31,'#version 300 es\nprecision highp float;layout(location=0)in vec4 p;layout(location=1)in vec2 uv;out vec2 v;void main(){vec2 xy=(p.xy+vec2(.5))/vec2(640,480);gl_Position=vec4(xy*2.-1.,p.z*2.-1.,1.)/p.w;v=uv;}')
 fs=shader(0x8b30,'#version 300 es\nprecision highp float;uniform sampler2D image;in vec2 v;out vec4 color;void main(){color=texture(image,v);}')
 program=gl('glCreateProgram',U)()
 for s in [vs,fs]:gl('glAttachShader',None,U,U)(program,s)
 gl('glLinkProgram',None,U)(program);ok=I();gl('glGetProgramiv',None,U,U,C.POINTER(I))(program,0x8b82,C.byref(ok));assert ok.value
 for s in [vs,fs]:gl('glDeleteShader',None,U)(s)
 gl('glUseProgram',None,U)(program);handle=U();gl('glGenVertexArrays',None,I,C.POINTER(U))(1,C.byref(handle));vao=handle.value;gl('glBindVertexArray',None,U)(vao)
 gl('glGenBuffers',None,I,C.POINTER(U))(1,C.byref(handle));buffer=handle.value;gl('glBindBuffer',None,U,U)(0x8892,buffer)
 for loc,count,offset in [(0,4,0),(1,2,20)]:gl('glEnableVertexAttribArray',None,U)(loc);gl('glVertexAttribPointer',None,U,I,U,U,I,P)(loc,count,0x1406,0,28,offset)
 gl('glGenTextures',None,I,C.POINTER(U))(1,C.byref(handle));gltexture=handle.value;gl('glBindTexture',None,U,U)(0x0de1,gltexture)
 packed=b''.join(struct.pack('<H',((v<<4)|(v>>12))&0xffff)for(v,)in struct.iter_unpack('<H',texture_bytes));pixels=C.create_string_buffer(packed)
 gl('glTexImage2D',None,U,I,I,I,I,I,U,U,P)(0xde1,0,0x8056,256,256,0,0x1908,0x8033,pixels)
 for k in [0x2802,0x2803]:gl('glTexParameteri',None,U,U,I)(0xde1,k,0x2901)
 for cap in [0x0be2,0x0b71,0x0b44,0x0bd0,0x0c11]:gl('glDisable',None,U)(cap)
 gl('glViewport',None,I,I,I,I)(0,0,640,480)
 for name,bits in phases.items():
  uv=struct.unpack('<f',struct.pack('<I',bits))[0]
  vertices=b''.join(struct.pack('<4fI2f',x,y,0,1,0xffffffff,u,v)for x,y,u,v in [(-.5,-.5,uv,uv),(639.5,-.5,uv+5,uv),(-.5,479.5,uv,uv+3.75),(639.5,479.5,uv+5,uv+3.75)])
  for point in [True,False]:
   for k in [5,6]:call(device,'IDirect3DDevice9','SetSamplerState',[U,U,U],[0,k,1 if point else 2])
   call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0,1,0]);data=C.create_string_buffer(vertices)
   call(device,'IDirect3DDevice9','BeginScene',[],[]);call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,data,28]);call(device,'IDirect3DDevice9','EndScene',[],[])
   call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[target,readback]);call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16]);native=b''.join(C.string_at(lock.bits+y*lock.pitch,2560)for y in range(480));call(readback,'IDirect3DSurface9','UnlockRect',[],[])
   for k in [0x2800,0x2801]:gl('glTexParameteri',None,U,U,I)(0xde1,k,0x2600 if point else 0x2601)
   gl('glBufferData',None,U,C.c_ssize_t,P,U)(0x8892,len(vertices),data,0x88e0);gl('glDrawArrays',None,U,I,I)(5,0,4)
   out=C.create_string_buffer(640*480*4);gl('glReadPixels',None,I,I,I,I,U,U,P)(0,0,640,480,0x1908,0x1401,out);assert gl('glGetError',U)()==0
   rgba=out.raw;angle=bytearray(rgba);angle[0::4]=rgba[2::4];angle[2::4]=rgba[0::4];angle=bytes(angle)
   stem=name+('-point'if point else'-linear');(O/(stem+'-native.bgra')).write_bytes(native);(O/(stem+'-angle.bgra')).write_bytes(angle)
   diff=sum(native[i:i+4]!=angle[i:i+4]for i in range(0,len(native),4));row=dict(name=name,uvWord=bits,point=point,differentPixels=diff,nativeSha256=sha(native),angleSha256=sha(angle),vertexSha256=sha(vertices));rows.append(row);print(json.dumps(row),flush=True)
finally:
 if egl:
  if gltexture:gl('glDeleteTextures',None,I,C.POINTER(U))(1,C.byref(U(gltexture)))
  if buffer:gl('glDeleteBuffers',None,I,C.POINTER(U))(1,C.byref(U(buffer)))
  if vao:gl('glDeleteVertexArrays',None,I,C.POINTER(U))(1,C.byref(U(vao)))
  if program:gl('glDeleteProgram',None,U)(program)
  info=egl.info;egl.close()
 for obj,interface in [(texture,'IDirect3DTexture9'),(readback,'IDirect3DSurface9'),(target,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')]:
  if obj.value:method(obj,interface,'Release',[])(obj)
 if window:assert user.DestroyWindow(window)
report=dict(rows=rows,cases=len(rows),actualD3d9HalAndAngleD3d11=True,authoredScreenQuadAndTextureOnlyShader=True,
             textureSha256=sha(texture_bytes),nativeGameOrProductionRendererAccepted=False,allContextsClosed=True,
             audibleOutput=False,angle=info,d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),completeGame=False)
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n')
