"""Actual player/enemy portrait roots and expression family timing."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x100000);resource=base+0x3000;table=base+0x6000;templates=base+0x10000;stack=base+0xf0000;root=base+0xb0000
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());extraction=Path(archive['extraction']);codes={}
 roots=[('pl00.anm',27),('pl01.anm',37),('pl02.anm',25),('st01enm.anm',10),('st01enm.anm',16),('st02enm.anm',22),('st02enm.anm',28),('st03enm.anm',13),('st03enm.anm',18),('st04enm.anm',8),('st04enm.anm',13),('st04enm2.anm',8),('st04enm2.anm',9),('st05enm.anm',8),('st05enm.anm',13),('st06enm.anm',14),('st06enm.anm',19),('st07enm.anm',12),('st07enm.anm',16),('st07enm2.anm',8),('st07enm3.anm',8)]
 resources={name:dict((s,b) for s,_,b in importlib.import_module('th-anm-script-dump').scripts((extraction/name).read_bytes())) for name,_ in roots}
 resource_hashes={name:hashlib.sha256((extraction/name).read_bytes()).hexdigest() for name in resources}
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 allocated=[]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);result=0
  if a==0x48f980:result=get(sp+4);m.mem_write(result,bytes([get(sp+8)&255])*get(sp+12));pop=0
  elif a==0x46f1e0:m.mem_write(get(sp+4)+0x34,struct.pack('<H',get(sp+8)&0xffff));pop=8
  elif a==0x47fcb0:
   result=root+0x1000*(len(allocated)+1);m.mem_write(result,bytes(0x700));put(result+0x580,result);allocated.append(result);pop=0
  elif a in (0x47e890,0x47e950,0x47e9f0,0x47eab0):result=get(sp+4);put(result,100+allocated.index(get(sp+8)));pop=8
  elif a==0x47f0a0:result=root if get(sp+4)==9000 else 0;pop=4
  elif a==0x4854a0:pop=0
  else:return
  if a!=0x4854a0:uc.reg_write(UC_X86_REG_EAX,result)
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x48f980,0x46f1e0,0x47fcb0,0x47e890,0x47e950,0x47e9f0,0x47eab0,0x47f0a0,0x4854a0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4db520,base+0xd0000);put(0x4f56cc,base+0xd0000);put(resource+0x120,table);put(resource+0x10c,templates)

 def run(address,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(address,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 offsets=(0x534,0x538,0x24,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x4a0,0x4bc,0x4c0,0x78,0x7c)
 def state(p):
  slot=struct.unpack('<h',m.mem_read(p+0x4aa,2))[0];return [get(p+0x34)&0xffff,*[get(p+o) for o in offsets],get(p+0x528)&0xffff,get(p+0x1c)&0xa00,get(p+0x18)&1,get(p+0x28)-codes[slot] if get(p+0x28) else 0xffffffff,int(get(p+0x594)==root),slot]
 def family_state():return [state(p) for p in [root,*allocated]]
 rows=[]
 for resource_index,rate,synchronous,sequence in itertools.product(range(len(roots)),(.5,1.,1.25),(0,1),(0,1)):
  filename,slot=roots[resource_index];bodies=resources[filename];codes.clear();cursor=base+0x80000
  for script,body in bodies.items():codes[script]=cursor;m.mem_write(cursor,body);put(table+script*4,cursor);cursor+=(len(body)+15)&~15
  allocated.clear();m.mem_write(0x4d8f58,struct.pack('<f',rate))
  for s in bodies:
   p=templates+s*0x5cc;m.mem_write(p,bytes(0x5cc));run(0x46f3e0,resource,(p,s))
   for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(p+o,v)
   assert run(0x46fe50,p)==0
  m.mem_write(root,bytes(0x700));put(root+0x580,root);run(0x40af00,resource,(root,slot));put(root+0x1c,get(root+0x1c)|0x200);assert run(0x46fe50,root)==0;assert len(allocated) in (0,2)
  linked=[];node=get(root+0x584)
  while node:linked.append(struct.unpack('<h',m.mem_read(get(node)+0x4aa,2))[0]);node=get(node+4)
  initial=family_state();frames=[];events=[];active=[True]*(len(allocated)+1)
  for frame in range(140):
   label=({12:2,45:3,60:2,100:1} if sequence==0 else {12:2,25:17,35:18,45:3,55:19,60:2,65:20,75:21,85:22,100:1}).get(frame)
   if label is not None:run(0x47f1b0 if synchronous else 0x47f140,base+0xd0000,(9000,label));events.append(dict(frame=frame,label=label,state=family_state()))
   statuses=[]
   for i,p in enumerate([*allocated,root]):
    index=(i+1)%len(active);status=run(0x46fe50,p) if active[index] else 1;active[index]=not status;statuses.append(status)
   frames.append(dict(statuses=statuses,state=family_state()))
   if not any(active):break
  rows.append(dict(input=[resource_index,slot,rate,synchronous,sequence],linked=linked,initial=initial,events=events,frames=frames))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceHashes=resource_hashes,roots=roots,rows=rows,scope='Twenty-one actual player/enemy portrait roots, including MSG20 effect roots, three player portraits, seven stages and Extra sisters. Full original46f3e0/40af00/46fe50 and nested47ee90 creation/linking; full47f140 deferred and47f1b0 synchronous family labels2/3/1 and17..22 expressions; ordinary creation-order updates. Allocator/registration/lookup/sprite/memset/cookie boundaries controlled. Selected state capture retains deleted VMs; no native manager traversal/destructor, actual sprite geometry/GPU or full dialogue/world claim.')
 (ROOT/'artifacts/th14/dialogue-portrait-family-native.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native portrait families',len(rows),sum(len(r['frames']) for r in rows))
if __name__=='__main__':main()
