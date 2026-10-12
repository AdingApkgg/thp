"""Retail parent creation, child linking and synchronous family interrupts."""
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
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());source=Path(archive['extraction'])/'front.anm';bodies={s:b for s,_,b in importlib.import_module('th-anm-script-dump').scripts(source.read_bytes()) if s in range(168,232)};codes={};cursor=base+0x80000
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
 for slot,body in bodies.items():codes[slot]=cursor;m.mem_write(cursor,body);put(table+slot*4,cursor);cursor+=(len(body)+15)&~15
 def run(address,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(address,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 offsets=(0x534,0x538,0x24,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x4a0,0x4bc,0x4c0,0x78,0x7c)
 def state(p):
  slot=struct.unpack('<h',m.mem_read(p+0x4aa,2))[0];return [get(p+0x34)&0xffff,*[get(p+o) for o in offsets],get(p+0x528)&0xffff,get(p+0x1c)&0xa00,get(p+0x18)&1,get(p+0x28)-codes[slot] if get(p+0x28) else 0xffffffff,int(get(p+0x594)==root),slot]
 def family_state():return [state(p) for p in [root,*allocated]]
 rows=[]
 for slot,rate,width,synchronous in itertools.product(range(216,232),(.5,1.,1.25),(32.,128.,384.),(0,1)):
  allocated.clear();m.mem_write(0x4d8f58,struct.pack('<f',rate))
  for s in (slot,slot-48,slot-32,slot-16):
   p=templates+s*0x5cc;m.mem_write(p,bytes(0x5cc));run(0x46f3e0,resource,(p,s))
   for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(p+o,v)
   assert run(0x46fe50,p)==0
  m.mem_write(root,bytes(0x700));put(root+0x580,root);run(0x40af00,resource,(root,slot));put(root+0x1c,get(root+0x1c)|0x200);assert run(0x46fe50,root)==0;assert len(allocated)==3
  for p in (allocated[0],allocated[2]):m.mem_write(p+0x4bc,struct.pack('<f',width))
  linked=[];node=get(root+0x584)
  while node:linked.append(struct.unpack('<h',m.mem_read(get(node)+0x4aa,2))[0]);node=get(node+4)
  initial=family_state();frames=[];events=[];active=[True]*4
  for frame in range(110):
   label={12:2,45:3,60:8,90:1}.get(frame)
   if label is not None:run(0x47f1b0 if synchronous else 0x47f140,base+0xd0000,(9000,label));events.append(dict(frame=frame,label=label,state=family_state()))
   statuses=[]
   for i,p in enumerate([*allocated,root]):
    index=(i+1)%4;status=run(0x46fe50,p) if active[index] else 1;active[index]=not status;statuses.append(status)
   frames.append(dict(statuses=statuses,state=family_state()))
   if not any(active):break
  rows.append(dict(input=[slot,rate,width,synchronous],linked=linked,initial=initial,events=events,frames=frames))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=rows,scope='Actual front.anm216..231 roots and three actual child scripts; complete46f3e0/40af00/46fe50 and nested47ee90 allocation/copy/first update/parent linking. Complete47f140 queues the full family;complete47f1b0 synchronously updates root and reverse child chain at labels2/3/8/1; ordinary updates explicitly run registered creation order. Allocator/registry/lookup/sprite/memset/cookie boundaries controlled. Deleted VMs retained for state capture; no native manager traversal/destructor or GPU/full-world claim.')
 (ROOT/'artifacts/th14/dialogue-panel-family-native.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native panel families',len(rows),sum(len(r['frames']) for r in rows))
if __name__=='__main__':main()
