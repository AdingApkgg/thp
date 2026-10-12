"""Visible standalone quads through whole original40f2f0/4107b0/478f60."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-standalone-render';OUT.mkdir(parents=True,exist_ok=True)
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
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),stop,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(entry,stop,count=300000)
  except Exception:
   print('entry',hex(entry),'eip',hex(m.reg_read(UC_X86_REG_EIP)),flush=True);raise
  assert m.reg_read(UC_X86_REG_EIP)==stop,hex(m.reg_read(UC_X86_REG_EIP))
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
 states={};draws=[];events=[];camera_mode=[0];animation_events=[];quads=[];vertex_buffer=base+0x15000;vertex_table=base+0x16000;vertex_data=base+0x17000
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==stop+0x100:key,value=get(sp+8),get(sp+12);states[key]=value;events.append([key,value])
  elif a==0x475f80:
   p=get(sp+4);quads.append(dict(depth=states[14],fog=states[28],vertices=[list(struct.unpack('<4fI2f',m.mem_read(p+i*28,28))) for i in range(4)]))
  elif a==0x478f60:draws.append([(get(sp+4)-stage-0x20c)//0x5cc,states[14],states[28],camera_mode[0]])
  elif a==0x4461e0:camera_mode[0]=1
  elif a==0x446400:camera_mode[0]=0
  elif a==0x40af00:animation_events.append([(get(sp+4)-stage-0x20c)//0x5cc,get(sp+8)])
  elif a==0x4854af:uc.reg_write(UC_X86_REG_EAX,0)
  elif a==stop+0x170:put(get(sp+24),vertex_buffer)
  elif a==stop+0x180:put(get(sp+16),vertex_data)
 for offset,address,cleanup in [(0xe4,stop+0x100,12),(0xb0,stop+0x110,12),(0xbc,stop+0x120,8),(0x114,stop+0x130,16),(0x104,stop+0x140,12),(0x10c,stop+0x150,16),(0x164,stop+0x160,8)]:put(table+offset,address);m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 for a,cleanup in [(0x475eb0,0),(0x475f80,4),(0x4854a0,0),(0x40af00,8),(0x46fe50,0),(0x40f610,4),(0x4854af,0)]:m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
 for a in (0x475f80,0x478f60,0x4461e0,0x446400,0x40af00,0x4854af):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for address,cleanup in [(stop+0x170,28),(stop+0x180,20),(stop+0x190,4),(stop+0x1a0,20),(stop+0x1b0,16)]:m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 put(table+0x68,stop+0x170);put(vertex_buffer,vertex_table);put(vertex_table+0x2c,stop+0x180);put(vertex_table+0x30,stop+0x190)
 put(table+0x190,stop+0x1a0);put(table+0x144,stop+0x1b0)
 put(device,table);put(0x4d8f68,device);put(0x4f56cc,manager);floats(0x4d8f58,[1]);m.mem_write(instances,b'\xff\xff');floats(sprite+0x34,[48,32]);put(0x4f7a6c,1)
 rows=[];texture=base+0x9100;put(sprite+8,texture);put(texture,123);floats(0x4f7a6c,[1]);put(0x4f7a88,320);put(0x4f7a8c,16);put(0x4f7a80,320);put(0x4f7a84,16)
 trace=[]
 def trace_code(uc,a,n,u):
  if a<0x1000:raise RuntimeError('unmapped service trace '+str([hex(v) for v in trace]))
  trace.append(a)
  if len(trace)>20:del trace[0]
 trace_hook=m.hook_add(UC_HOOK_CODE,trace_code)
 try:put(0x4d9640,camera);run(0x47b9f0,(),manager)
 except Exception:
  print('trace',[hex(a) for a in trace],flush=True);raise
 m.hook_del(trace_hook)
 for layer,mode,depth,fog,mask,pattern in itertools.product(range(12),range(4),range(2),range(2),(2,0xff),range(2)):
  m.mem_write(stage,bytes(0x4500));m.mem_write(camera,bytes(0x12c));floats(camera,[0,0,-600,0,0,1,0,1,0,0,0,1]);floats(camera+0x54,[.5235987901687622]);m.mem_write(camera+0xe0,struct.pack('<4I2f',116,4,408,472,0,1));put(stage+0x18,instances)
  m.mem_write(manager+0xbc8188,bytes([255])*16);m.mem_write(0x4fd218,bytes(112))
  for i in range(4):floats(0x4fd224+i*28,[1])
  for i in range(8):
   vm=stage+0x20c+i*0x5cc;assigned=layer if pattern==0 else i;put(stage+0x306c+i*4,assigned);put(vm+0x2c,sprite if mask&(1<<i) else 0);put(vm+0x18,3|(mode<<25));floats(vm+0x60,[1,1,1,1]);floats(vm+0x78,[1,1]);floats(vm+0x80,[32,48]);floats(vm+0x59c,[180+i*24,100+i*20,.375]);put(vm+0x534,0xff123456);put(vm+0x538,0xffabcdef);put(vm+0x53c,0xff123456);floats(vm+0x3b8,[0,0,1,0,0,1,1,1])
  put(0x4d9964,depth);put(0x4d9960,fog);states.clear();states.update({14:depth,28:fog});draws.clear();events.clear();quads.clear();camera_mode[0]=0;run(0x446400,(camera,));run(0x40f2f0,(layer,),stage)
  rows.append(dict(input=[layer,mode,depth,fog,mask,pattern],draws=draws.copy(),quads=quads.copy(),finalDepth=states[14],finalFog=states[28],status=m.reg_read(UC_X86_REG_EAX)))
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,executableSha256=sha(img.data),dllSha256=sha(dll.data),toolSha256=sha(Path(__file__).read_bytes()),rows=rows,scope='Whole original40f2f0/4107b0/478f60 visible standalone modes0..3 with real32 D3DX camera setup; synthetic VMs and empty object list. GPU batch/flush, COM calls and cookie are controlled; quad submission vertices and draw-time depth/fog observed, no actual HAL/world/audio proof.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS visible standalone',len(rows),'cases',sum(len(r['quads']) for r in rows),'quads')
if __name__=='__main__':main()
