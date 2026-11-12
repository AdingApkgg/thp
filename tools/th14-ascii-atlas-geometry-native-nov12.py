"""Original real-ASCII constructor, queue, traversal, geometry, batch and draw-time states.

Texture creation and D3D methods are declared services. Camera screen-matrix
calculation is outside this screen-space vertex comparison; pixels are not captured.
"""
from pathlib import Path
import hashlib,importlib,itertools,json,struct,sys,traceback
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-atlas-geometry-nov12';O=H/'native';assert not O.exists();O.mkdir();sys.path.insert(0,str(R/'tools'));sha=lambda b:hashlib.sha256(b).hexdigest();im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert sha(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,n in im.sections:
 page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,im.data[off:off+n])
loader=importlib.import_module('th14-native-transition-resource-loader-nov09').install(m);B=0x78000000;SUP=B+0x10000;STACK=B+0xff000;STOP=B+0xfe000;DEVICE=B+0x60000;VTABLE=B+0x61000;REQUEST=B+0x50000;POSITION=B+0x51000;m.mem_map(B,0x100000)
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];events=[];device_states={};samplers={};stages={};texture_ids={};bound_texture=0;fvf=0;phase='';rows=[];error=''
def ret(value=0,argc=0):
 sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EIP,get(sp));m.reg_write(UC_X86_REG_ESP,sp+4+argc*4);m.reg_write(UC_X86_REG_EAX,value)
def run(entry,owner=0,args=()):
 m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),STOP,*args))
 for reg,val in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_ECX,owner),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,val)
 try:m.emu_start(entry,STOP,count=5000000)
 except Exception as exc:raise RuntimeError(f'pc={m.reg_read(UC_X86_REG_EIP):x} entry={entry:x} phase={phase}')from exc
 assert m.reg_read(UC_X86_REG_EIP)==STOP,hex(m.reg_read(UC_X86_REG_EIP))
 return m.reg_read(UC_X86_REG_EAX)
services={}
def service(uc,pc,size,unused):
 global bound_texture,fvf
 if pc==0x446250:ret(0,1);return # Declared camera-matrix helper; no screen vertex transform.
 name,argc=services[pc];sp=m.reg_read(UC_X86_REG_ESP);args=list(struct.unpack('<'+'I'*argc,m.mem_read(sp+4,argc*4)));assert args[0]==DEVICE
 if name=='SetRenderState':device_states[args[1]]=args[2]
 elif name=='SetSamplerState':assert args[1]==0;samplers[args[2]]=args[3]
 elif name=='SetTextureStageState':assert args[1]==0;stages[args[2]]=args[3]
 elif name=='SetTexture':assert args[1]==0 and args[2] in texture_ids;bound_texture=texture_ids[args[2]]
 elif name=='SetFVF':fvf=args[1]
 elif name=='DrawPrimitiveUP':
  topology,count,pointer,stride=args[1:];n=count*3 if topology==4 else count+2;assert 0<n<=4096 and stride==28
  events.append(dict(topology=topology,vertices=n,stride=stride,fvf=fvf,texture=bound_texture,renderStates=dict(device_states),samplers=dict(samplers),stages=dict(stages),verticesHex=bytes(m.mem_read(pointer,n*stride)).hex()))
 ret(0,argc)
for slot,name,argc in [(44,'SetTransform',3),(47,'SetViewport',2),(57,'SetRenderState',3),(65,'SetTexture',3),(67,'SetTextureStageState',4),(69,'SetSamplerState',4),(83,'DrawPrimitiveUP',5),(89,'SetFVF',2)]:
 address=B+0x70000+slot*16;services[address]=(name,argc);put(VTABLE+slot*4,address);m.hook_add(UC_HOOK_CODE,service,begin=address,end=address)
