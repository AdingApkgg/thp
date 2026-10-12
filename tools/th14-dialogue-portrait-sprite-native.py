"""Real portrait sprite record construction and unmodified binding lifecycle."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x100000);resource=base+0x3000;table=base+0x6000;templates=base+0x10000;stack=base+0xf0000;root=base+0xb0000;manager=0x71000000;m.mem_map(manager,0x1000000)
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());extraction=Path(archive['extraction']);codes={}
 roots=[('pl00.anm',27),('pl01.anm',37),('pl02.anm',25),('st01enm.anm',10),('st01enm.anm',16),('st02enm.anm',22),('st02enm.anm',28),('st03enm.anm',13),('st03enm.anm',18),('st04enm.anm',8),('st04enm.anm',13),('st04enm2.anm',8),('st04enm2.anm',9),('st05enm.anm',8),('st05enm.anm',13),('st06enm.anm',14),('st06enm.anm',19),('st07enm.anm',12),('st07enm.anm',16),('st07enm2.anm',8),('st07enm3.anm',8)]
 resources={name:dict((s,b) for s,_,b in importlib.import_module('th-anm-script-dump').scripts((extraction/name).read_bytes())) for name,_ in roots}
 resource_hashes={name:hashlib.sha256((extraction/name).read_bytes()).hexdigest() for name in resources}
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 allocated=[];dead=set()
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);result=0
  if a==0x48f980:result=get(sp+4);m.mem_write(result,bytes([get(sp+8)&255])*get(sp+12));pop=0
  elif a==0x4854af:
   result=root+0x1000*len(allocated);m.mem_write(result,bytes(0x700));allocated.append(result);pop=0
  elif a==0x4854fe:dead.add(get(sp+4));pop=0
  elif a==0x4854a0:pop=0
  else:return
  if a!=0x4854a0:uc.reg_write(UC_X86_REG_EAX,result)
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x48f980,0x4854af,0x4854fe,0x4854a0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4db520,base+0xd0000);put(0x4f56cc,manager);put(resource+0x120,table);put(resource+0x10c,templates)

 def run(address,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(address,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 offsets=(0x534,0x538,0x24,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x4a0,0x4bc,0x4c0,0x78,0x7c)
 def state(p):
  slot=struct.unpack('<h',m.mem_read(p+0x4aa,2))[0];return [get(p+0x34)&0xffff,*[get(p+o) for o in offsets],get(p+0x528)&0xffff,get(p+0x1c)&0xa00,get(p+0x18)&1,get(p+0x28)-codes[slot] if get(p+0x28) else 0xffffffff,int(get(p+0x594)==root),slot,*[get(p+o) for o in (0x80,0x84,0x3b8,0x3bc,0x3c0,0x3c4,0x3c8,0x3cc,0x3d0,0x3d4,0x3e0,0x3f4,0x460,0x474,0x420,0x434)]]
 def family_state():return [state(p) if p not in dead else [0]*38 for p in allocated]
 def layer_state():
  result=[]
  for layer in range(36):
   p=get(manager+0xfe8218+layer*0x5cc+0x590);chain=[]
   while p:chain.append(allocated.index(p));assert len(chain)<=len(allocated);p=get(p+0x590)
   result.append(chain)
  return result
 def prepare_sprites(filename):
  data=(extraction/filename).read_bytes();offset=0;index=0;records=base+0x40000;source=base+0x60000;put(resource+0x11c,records)
  while True:
   ns=struct.unpack_from('<H',data,offset+4)[0];width,height=struct.unpack_from('<HH',data,offset+10)
   for i in range(ns):
    raw=struct.unpack_from('<I',data,offset+64+i*4)[0]+offset;number,x,y,w,h=struct.unpack_from('<I4f',data,raw);assert number==index
    right=struct.unpack('<f',struct.pack('<f',x+w))[0];bottom=struct.unpack('<f',struct.pack('<f',y+h))[0]
    m.mem_write(source,bytes(72));m.mem_write(source+0xc,struct.pack('<6f',x,y,right,bottom,float(height),float(width)));m.mem_write(source+0x3c,struct.pack('<2f',1.,1.));run(0x47d9e0,resource,(index,source));index+=1
   stride=struct.unpack_from('<I',data,offset+36)[0]
   if not stride:break
   offset+=stride
  put(resource+0x108,index)
 rows=[]
 for resource_index,rate,synchronous,sequence in itertools.product(range(len(roots)),(.5,1.,1.25),(0,1),(0,1)):
  filename,slot=roots[resource_index];bodies=resources[filename];prepare_sprites(filename);codes.clear();cursor=base+0x80000
  for script,body in bodies.items():codes[script]=cursor;m.mem_write(cursor,body);put(table+script*4,cursor);cursor+=(len(body)+15)&~15
  allocated.clear();dead.clear();m.mem_write(manager+0xfe8208,bytes(16));put(manager+0xff52c8,0);m.mem_write(0x4d8f58,struct.pack('<f',rate))
  for s in bodies:
   p=templates+s*0x5cc;m.mem_write(p,bytes(0x5cc));run(0x46f3e0,resource,(p,s))
   for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(p+o,v)
   assert run(0x46fe50,p)==0
  run(0x47ed10,resource,(base+0x9000,slot,0,0,0xffffffff,0,0));handle=get(base+0x9000);assert allocated[0]==root;assert len(allocated) in (1,3);assert run(0x47f0a0,manager,(handle,))==root
  linked=[];node=get(root+0x584)
  while node:linked.append(struct.unpack('<h',m.mem_read(get(node)+0x4aa,2))[0]);node=get(node+4)
  initial=family_state();frames=[];events=[]
  for frame in range(140):
   label=({12:2,45:3,60:2,100:1} if sequence==0 else {12:2,25:17,35:18,45:3,55:19,60:2,65:20,75:21,85:22,100:1}).get(frame)
   if label is not None:run(0x47f1b0 if synchronous else 0x47f140,manager,(handle,label));events.append(dict(frame=frame,label=label,state=family_state()))
   run(0x47e5e0,manager);run(0x47e6c0,manager)
   alive=[int(p not in dead) for p in allocated]
   frames.append(dict(alive=alive,state=family_state(),layers=layer_state()))
   if not any(alive):break
  rows.append(dict(input=[resource_index,slot,rate,synchronous,sequence],linked=linked,initial=initial,events=events,frames=frames))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceHashes=resource_hashes,roots=roots,rows=rows,scope='Twenty-one real portrait/MSG20 effect roots; original47d9e0 builds all647 sprite records from independent original ANM chunk coordinates/extents, original46f1e0 binding runs without replacement. Actual47ed10/47fcb0 heap factory,40af00 preparation/copy,47ee90 children,47e890 registration,47f0a0 lookup,47f140/47f1b0 labels,47e5e0/47e6c0 updates and47eb50 destruction. Captures prior22 state words plus sprite dimensions,eight UV coordinates,sprite/UV/transform matrix diagonals at every frame/event. Native texture extents supplied from ANM headers with resize factors1; native full resource loader and dynamic texture resizing not claimed. CRT heap allocate/free,memset/cookie controlled; no sprite binding replacement, geometry/GPU or full world claim.')
 (ROOT/'artifacts/th14/dialogue-portrait-sprite-native.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native portrait sprite',len(rows),sum(len(r['frames']) for r in rows))
if __name__=='__main__':main()
