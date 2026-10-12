"""Whole original stage culling and pinned 32-bit D3DX; assets read-only."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/stage-visibility';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
def main():
 Image=importlib.import_module('th12-pe').Image
 image=Image('H:/Games/th/14/th14.exe');dll=Image('C:/Windows/SysWOW64/d3dx9_43.dll')
 assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 assert sha(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for img in (image,dll):
  for _,b,size,raw,n in img.sections:
   first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;stop=base;stack=base+0xff000;camera=base+0x1000;obj=base+0x2000;pos=base+0x3000;device=base+0x4000;table=base+0x5000
 m.mem_map(base,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 values=lambda p,n:list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
 def run(entry,args=(),ecx=0,maximum=9610000):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),stop,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx)
  m.reg_write(UC_X86_REG_XMM2,struct.unpack('<I',struct.pack('<f',maximum))[0]);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(entry,stop,count=200000);assert m.reg_read(UC_X86_REG_EIP)==stop,hex(m.reg_read(UC_X86_REG_EIP))
 m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,(0x101ca068,))
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];directory=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0]
 functions,names,ordinals=[dll.image_base+dll.u32(directory+x) for x in (28,32,36)];exports={}
 for i in range(dll.u32(directory+24)):
  name=dll.cstring(dll.image_base+dll.u32(names+i*4),128);ordinal=struct.unpack('<H',dll.read(ordinals+i*2,2))[0];exports[name]=dll.image_base+dll.u32(functions+ordinal*4)
 for slot,name in [(0x4b12d0,'D3DXMatrixTranslation'),(0x4b12f4,'D3DXVec3ProjectArray'),(0x4b12ec,'D3DXMatrixLookAtLH'),(0x4b12e8,'D3DXMatrixPerspectiveFovLH'),(0x4b12b8,'D3DXVec3Normalize')]:put(slot,exports[name])
 # COM SetTransform and stack cookie only: real camera and projection bodies run.
 put(device,table);put(table+0xb0,stop+0x100);m.mem_write(stop+0x100,b'\xc2\x0c\x00');put(0x4d8f68,device);put(0x4f56cc,0)
 m.mem_write(0x4854a0,b'\xc3');put(0x4f7a70,32);put(0x4f7a74,16)
 projection_calls=[]
 def observe(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);count=get(sp+36);src=get(sp+12);stride=get(sp+16)
  projection_calls.append(dict(count=count,points=[values(src+i*stride,3) for i in range(count)]));observe.output=get(sp+4);observe.stride=get(sp+8)
 def after_project(uc,a,n,u):projection_calls[-1]['projected']=[values(observe.output+i*observe.stride,3) for i in range(projection_calls[-1]['count'])]
 m.hook_add(UC_HOOK_CODE,observe,begin=exports['D3DXVec3ProjectArray'],end=exports['D3DXVec3ProjectArray'])
 m.hook_add(UC_HOOK_CODE,after_project,begin=0x40ef1e,end=0x40ef1e)
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text(encoding='utf-8'))
 timeline_path=ROOT/'artifacts/th14/stage-native.json';timeline=json.loads(timeline_path.read_text(encoding='utf-8'));rows=[];resources={}
 def sample(label,position,size,instance,maximum=9610000):
  floats(obj+4,position+size);floats(pos,instance);projection_calls.clear();run(0x40ebc0,(pos,camera),obj,maximum)
  rows.append(dict(label=label,position=position,size=size,instance=instance,maximum=maximum,cameraPosition=values(camera,3),eyeOffset=values(camera+0x3c,3),view=values(camera+0x60,16),projection=values(camera+0xa0,16),viewport=list(struct.unpack('<4I2f',m.mem_read(camera+0xe0,24))),visible=1-m.reg_read(UC_X86_REG_EAX),projectedInputs=projection_calls.copy()))
 identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
 m.mem_write(camera,bytes(0x12c));floats(camera+0x60,identity);floats(camera+0xa0,identity);m.mem_write(camera+0xe0,struct.pack('<4I2f',24,8,400,464,0,1))
 for x in (-2,-1.04,-1,-.98,-.5,0,.5,.98,1,1.04,2):
  for y in (-2,-1,0,1,2):
   for z in (-.5,0,.25,.75,1,1.5):sample(['identity',x,y,z],[x,y,z],[.25,.5,.75],[.125,-.125,.0625])
 for x in (-.75,0,.75):
  for y in (-.75,0,.75):sample(['near-plane',x,y],[x,y,0],[0,0,0],[0,0,0])
 # Independent rounded distance thresholds; geometry remains on-screen.
 distance_projection=identity.copy();distance_projection[0]=distance_projection[5]=distance_projection[10]=1/4096
 floats(camera+0xa0,distance_projection)
 for i in range(64):
  point=[f32(713.125+i*17.331),f32(123.875+i*11.717),f32(523.625+i*13.129)]
  squared=f32(f32(f32(point[1]*point[1])+f32(point[0]*point[0]))+f32(point[2]*point[2]));word=struct.unpack('<I',struct.pack('<f',squared))[0]
  for delta in (-1,0,1):sample(['distance',i,delta],point,[1,1,1],[0,0,0],struct.unpack('<f',struct.pack('<I',word+delta))[0])
 for stage in range(1,8):
  name=f'st{stage:02}.std';raw=(Path(archive['extraction'])/name).read_bytes();expected=next(e['sha256'] for e in archive['decoded'] if e['name']==name);assert sha(raw)==expected;resources[name]=expected
  count=struct.unpack_from('<h',raw)[0];objects=[]
  for i in range(count):
   at=struct.unpack_from('<I',raw,0x90+i*4)[0];objects.append(list(struct.unpack_from('<6f',raw,at+4)))
  instances=[];at=struct.unpack_from('<I',raw,4)[0]
  while struct.unpack_from('<h',raw,at)[0]>=0:
   number=struct.unpack_from('<h',raw,at)[0];instances.append((number,list(struct.unpack_from('<3f',raw,at+4))));at+=16
  row=next(r for r in timeline['rows'] if r['name']==name and r['rate']==1)
  for frame in sorted(set(range(0,1200,10))|{1,599,1199}):
   for viewport_mode,viewport in enumerate(((24,8,400,464),(116,4,408,472))):
    state=row['timeline'][frame]['values'];m.mem_write(camera,bytes(0x12c));floats(camera,state[:9]);floats(camera+0x3c,state[9:12]);floats(camera+0x54,[state[18]])
    # Controlled current direction + target offset, not a native full-update claim.
    vector=base+0x6000;floats(vector,[f32(state[3+i]+state[12+i]) for i in range(3)]);run(exports['D3DXVec3Normalize'],(camera+0x24,vector))
    m.mem_write(camera+0xe0,struct.pack('<4I2f',*viewport,0,1));run(0x446400,(camera,))
    for instance,(number,position) in enumerate(instances):sample([stage,frame,instance,number,viewport_mode],objects[number][:3],objects[number][3:],position)
 viewport_path=ROOT/'artifacts/th14/compositor-native.json';viewport_proof=json.loads(viewport_path.read_text(encoding='utf-8'));assert viewport_proof['executableSha256']==sha(image.data);assert viewport_proof['cameras'][0]['viewports'][3]==[116,4,408,472,0,1]
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,entry='0x40ebc0',executableSha256=sha(image.data),dllSha256=sha(dll.data),functionSha256=sha(image.read(0x40ebc0,0x461)),timelineSha256=sha(timeline_path.read_bytes()),viewportProofSha256=sha(viewport_path.read_bytes()),resources=resources,rows=rows,toolSha256=sha(Path(__file__).read_bytes()),scope='Whole original stage bounding-box distance/projection/culling function with actual pinned32 D3DX Translation/ProjectArray; original seven STD object/instance records at123 controlled camera samples through frame1199, both independent400x464 and original reset640-display world408x472 viewports,330 identity controls,9 exact near-plane controls and192 independent float32 distance thresholds. Camera setup calls original446400 with actual D3DX; normalized current direction plus target offset controlled before camera setup. Matrices are identical inputs to both culling implementations. No complete native Stage update/draw or camera publication timing, GPU/world/audio equivalence claim.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS original stage visibility',len(rows),'cases',len(resources),'STD resources')
if __name__=='__main__':main()
