"""Actual portrait native pool/heap allocation, recycle and stale-handle lookup."""
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
 allocated=[];dead=set();heap_allocated=[];pool_allocations=[]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);result=0
  if a==0x48f980:result=get(sp+4);m.mem_write(result,bytes([get(sp+8)&255])*get(sp+12));pop=0
  elif a==0x46f1e0:m.mem_write(get(sp+4)+0x34,struct.pack('<H',get(sp+8)&0xffff));pop=8
  elif a==0x4854af:
   result=base+0xb0000+0x1000*len(heap_allocated);m.mem_write(result,bytes(0x700));heap_allocated.append(result);allocated.append(result);pop=0
  elif a==0x4854fe:dead.add(get(sp+4));pop=0
  elif a==0x47ecc1:dead.add(uc.reg_read(UC_X86_REG_ESI));return
  elif a==0x47fd12:
   result=uc.reg_read(UC_X86_REG_EDX);allocated.append(result);pool_allocations.append(get(result+0x544));return
  elif a==0x4854a0:pop=0
  else:return
  if a!=0x4854a0:uc.reg_write(UC_X86_REG_EAX,result)
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x48f980,0x46f1e0,0x4854af,0x4854fe,0x4854a0,0x47fd12,0x47ecc1):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4db520,base+0xd0000);put(0x4f56cc,manager);put(resource+0x120,table);put(resource+0x10c,templates)

 def run(address,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(address,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP));return m.reg_read(UC_X86_REG_EAX)
 offsets=(0x534,0x538,0x24,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x4a0,0x4bc,0x4c0,0x78,0x7c)
 def state(p):
  slot=struct.unpack('<h',m.mem_read(p+0x4aa,2))[0];return [get(p+0x34)&0xffff,*[get(p+o) for o in offsets],get(p+0x528)&0xffff,get(p+0x1c)&0xa00,get(p+0x18)&1,get(p+0x28)-codes[slot] if get(p+0x28) else 0xffffffff,int(get(p+0x594)==root),slot]
 def family_state():return [state(p) if p not in dead else [0]*22 for p in allocated]
 def layer_state():
  result=[]
  for layer in range(36):
   p=get(manager+0xfe8218+layer*0x5cc+0x590);chain=[]
   while p:chain.append(allocated.index(p));assert len(chain)<=len(allocated);p=get(p+0x590)
   result.append(chain)
  return result
 rows=[]
 for resource_index,capacity,synchronous,sequence in itertools.product(range(len(roots)),(0,1,3),(0,1),(0,1)):
  rate=1.
  filename,slot=roots[resource_index];bodies=resources[filename];codes.clear();cursor=base+0x80000
  for script,body in bodies.items():codes[script]=cursor;m.mem_write(cursor,body);put(table+script*4,cursor);cursor+=(len(body)+15)&~15
  allocated.clear();dead.clear();heap_allocated.clear();pool_allocations.clear();m.mem_write(manager+0xfe8208,bytes(16));put(manager+0xff52c8,0);m.mem_write(0x4d8f58,struct.pack('<f',rate))
  sentinel=manager+0xbc7af8;m.mem_write(sentinel,bytes(16));put(sentinel+4,manager+0xdc+0x5cc if capacity else 0)
  for i in range(capacity):
   p=manager+0xdc+i*0x5e4;m.mem_write(p,bytes(0x5e4));put(p+0x544,i);run(0x40cc90,p);put(p+0x5cc,p);put(p+0x5d0,manager+0xdc+(i+1)*0x5e4+0x5cc if i+1<capacity else 0);put(p+0x5d4,manager+0xdc+(i-1)*0x5e4+0x5cc if i else sentinel);put(p+0x5e0,i)
  for s in bodies:
   p=templates+s*0x5cc;m.mem_write(p,bytes(0x5cc));run(0x46f3e0,resource,(p,s))
   for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(p+o,v)
   assert run(0x46fe50,p)==0
  cycles=[];previous_handle=0
  for cycle in range(2):
   # Keep the actual pool free chain from the preceding destruction cycle.
   for p in allocated:
    if p not in dead:run(0x47eb50,manager,(p,))
   allocated.clear();dead.clear();pool_allocations.clear()
   run(0x47ed10,resource,(base+0x9000,slot,0,0,0xffffffff,0,0));handle=get(base+0x9000);root=allocated[0];assert len(allocated) in (1,3);assert run(0x47f0a0,manager,(handle,))==root
   stale=run(0x47f0a0,manager,(previous_handle,));assert stale==0;assert len(pool_allocations)==min(capacity,len(allocated))
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
   cycles.append(dict(linked=linked,initial=initial,events=events,frames=frames,pool=list(pool_allocations),staleFound=bool(stale)))
   previous_handle=handle
  rows.append(dict(input=[resource_index,capacity,synchronous,sequence],cycles=cycles))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceHashes=resource_hashes,roots=roots,rows=rows,scope='Twenty-one real portrait/MSG20 effect roots, two consecutive creation/lifetime cycles, native pool capacities0/1/3 and heap fallback. Whole47ed10 factory,47fcb0 allocator (actual pool and heap branches),40cc90 pool initialization,40af00 template copy,47ee90 children,47e890 registration,47f0a0 lookup,47f140/47f1b0 labels,47e5e0/47e6c0 update and47eb50 pool/heap destruction. Actual freed pool nodes are reused in the second cycle; stale prior root handle must not resolve while the new root is alive. CRT heap allocation/free, sprite binding,memset/cookie controlled; heap allocator returns fresh synthetic storage. Synthetic shortened native free chain supplies tested pool capacities. Original encoded handles and storage addresses recorded only as native observations, not required as portable internal representation. No sprite geometry/GPU, full MSG interpreter/world or complete original scene claim.')
 (ROOT/'artifacts/th14/dialogue-portrait-pool-native.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native portrait pool',len(rows),sum(len(c['frames']) for r in rows for c in r['cycles']))
if __name__=='__main__':main()
