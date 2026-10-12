"""Retail STD14 layer assignment and complete layer traversal with standalone VMs."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-standalone';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 Image=importlib.import_module('th12-pe').Image;img=Image('H:/Games/th/14/th14.exe');dll=Image('C:/Windows/SysWOW64/d3dx9_43.dll')
 assert sha(img.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for image in (img,dll):
  for _,b,size,raw,n in image.sections:
   first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,image.data[raw:raw+n])
 base=0x70000000;stop=base;stage=base+0x1000;code=base+0x7000;instances=base+0x8000;sprite=base+0x9000;device=base+0xa000;table=base+0xb000;stack=base+0xff000;manager=0x71000000;camera=0x4d9514
 m.mem_map(base,0x100000);m.mem_map(manager,0x1000000);m.mem_map(0,4096)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 def run(entry,args=(),ecx=0):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),stop,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(entry,stop,count=300000);assert m.reg_read(UC_X86_REG_EIP)==stop,hex(m.reg_read(UC_X86_REG_EIP))
 m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,(0x101ca068,))
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];export=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0];functions,names,ordinals=[dll.image_base+dll.u32(export+x) for x in (28,32,36)];exports={}
 for i in range(dll.u32(export+24)):
  name=dll.cstring(dll.image_base+dll.u32(names+i*4),128);ordinal=struct.unpack('<H',dll.read(ordinals+i*2,2))[0];exports[name]=dll.image_base+dll.u32(functions+ordinal*4)
 pe=struct.unpack_from('<I',img.data,0x3c)[0];directory=img.image_base+struct.unpack_from('<I',img.data,pe+0x80)[0]
 while img.u32(directory+12):
  lookup=img.image_base+img.u32(directory);iat=img.image_base+img.u32(directory+16);index=0
  while img.u32(lookup+index*4):
   hint=img.u32(lookup+index*4);address=iat+index*4;index+=1
   if hint&0x80000000:continue
   name=img.cstring(img.image_base+hint+2)
   if name in exports:put(address,exports[name])
  directory+=20
 states={};draws=[];events=[];camera_mode=[0];animation_events=[]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==stop+0x100:key,value=get(sp+8),get(sp+12);states[key]=value;events.append([key,value])
  elif a==0x478f60:draws.append([(get(sp+4)-stage-0x20c)//0x5cc,states[14],states[28],camera_mode[0]])
  elif a==0x4461e0:camera_mode[0]=1
  elif a==0x446400:camera_mode[0]=0
  elif a==0x40af00:animation_events.append([(get(sp+4)-stage-0x20c)//0x5cc,get(sp+8)])
  elif a==0x4854af:uc.reg_write(UC_X86_REG_EAX,0)
 for offset,address,cleanup in [(0xe4,stop+0x100,12),(0xb0,stop+0x110,12),(0xbc,stop+0x120,8)]:put(table+offset,address);m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 for a,cleanup in [(0x475eb0,0),(0x4854a0,0),(0x40af00,8),(0x46fe50,0),(0x40f610,4),(0x4854af,0)]:m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
 for a in (0x478f60,0x4461e0,0x446400,0x40af00,0x4854af):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(device,table);put(0x4d8f68,device);put(0x4f56cc,manager);floats(0x4d8f58,[1]);m.mem_write(instances,b'\xff\xff');floats(sprite+0x34,[48,32]);put(0x4f7a6c,1)
 rows=[];scripts=[]
 for slot,script,layer in itertools.product(range(8),(-1,7),range(12)):
  m.mem_write(stage,bytes(0x4500));m.mem_write(code,struct.pack('<ihh3iihh',0,14,20,slot,script,layer,0,0,8));put(stage+0x1c,code);put(stage+0x4c,code);put(stage+0x38,-1);put(stage+0x44,0x4d8f58);put(stage+0x48,1);floats(stage+0x4274,[0,0,-600,0,300,600,0,1,0]);floats(stage+0x42c8,[.5235987901687622]);put(stage+0x20c+slot*0x5cc+0x18,1);animation_events.clear();run(0x40f670,(),stage)
  scripts.append(dict(input=[slot,script,layer],layers=[get(stage+0x306c+i*4) for i in range(8)],renderEnabled=bool(get(stage+0x20c+slot*0x5cc+0x18)&1),events=animation_events.copy()))
 for layer,initial_depth,initial_fog,mask,pattern in itertools.product(range(12),range(2),range(2),(0,1,2,0x55,0xaa,0xff),range(3)):
  m.mem_write(stage,bytes(0x4500));m.mem_write(camera,bytes(0x12c));floats(camera,[0,0,-600,0,0,1,0,1,0,0,0,1]);floats(camera+0x54,[.5235987901687622]);m.mem_write(camera+0xe0,struct.pack('<4I2f',116,4,408,472,0,1));put(stage+0x18,instances)
  for i in range(8):
   assigned=layer if pattern==0 else i if pattern==1 else (layer+i)%12;put(stage+0x306c+i*4,assigned);put(stage+0x20c+i*0x5cc+0x2c,sprite if mask&(1<<i) else 0)
  put(0x4d9964,initial_depth);put(0x4d9960,initial_fog);states.clear();states.update({14:initial_depth,28:initial_fog});draws.clear();events.clear();camera_mode[0]=0;run(0x40f2f0,(layer,),stage)
  rows.append(dict(input=[layer,initial_depth,initial_fog,mask,pattern],draws=draws.copy(),finalDepth=states[14],finalFog=states[28],finalCameraMode=camera_mode[0],status=m.reg_read(UC_X86_REG_EAX)))
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text(encoding='utf-8'));resources=[]
 for number in range(1,8):
  name=f'st0{number}.std';data=(Path(archive['extraction'])/name).read_bytes();assert sha(data)==next(r['sha256'] for r in archive['decoded'] if r['name']==name);offset=struct.unpack_from('<I',data,8)[0];commands=[]
  while offset+8<=len(data):
   time,op,length=struct.unpack_from('<ihh',data,offset)
   if time<0 or length<8:break
   if op==14:commands.append(dict(time=time,offset=offset,arguments=list(struct.unpack_from('<'+'i'*((length-8)//4),data,offset+8))))
   offset+=length
  resource=dict(name=name,sha256=sha(data),commands=commands)
  if number in (3,6):
   frames=3600 if number==3 else 10800;m.mem_write(stage,bytes(0x4500));m.mem_write(code,data[struct.unpack_from('<I',data,8)[0]:]);put(stage+0x1c,code);put(stage+0x4c,code);put(stage+0x38,-1);put(stage+0x44,0x4d8f58);put(stage+0x48,1);floats(stage+0x4274,[0,0,-600,0,300,600,0,1,0]);floats(stage+0x42c8,[.5235987901687622]);timeline=[]
   for frame in range(frames):
    animation_events.clear();run(0x40f670,(),stage);timeline.append(dict(layers=[get(stage+0x306c+i*4) for i in range(8)],scriptTime=get(stage+0x3c),instructionOffset=get(stage+0x4c)-code,events=animation_events.copy()))
   resource['timeline']=timeline
  resources.append(resource)
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,executableSha256=sha(img.data),dllSha256=sha(dll.data),toolSha256=sha(Path(__file__).read_bytes()),scriptFunctionSha256=sha(img.read(0x40f670,0xd7c)),layerFunctionSha256=sha(img.read(0x40f2f0,0x316)),standaloneFunctionSha256=sha(img.read(0x4107b0,0x173)),scripts=scripts,rows=rows,resources=resources,scope='Original STD interpreter14 third-argument assignment with animation setup/update controlled; complete40f2f0 and4107b0 using all eight embedded slots, invisible original478f60 and real32 D3DX camera setup. Empty object list, no visible geometry/callback/GPU/world/audio proof.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS',len(scripts),'STD14 assignments',len(rows),'whole-layer standalone cases')
if __name__=='__main__':main()