m.hook_add(UC_HOOK_CODE,service,begin=0x446250,end=0x446250);put(DEVICE,VTABLE);put(0x4d8f68,DEVICE)
meta=json.loads((R/'artifacts/archive-differential/th14.json').read_bytes());blob=(Path(meta['extraction'])/'ascii.anm').read_bytes();assert sha(blob)=='fc1c2295fda07140b475b2ddd45d221920534e4a011c529e76578609d69a9284'
try:
 for resolution,width,height in [(0,640,480),(1,960,720),(2,1280,960)]:
  phase=f'load ascii width={width}';m.mem_write(0x4f7a64,struct.pack('<2If',width,height,width/640.));m.mem_write(0x4f7a54,bytes([resolution]));resource=loader.load('ascii.anm',blob,2,1.);texture_ids={p:i+1 for i,p in enumerate(loader.context['textures'])}
  for font,(sx,sy),shadow,pass_index,(horizontal,vertical) in itertools.product(range(6),[(1.,1.),(.7,.3)],[False,True],[0,1,2],[(1,1),(0,0),(2,2)]):
   phase=f'width={width} font={font} scale={sx}/{sy} shadow={shadow} pass={pass_index} align={horizontal}/{vertical}'
   m.mem_write(SUP,bytes(0x1a000));put(0x4db520,SUP);put(SUP+0x191e4,resource.resource);put(SUP+0x191dc,9)
   m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EBX,SUP);m.reg_write(UC_X86_REG_EDI,resource.resource);m.emu_start(0x40b613,0x40b64a,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x40b64a
   assert get(SUP+0x14+0x2c)==resource.sprites
   run(0x4465e0,0x4d8f60);put(0x4d9640,0x4d93e8);put(loader.manager+0xd0,0);put(loader.manager+0xd4,0)
   start=loader.manager+0xbc81f4;put(loader.manager+0xf481f4,start);put(loader.manager+0xf481f8,start);put(loader.manager+0xbc81f0,0);m.mem_write(loader.manager+0xbc8188,bytes([255])*16)
   for i in range(4):put(0x4fd218+i*28+12,0x3f800000)
   device_states.clear();device_states.update({19:5,20:6,171:1,206:0,207:2,208:1,209:1,15:1});samplers.clear();samplers.update({1:1,2:1,5:2,6:2});stages.clear();stages.update({1:4,2:2,3:3,4:4,5:2,6:3,24:2});bound_texture=0;fvf=0;events.clear()
   requests=[dict(text='A. 1,2s',position=[16.25,28.5,-.125],font=font,scale=[sx,sy],shadow=shadow,color=0xa5345678,horizontal=horizontal,vertical=vertical),dict(text='0.9',position=[620.25,471.5,0.],font=(font+1)%6,scale=[.75,1.5],shadow=not shadow,color=0x803d7fbe,horizontal=1,vertical=1)]
   for request in requests:
    m.mem_write(REQUEST,request['text'].encode()+b'\0');m.mem_write(POSITION,struct.pack('<3f',*request['position']));m.mem_write(SUP+0x191b4,struct.pack('<2f',*request['scale']))
    for off,value in [(0x191b0,request['color']),(0x191c8,request['font']),(0x191c4,int(request['shadow'])),(0x191cc,pass_index),(0x191d4,request['horizontal']),(0x191d8,request['vertical'])]:put(SUP+off,value)
    run(0x40b9b0,SUP,(POSITION,REQUEST))
   assert get(SUP+0x191ac)==2
   result=run(0x40b920 if pass_index==2 else 0x40be30,SUP,() if pass_index==2 else(pass_index,));assert result==1
   rows.append(dict(width=width,height=height,resolution=resolution,font=font,scale=[sx,sy],shadow=shadow,passIndex=pass_index,horizontal=horizontal,vertical=vertical,requests=requests,draws=list(events)))
except Exception:
 error=traceback.format_exc();(O/'exception.txt').write_text(error)
report=dict(executableSha256=sha(im.data),asciiSha256=sha(blob),cases=len(rows),rows=rows,error=error,phase=phase,actualOriginalResourceLoader=True,actualOriginalAsciiVmInitializationAndBinding=True,actualOriginalQueueTraversalGeometryAndBatchFlush=True,opaqueTextureIdsDeclaredByLoaderOrdinal=True,cameraMatrixHelperAndD3dServicesDeclared=True,drawTimeVerticesAndStatesRecorded=True,noGpuPixels=True,newGameRuns=0,newGpuRuns=0,completeGame=False,toolSha256=sha(Path(__file__).read_bytes()))
(O/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}));raise SystemExit(1 if error else 0)
