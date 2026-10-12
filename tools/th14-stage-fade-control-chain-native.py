"""Original TH14 game control priority gate with fade callback chains."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-fade-control-chain';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 Image=importlib.import_module('th12-pe').Image;image=Image('H:/Games/th/14/th14.exe');dll=Image('C:/Windows/SysWOW64/d3dx9_43.dll')
 assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353';assert sha(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for img in (image,dll):
  for _,b,size,raw,n in img.sections:
   first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;stop=base;stack=base+0xff000;stage=base+0x1000;directory=base+0x6000;instances=base+0x7000;vms=base+0x8000;sprite=base+0xa000;device=base+0xb000;table=base+0xc000;manager=0x71000000;camera=0x4d9514
 m.mem_map(base,0x100000);m.mem_map(manager,0x1000000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));values=lambda p,n:list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
 def run(entry,args=(),ecx=0):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),stop,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(entry,stop,count=200000);assert m.reg_read(UC_X86_REG_EIP)==stop
 m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,(0x101ca068,))
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];export=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0];functions,names,ordinals=[dll.image_base+dll.u32(export+x) for x in (28,32,36)];exports={}
 for i in range(dll.u32(export+24)):
  name=dll.cstring(dll.image_base+dll.u32(names+i*4),128);ordinal=struct.unpack('<H',dll.read(ordinals+i*2,2))[0];exports[name]=dll.image_base+dll.u32(functions+ordinal*4)
 for slot,name in [(0x4b12d0,'D3DXMatrixTranslation'),(0x4b12f4,'D3DXVec3ProjectArray'),(0x4b12ec,'D3DXMatrixLookAtLH'),(0x4b12e8,'D3DXMatrixPerspectiveFovLH'),(0x4b12b8,'D3DXVec3Normalize'),(0x4b12d4,'D3DXMatrixMultiply')]:put(slot,exports[name])
 control_results=[];callback_order=[];freed=[];queue=base+0x40000;allocations=[];registrations=[];allocated_nodes=[];fade=base+0x9000;control=base+0x30000;events=[];states={};draws=[];draw_states=[];submissions=[];layers=[];clears=[];fade_requests=[];camera_events=[];pending=[];matrices={};vertex_buffer=base+0x20000;vertex_table=base+0x21000;vertex_data=base+0x22000;geometry=base+0x15000;texture=base+0x16000
 def observe(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==stop+0x100:key,value=get(sp+8),get(sp+12);states[key]=value;events.append([key,value])
  elif a==stop+0x110:matrices[get(sp+8)]=list(struct.unpack('<16I',m.mem_read(get(sp+12),64)))
  elif a==stop+0x160:
   count=get(sp+12);stride=get(sp+20);assert get(sp+8)==5 and count==2 and stride==20
   submissions.append(list(struct.unpack('<20I',m.mem_read(get(sp+16),80))))
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
  elif a==stop+0x1d0:
   p=get(sp+12);clears.append([get(sp+16),get(sp+20),*struct.unpack('<4i',m.mem_read(p,16))])
  elif a==0x4854af:
   size=get(sp+4);assert size in (0x44,0x28);allocations.append(size)
   if size==0x44:p=fade
   else:p=base+0xa000+len(allocated_nodes)*0x100;allocated_nodes.append(p)
   uc.reg_write(UC_X86_REG_EAX,p)
  elif a==0x4854fe:freed.append(get(sp+4))
  elif a in (0x401120,0x4011d0):
   node=get(sp+4);registrations.append([0 if a==0x401120 else 1,get(node+8),get(sp+8),int(get(node+0x24)==fade),get(node+4)&2])
  elif a==0x436620:callback_order.append(11)
  elif a in (0x46c400,0x46c970):callback_order.append(16)
  elif a==0x4012f7 and callback_order[-1]==11:control_results.append(uc.reg_read(UC_X86_REG_EAX))
  elif a==0x446400:camera_events.append([states.get(14,0),states.get(28,0),states.get(23,8),get(manager+0xff52d0),get(manager+0xff52cc)])
  elif a in (0x40f2f0,0x47e810):layers.append([get(sp+4),states[14],states[28],states[23]])
  elif a==0x478f60:
   index=(get(sp+4)-vms)//0x5cc;draws.append(index);draw_states.append([index,states[14],states[28]])
 for offset,address,cleanup in [(0xe4,stop+0x100,12),(0xb0,stop+0x110,12),(0xbc,stop+0x120,8),(0x114,stop+0x130,16),(0x104,stop+0x140,12),(0x10c,stop+0x150,16),(0x14c,stop+0x160,20),(0x164,stop+0x170,8)]:put(table+offset,address);m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
 for address,cleanup in [(0x475eb0,0),(0x475f80,4),(0x4854a0,0),(stop+0x180,28),(stop+0x190,20),(stop+0x1a0,4),(stop+0x1b0,20),(stop+0x1c0,16)]:
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
 m.hook_add(UC_HOOK_CODE,observe,begin=0x478f60,end=0x478f60)
 put(table+0xac,stop+0x1d0);m.mem_write(stop+0x1d0,b'\xc2\x1c\x00');m.hook_add(UC_HOOK_CODE,observe,begin=stop+0x1d0,end=stop+0x1d0);m.mem_write(0x4854af,b'\xc3');[m.hook_add(UC_HOOK_CODE,observe,begin=a,end=a) for a in (0x4854af,0x40f2f0,0x47e810)];put(table+0x68,stop+0x180);put(vertex_buffer,vertex_table);put(vertex_table+0x2c,stop+0x190);put(vertex_table+0x30,stop+0x1a0);put(table+0x190,stop+0x1b0);put(table+0x144,stop+0x1c0)
 put(device,table);put(0x4d8f68,device);put(0x4f56cc,manager);put(0x4f7a70,32);put(0x4f7a74,16);rows=[];floats(0x4f7a6c,[1]);put(0x4f7a88,320);put(0x4f7a8c,16);put(0x4f7a80,320);put(0x4f7a84,16);put(0x4d9640,camera);run(0x47b9f0,(),manager)
 for address in (0x401120,0x4011d0,0x436620,0x46c400,0x46c970,0x4012f7):m.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
 m.mem_write(0x4854fe,b'\xc3');m.hook_add(UC_HOOK_CODE,observe,begin=0x4854fe,end=0x4854fe)
 put(0x4db51c,queue);m.mem_write(0x4f5815,b'\x00')
 m.hook_add(UC_HOOK_CODE,observe,begin=0x446400,end=0x446400)
 def fields():return [get(stage+o) for o in (0x3094,0x4224,0x4228,0x422c,0x4230,0x3090,0x4218,0x421c,0x4220)]+[get(manager+0xff52d0),get(manager+0xff52cc),states[14],states[23],states[28],states.get(34,0),states.get(36,0),states.get(37,0)]
 put(0x4f7a64,640);put(0x4f7a68,480);put(0x4db558,control);put(0x4db524,stage)
 def effect_fields():return [get(fade+o) for o in (0x10,0x1c,0x18,0x20)]+[registrations[1][2]]+[get(fade+o) for o in (0x30,0x34,0x38)]
 def stage_fields():return [get(stage+o) for o in (0x4224,0x4228,0x422c,0x4230)]

 # Control helpers are delivery boundaries; the complete original game-control
 # callback and original callback-chain return-code dispatch remain executable.
 for address,cleanup in [(0x434360,0),(0x46fe50,0),(0x445710,8),(0x445810,0)]:m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
 hud=base+0x60000;root=base+0x70000;timer_owner=base+0x90000
 put(0x4db550,hud);put(0x4db68c,root);put(0x4db688,timer_owner);put(timer_owner+0x10,1);put(0x4f58b8,0);put(0x4d916c,0);put(0x4f58a4,1)
 for kind,rate,flags in itertools.product((2,3),(.3,.5,.99,1,1.01,1.25),(0,1,4,5,0x10,0x20,0x30,0x80,0x100,0x800)):
  m.mem_write(stage,bytes(0x4500));m.mem_write(fade,bytes(0x44));m.mem_write(base+0xa000,bytes(0x300));m.mem_write(control,bytes(0x100));m.mem_write(queue,bytes(0x100));freed.clear();m.mem_write(instances,b'\xff\xff');put(stage+0x18,instances);floats(stage+0x308c,[9610000]);put(stage+0x3090,3);put(stage+0x3094,0xffffff);put(stage+0x4224,4 if kind==3 else 1);put(stage+0x4228,-1);put(stage+0x4234,0x4d8f58);put(stage+0x4238,1);floats(0x4d8f58,[rate]);put(0x4f56c8,0);put(control+0x14,200)
  m.mem_write(camera,bytes(0x12c));floats(camera,[0,0,-600,0,0,1,0,1,0,0,0,1]);floats(camera+0x54,[.5235987901687622]);m.mem_write(camera+0xe0,struct.pack('<4I2f',116,4,408,472,0,1));floats(camera+0x110,[1000,5000]);put(camera+0x128,0xff605070);m.mem_write(stage+0x4274,bytes(m.mem_read(camera,0x12c)));put(0x4d9640,camera)
  put(0x4d9964,0);put(0x4d9960,0);put(manager+0xff52d0,0);put(manager+0xff52cc,0x80808080);states.clear();states.update({14:0,23:8,28:0,34:0,36:0,37:0x3f800000});allocations.clear();registrations.clear();allocated_nodes.clear();submissions.clear();pending.clear()
  run(0x40e2f0 if kind==3 else 0x4105f0,(),stage);assert allocations==[0x44,0x28,0x28];initial=effect_fields()+stage_fields()
  run(0x401570,(0x436d70,));control_node=m.reg_read(UC_X86_REG_EAX);assert control_node==allocated_nodes[2];put(control_node+0x24,control);put(control_node+4,get(control_node+4)|2);run(0x401120,(control_node,11));assert registrations[-1]==[0,0x436d70,11,0,2]
  submissions.clear();run(0x4013b0,(),queue);assert len(submissions)==1;initial_vertices=submissions[0];timeline=[]
  for frame in range(1300):
   requested=flags if frame in (10,11,12,13) else 0;put(control+0x80,requested);control_results.clear();callback_order.clear();submissions.clear();run(0x401280,(),queue)
   assert control_results==[3 if requested&0x30 and not requested&4 else 1];assert callback_order==([11] if control_results==[3] else [11,16])
   # The first chain node always remains the control owner at priority11.
   first=get(queue+0x18);assert get(first)==control_node;active=get(first+4)!=0;assert active==(get(queue+0x40)!=0)
   run(0x4013b0,(),queue);assert len(submissions)==int(active)
   timeline.append(dict(requestedFlags=requested,effectiveFlags=get(control+0x80),controlFrame=get(control+0x14),callbackOrder=callback_order.copy(),controlReturns=control_results.copy(),active=active,fields=effect_fields() if active else [],vertices=submissions[0] if submissions else []))
   if not active:break
  assert freed==[allocated_nodes[0],allocated_nodes[1],fade];run(0x401630,(control_node,),queue);assert not get(queue+0x18) and not get(queue+0x40);assert freed[-1]==control_node
  rows.append(dict(input=[kind,rate],flags=flags,allocations=allocations.copy(),registrations=registrations.copy(),initial=initial,initialVertices=initial_vertices,timeline=timeline,freed=[0 if p==fade else allocated_nodes.index(p)+1 for p in freed]))
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,executableSha256=sha(image.data),dllSha256=sha(dll.data),controlFunctionSha256=sha(image.read(0x436620,0x740)),controlWrapperSha256=sha(image.read(0x436d70,5)),updateSchedulerSha256=sha(image.read(0x401280,0x10b)),callbackReturnTableSha256=sha(image.read(0x40138c,0x24)),rows=rows,toolSha256=sha(Path(__file__).read_bytes()),scope='Whole original436620 game-control callback registered by actual401570/401120 at priority11, followed by actual original fade at16 through401280 scheduler and4013b0 draw chain. Controller clock starts200 to avoid stage activation, ten flags applied four updates, six rates and both Stage fade types. Actual controller return/flags, invoked callback order and fade fields/vertices recorded. Detached ANM/control-service/audio delivery boundaries controlled; unrelated callbacks empty; no actual Session mapping or natural pause/transition proof.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS native control/fade chains',len(rows),sum(len(r['timeline']) for r in rows))
if __name__=='__main__':main()
