"""Whole original40f2f0 with real invisible Ribbon8 callbacks and cache divergence."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-asset-render';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 Image=importlib.import_module('th12-pe').Image;image=Image('H:/Games/th/14/th14.exe');dll=Image('C:/Windows/SysWOW64/d3dx9_43.dll')
 assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353';assert sha(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for img in (image,dll):
  for _,b,size,raw,n in img.sections:
   first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;stop=base;stack=base+0xff000;stage=base+0x1000;directory=base+0x6000;instances=base+0x7000;vms=base+0x10000;sprite=base+0xa000;device=base+0xb000;table=base+0xc000;manager=0x71000000;camera=0x4d9514
 m.mem_map(base,0x100000);m.mem_map(manager,0x1000000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));values=lambda p,n:list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
 def run(entry,args=(),ecx=0):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),stop,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(entry,stop,count=200000);assert m.reg_read(UC_X86_REG_EIP)==stop
 m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,(0x101ca068,))
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];export=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0];functions,names,ordinals=[dll.image_base+dll.u32(export+x) for x in (28,32,36)];exports={}
 for i in range(dll.u32(export+24)):
  name=dll.cstring(dll.image_base+dll.u32(names+i*4),128);ordinal=struct.unpack('<H',dll.read(ordinals+i*2,2))[0];exports[name]=dll.image_base+dll.u32(functions+ordinal*4)
 for slot,name in [(0x4b12d0,'D3DXMatrixTranslation'),(0x4b12f4,'D3DXVec3ProjectArray'),(0x4b12ec,'D3DXMatrixLookAtLH'),(0x4b12e8,'D3DXMatrixPerspectiveFovLH'),(0x4b12b8,'D3DXVec3Normalize'),(0x4b12d4,'D3DXMatrixMultiply')]:put(slot,exports[name])
 events=[];states={};draws=[];draw_states=[];submissions=[];pending=[];matrices={};vertex_buffer=base+0xf000;vertex_table=base+0xf100;vertex_data=base+0xf200;geometry=base+0xa800;texture=base+0x9c00
 def observe(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==stop+0x100:key,value=get(sp+8),get(sp+12);states[key]=value;events.append([key,value])
  elif a==stop+0x110:matrices[get(sp+8)]=list(struct.unpack('<16I',m.mem_read(get(sp+12),64)))
  elif a==stop+0x160:
   count=get(sp+12);stride=get(sp+20);p=get(sp+16);assert get(sp+8)==5 and stride==24
   submissions.append([1,get(sp+8),count,stride,states[14],states[28],*matrices[256],*matrices[16],*struct.unpack('<'+'I'*((count+2)*6),m.mem_read(p,(count+2)*stride))])
  elif a==0x475f80:
   pending.append(list(struct.unpack('<28I',m.mem_read(get(sp+4),112))));put(manager+0xbc81f0,len(pending))
  elif a==0x475eb0:
   for v in pending:submissions.append([0,states[14],states[28],*v])
   pending.clear();put(manager+0xbc81f0,0)
  elif a==stop+0x180:put(get(sp+24),vertex_buffer)
  elif a==stop+0x190:put(get(sp+16),vertex_data)
  elif a==stop+0x1c0:
   count=get(sp+16);first=get(sp+12);assert get(sp+8)==5
   submissions.append([2,get(sp+8),count,states[14],states[28],states[60],*matrices[256],*matrices[16],*struct.unpack('<'+'I'*((count+2)*5),m.mem_read(vertex_data+first*20,(count+2)*20))])
  elif a==0x478f60:
   index=(get(sp+4)-vms)//0x5cc;draws.append(index);draw_states.append([index,states[14],states[28]])
 for offset,address,cleanup in [(0xe4,stop+0x100,12),(0xb0,stop+0x110,12),(0xbc,stop+0x120,8),(0x114,stop+0x130,16),(0x104,stop+0x140,12),(0x10c,stop+0x150,16),(0x14c,stop+0x160,20),(0x164,stop+0x170,8)]:put(table+offset,address);m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
 for address,cleanup in [(0x475eb0,0),(0x475f80,4),(0x4854a0,0),(stop+0x180,28),(stop+0x190,20),(stop+0x1a0,4),(stop+0x1b0,20),(stop+0x1c0,16)]:
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
 m.hook_add(UC_HOOK_CODE,observe,begin=0x478f60,end=0x478f60)
 put(table+0x68,stop+0x180);put(vertex_buffer,vertex_table);put(vertex_table+0x2c,stop+0x190);put(vertex_table+0x30,stop+0x1a0);put(table+0x190,stop+0x1b0);put(table+0x144,stop+0x1c0)
 put(device,table);put(0x4d8f68,device);put(0x4f56cc,manager);put(0x4f7a70,32);put(0x4f7a74,16);rows=[];floats(0x4f7a6c,[1]);put(0x4f7a88,320);put(0x4f7a8c,16);put(0x4f7a80,320);put(0x4f7a84,16);put(0x4d9640,camera);run(0x47b9f0,(),manager)
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text(encoding='utf-8'));resources={};timeline_path=ROOT/'artifacts/th14/stage-native.json';timeline=json.loads(timeline_path.read_text(encoding='utf-8'));raw_base=base+0x80000
 for number in range(1,8):
  name=f'st0{number}.std';raw=(Path(archive['extraction'])/name).read_bytes();resources[name]=sha(raw);assert resources[name]==next(e['sha256'] for e in archive['decoded'] if e['name']==name)
  object_offsets=[struct.unpack_from('<I',raw,0x90+i*4)[0] for i in range(struct.unpack_from('<h',raw)[0])];animation_count=struct.unpack_from('<h',raw,2)[0];instance_offset=struct.unpack_from('<I',raw,4)[0];instance_count=0
  while struct.unpack_from('<h',raw,instance_offset+instance_count*16)[0]>=0:instance_count+=1
  for frame,layer,mode,depth,fog,mask,callbacks,visibility in itertools.product((0,599,1199),range(12),(8,23,24),range(2),range(2),(0,3),(0,1,3),(0,3)):
   m.mem_write(stage,bytes(0x4500));m.mem_write(vms,bytes(animation_count*0x5cc));m.mem_write(raw_base,raw);put(stage+0x14,directory);put(stage+0x18,raw_base+instance_offset);put(stage+0x208,vms);floats(stage+0x308c,[9610000]);floats(sprite+0x34,[48,32]);put(sprite+8,texture);put(texture,123)
   index=0
   for i,offset in enumerate(object_offsets):
    put(directory+i*4,raw_base+offset);p=offset+28
    while struct.unpack_from('<h',raw,p)[0]>=0:
     m.mem_write(raw_base+p+6,struct.pack('<h',index));index+=1;p+=struct.unpack_from('<h',raw,p+2)[0]
   assert index==animation_count
   state=next(r for r in timeline['rows'] if r['name']==name and r['rate']==1)['timeline'][frame]['values'];m.mem_write(camera,bytes(0x12c));floats(camera,state[:9]);floats(camera+0x3c,state[9:12]);floats(camera+0x54,[state[18]])
   vector=base+0xe000;floats(vector,[struct.unpack('<f',struct.pack('<f',state[3+i]+state[12+i]))[0] for i in range(3)]);run(exports['D3DXVec3Normalize'],(camera+0x24,vector));camera_input=values(camera,9)+values(camera+0x3c,3)+values(camera+0x24,3)+values(camera+0x54,1)
   m.mem_write(camera+0xe0,struct.pack('<4I2f',116,4,408,472,0,1));put(0x4d9640,camera)
   m.mem_write(manager+0xbc8188,bytes([255])*16);put(manager+0xbc8198,0);put(manager+0xbc8184,0);put(manager+0xbc81f0,0);submissions.clear();pending.clear();matrices.clear();m.mem_write(0x4fd218,bytes(112));[floats(0x4fd224+j*28,[1]) for j in range(4)]
   for n in range(80):m.mem_write(geometry+n*24,struct.pack('<3fI2f',n*.37,-n*.71,n*1.3,0x80123456,n/80,.25))
   for i in range(animation_count):
    vm=vms+i*0x5cc;put(vm+0x18,(3 if visibility&(1<<(i%2)) else 0)|(mode<<25)|(0x2000 if mask&(1<<(i%2)) else 0));put(vm+0x2c,sprite);floats(vm+0x60,[1,1,1,1]);floats(vm+0x78,[1,1]);floats(vm+0x80,[32,48]);floats(vm+0x59c,[180+i*24,100+i*20,.375]);floats(vm+0x3b8,[0,0,1,0,0,1,1,1]);put(vm+0x4ac,40);put(vm+0x5bc,0x40b3a0 if callbacks&(1<<(i%2)) else 0);put(vm+0x5b4,geometry);floats(vm+0x460,[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);put(vm+0x534,0xff123456);put(vm+0x538,0xffabcdef);put(vm+0x53c,0xff123456)
   put(0x4d9964,depth);put(0x4d9960,fog);events.clear();draws.clear();draw_states.clear();states.clear();states.update({14:depth,28:fog});run(0x40f2f0,(layer,),stage);run(0x475eb0)
   words=sum(submissions,[]);vm_fields=[]
   for i in range(animation_count):vm_fields+=values(vms+i*0x5cc+0x59c,3)+values(vms+i*0x5cc+0x60,2)+[float(bool(get(vms+i*0x5cc+0x18)&8))]
   rows.append(dict(stage=number,frame=frame,input=[layer,mode,depth,fog,mask,callbacks,visibility],camera=camera_input,status=m.reg_read(UC_X86_REG_EAX),counts=[get(stage+0x4218),get(stage+0x421c),get(stage+0x4220)],objects=[m.mem_read(raw_base+p+3,1)[0] for p in object_offsets],instances=[struct.unpack('<h',m.mem_read(raw_base+instance_offset+i*16+2,2))[0] for i in range(instance_count)],vms=vm_fields,drawStates=draw_states.copy(),finalDepth=states[14],finalFog=states[28],submissionWords=len(words),submissionsSha256=sha(struct.pack('<'+'I'*len(words),*words)),strips=sum(s[0]==1 for s in submissions),worldQuads=sum(s[0]==2 for s in submissions)))
  print('original asset stage',number,'rows',len(rows),flush=True)
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,executableSha256=sha(image.data),dllSha256=sha(dll.data),functionSha256=sha(image.read(0x40f2f0,0x316)),resources=resources,timelineSha256=sha(timeline_path.read_bytes()),rows=rows,toolSha256=sha(Path(__file__).read_bytes()),scope='Seven original STD object/primitive/instance records with the complete original40f2f0/40ebc0 and real32 D3DX camera and rendering functions, controlled original script camera inputs at frames0/599/1199. Animation slot indexes are the runtime sequential indexes assigned during resource parsing; VM state/sprite and Ribbon geometry are controlled. World modes8/23/24, depth flags, alternating/all/no callbacks, visible/invisible masks,12 layers and initial depth/fog. Submitted vertices, color, UV, world/texture matrices and state compared as complete little-endian32-bit byte hashes; VM preparation, actual draw entries, flags and counts compared directly. COM/batch/cookie controlled; no actual original ANM update, HAL pixels, complete stage/world/audio or native camera publication timing proof.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS original whole layer',len(rows))
if __name__=='__main__':main()
