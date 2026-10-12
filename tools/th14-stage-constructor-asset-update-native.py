"""TH14 original background ANM template/copy/update with real sprite binding."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-constructor-asset-update';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 parser=importlib.import_module('th-anm-script-dump');m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in image.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,image.data[raw:raw+n])
 base=0x70000000;m.mem_map(0,4096);m.mem_map(base,0x200000);vm=base+0x1000;resource=base+0x3000;sprites=base+0x10000;table=base+0x20000;code=base+0x30000;templates=base+0x60000;manager=base+0x80000;stack=base+0x1f0000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
 m.mem_write(0x4854a0,b'\xc3');put(0x4db520,manager);put(0x4f56cc,manager);floats(0x4f7a6c,[1]);put(0x4f7a88,320);put(0x4f7a8c,16)
 def run(entry,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(entry,base,count=200000)
  except Exception as e:raise RuntimeError(f'entry {entry:x} pc {m.reg_read(UC_X86_REG_EIP):x}') from e
  assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 offsets=[0x534,0x538,0x24,0x1c,0x548,0x54c,0x550,0x55c,0x560,0x564,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,*range(0x3b8,0x3d8,4),*range(0x4ac,0x4cc,4)]
 def state(p,slot):
  pointer=get(p+0x2c);sprite=(pointer-sprites)//72 if pointer else -1;instruction=get(p+0x28)
  return [sprite&0xffffffff,get(p+0x18)&1,(get(p+0x18)>>25)&31,*[get(p+o) for o in offsets],(instruction-get(table+slot*4))&0xffffffff if instruction else 0xffffffff]

 dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll');assert sha(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 for _,b,size,raw,n in dll.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,dll.data[raw:raw+n])
 m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,0,(0x101ca068,))
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];export=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0];functions,names,ordinals=[dll.image_base+dll.u32(export+x) for x in (28,32,36)]
 for i in range(dll.u32(export+24)):
  name=dll.cstring(dll.image_base+dll.u32(names+i*4),128)
  if name=='D3DXVec3Normalize':ordinal=struct.unpack('<H',dll.read(ordinals+i*2,2))[0];put(0x4b12b8,dll.image_base+dll.u32(functions+ordinal*4))

 assert image.u32(0x4d5620+8*24)==0x40b140
 loader=importlib.import_module('th14-native-stage-resource-loader').install(m)
 allocations={};pool=base+0x100000
 m.mem_write(0x485540,b'\xc3')
 def allocator(machine,address,size,user):
  nonlocal pool
  if loader.context.get('loading',False):return
  n=get(machine.reg_read(UC_X86_REG_ESP)+4);assert 0<n<=0x10000,n;assert pool+n<base+0x1e0000
  m.mem_write(pool,bytes([0xcd])*n);allocations[pool]=n;machine.reg_write(UC_X86_REG_EAX,pool);pool=(pool+n+15)&~15
 m.hook_add(UC_HOOK_CODE,allocator,begin=0x485540,end=0x485540)
 m.mem_write(0x4854af,b'\xc3');m.hook_add(UC_HOOK_CODE,allocator,begin=0x4854af,end=0x4854af)
 queue=0x72000000;m.mem_map(queue,0x40000);put(0x4db51c,queue);m.mem_write(0x4f5815,b'\x00');registrations=[]
 def registered(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP);node=get(sp+4);registrations.append([int(address==0x4011d0),get(node+8),get(sp+8),int(get(node+0x24)==stage),get(node+4)&2])
 for entry in (0x401120,0x4011d0):m.hook_add(UC_HOOK_CODE,registered,begin=entry,end=entry)
 def vm_state(p):
  origin=get(p+0x38);slot=next((i for i in range(get(resource+0x114)) if get(table+i*4)==origin),0) if origin else 0
  fields=state(p,slot);pointer=get(p+0x5b4)
  if pointer:
   assert pointer in allocations,hex(pointer)
   if get(p+0x5b8)==image.u32(0x4d5620+8*24):fields.extend([*struct.unpack('<602I',m.mem_read(pointer,0x968)),*[get(pointer+o) for o in (0xa08,0xa0c,0xa10,0xa14)]])
   else:fields.extend(struct.unpack('<'+'I'*(allocations[pointer]//4),m.mem_read(pointer,allocations[pointer])))
  return fields
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());rows=[];resources={};binary=bytearray();stage=base+0x90000;raw_base=base+0xb0000;directory=base+0xc0000;vms=base+0xd0000;nodes=[base+0xe9000+i*0x1000 for i in range(3)];put(0x4db528,stage)
 def stage_state(raw,objects):
  fields=[get(stage+o) for o in (0x4240,0x38,0x3c,0x40,0x3094,0x3098)]+[get(0x4d9514+i*4) for i in range(9)]
  fields+=[get(stage+0x306c+i*4) for i in range(8)]+[m.mem_read(raw_base+o+3,1)[0] for o in objects]
  count=struct.unpack_from('<H',raw,2)[0]
  for i in range(count):v=vm_state(vms+i*0x5cc);fields.append(len(v));fields.extend(v)
  for i in range(8):v=vm_state(stage+0x20c+i*0x5cc);fields.append(len(v));fields.extend(v)
  fields.extend(struct.unpack('<4I',m.mem_read(0x4db508,16)));return fields
 for number in range(1,8):
  name=f'st0{number}wl.anm';raw=(Path(archive['extraction'])/name).read_bytes();expected=next(r['sha256'] for r in archive['decoded'] if r['name']==name);assert sha(raw)==expected;resources[name]=expected;bodies=list(parser.scripts(raw))
  std_name=f'st0{number}.std';std=(Path(archive['extraction'])/std_name).read_bytes();expected=next(r['sha256'] for r in archive['decoded'] if r['name']==std_name);assert sha(std)==expected;resources[std_name]=expected;objects=[struct.unpack_from('<I',std,0x90+i*4)[0] for i in range(struct.unpack_from('<H',std)[0])]
  for rate in (.3,.5,.99,1,1.01,1.25):
   pool=base+0x100000;allocations.clear();floats(0x4d8f58,[rate]);m.mem_write(0x4db508,struct.pack('<HHIHHI',12345,0,0,54321,0,0));m.mem_write(templates,bytes(len(bodies)*0x5cc))
   loaded=loader.load(name,raw,(number&1)+3,rate);resource=loaded.resource;sprites=loaded.sprites;table=loaded.table;templates=loaded.templates
   loader.context['files']={std_name:std};registrations.clear();m.mem_write(queue,bytes(0x100));m.mem_write(stage,b'\xcd'*0x4500);put(0x4f58a4,number)
   m.mem_write(0x4d9514,bytes(0x12c));floats(0x4d9514+0x54,[.5235987901687622]);m.mem_write(0x4d9514+0xe0,struct.pack('<4I2f',0,0,640,480,0,1))
   std_path=base+0x4000;m.mem_write(std_path,(std_name+'\0').encode());assert run(0x40d300,stage)==stage
   assert run(0x40d3d0,stage,(std_path,0))==0
   raw_base=get(stage+0x10);directory=get(stage+0x14);vms=get(stage+0x208)
   assert get(stage+0x204)==resource;assert registrations==[[0,0x40eb70,13,1,0],[1,0x40eb80,3,1,0],[1,0x40eb90,6,1,0]],registrations
   assert get(stage+0x308c)==0x4b12a310
   m.mem_write(0x4db508,struct.pack('<HHIHHI',12345,0,0,54321,0,0))
   run(0x40f170,0);timeline=[]
   def capture(label):
    fields=stage_state(std,objects);b=struct.pack('<'+'I'*len(fields),*fields);offset=len(binary);binary.extend(b);timeline.append(dict(frame=label,offset=offset,words=len(fields),sha256=sha(b)))
   capture(-1)
   for frame in range(1200):assert run(0x40d980,stage)==1;capture(frame)
   rows.append(dict(stage=number,rate=rate,registrations=registrations.copy(),timeline=timeline))
  print('native whole Stage update with original STD/ANM',number,len(objects),flush=True)
 (OUT/'states.bin').write_bytes(binary)
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,rows=rows,resources=resources,binarySha256=sha(binary),binaryBytes=len(binary),executableSha256=sha(image.data),dllSha256=sha(dll.data),toolSha256=sha(Path(__file__).read_bytes()),parserSha256=sha((ROOT/'tools/th-anm-script-dump.py').read_bytes()),loaderSha256=sha((ROOT/'tools/th14-native-stage-resource-loader.py').read_bytes()),scope='Seven original STD and background ANM resources, complete40f170 object animation initialization and40d980 Stage update, actual full ANM/template/copy/interpreter and real32 D3DX normalization; six rates,1200 updates after initialization. Selected Stage clocks/tint/published camera/layers/object flags, selected51 VM words plus complete geometry or selected606 Ribbon words, RNG. Stage constructed by actual40d300 and initialized by40d3d0/40f030, actual original STD byte copy/pointer relocation/object VM allocation and401570/401120/4011d0 callback registrations at update13/background3/foreground6; linked callback queue otherwise empty, entry functions called explicitly. ANM resource constructed by actual47d090/47cff0/47ce40/47d130/47d230/47d420/47d9e0 and actual40cc90/46f3e0/negative-time46fe50 template preparation in the same emulator before Stage initialization. Exact file bytes supplied by controlled file service; texture upload/GetLevelDesc controlled to header dimensions. Initial camera FOV/viewport and global stage number controlled, actual STD directory and callback node construction; controlled CRT allocation; no OS asynchronous scheduling, filesystem/DAT I/O, Stage draw, HAL, battle/audio/natural clear proof.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS native full asset update',len(rows),len(binary))
if __name__=='__main__':main()
