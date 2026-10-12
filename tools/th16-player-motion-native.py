"""Full441cf0, ANM bind/tick/create/lookup/interrupt controlled, options inactive.

442380 runs unmodified; its active twelve-slot cases have a separate oracle.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
FIELDS=(0x2c780,0x165c8,0x16680,0x2c778,0x2c77c,0x16660,0x16664,0x16668,0x1666c,0x16670,0x16674,0x16678,0x1667c,0x61c,0x620,0x610,0x614,0x618,0x16684,0x165f4,0x1669c,0x165b4,0x165b8,0x165bc)
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,enemy,arena,stack=0x70000000,0x70001000,0x70040000,0x70050000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 handles={};events=[];next_id=2
 def initialize(v):
  m.mem_write(v,bytes(0x600));m.mem_write(v+0x5e0,struct.pack('<fff',91.,-72.,33.));m.mem_write(v+0x58,struct.pack('<ff',.75,1.25));put(v+0x490,77)
 def hook(machine,a,size,user):
  nonlocal next_id
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x46efa0:m.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0))
  elif a==0x46f0b0:
   v=handles.get(get(sp+4),0)
   if v:put(v+0x490,get(sp+8))
  elif a==0x407b20:events.append([0,get(sp+8)])
  elif a==0x406380:
   out,script=get(sp+4),get(sp+8);next_id+=1;v=arena+next_id*0x1000;handles[next_id]=v;initialize(v);events.append([1,script]);put(out,next_id);m.reg_write(UC_X86_REG_EAX,out)
  elif a==0x45f980:m.reg_write(UC_X86_REG_EAX,0)
 for a,n in ((0x46efa0,4),(0x46f0b0,8),(0x407b20,8),(0x406380,16),(0x45f980,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4a6db8,enemy+0x1000);put(enemy+0x100c,ret)
 rows=[]
 for index,(held,env,transition,seed,previous,rate) in enumerate(itertools.product(range(0,256,8),range(3),(0,3,4),range(3),(-100,0,100),(0.,.5,1.,1.5))):
  m.mem_write(player,bytes(0x30000));handles.clear();events.clear();next_id=2
  for i in (1,2):handles[i]=arena+i*0x1000;initialize(handles[i])
  charge=(0,1,4)[index%3];flags=(0,0x12,0x10)[seed]
  for off,v in ((0x61c,(-321,-23560,23560)[seed]),(0x620,(50319,4000,55350)[seed]),(0x63c,transition),(0x16650,576),(0x16654,256),(0x16658,407),(0x1665c,181),(0x2c778,previous),(0x2c77c,101),(0x1664c,flags),(0x16680,67),(0x16684,(0,29,31)[seed]),(0x165f4,4),(0x1669c,6),(0x165ac,(0,1,99)[seed]),(0x165b0,2 if seed==2 else 0),(0x165b4,23),(0x165b8,charge),(0x165bc,bits(float(charge))), (0x165c4,1)):
   put(player+off,v)
  for off,v in ((0x618,5.25),(0x16668,7.25),(0x1666c,11.25),(0x16670,12.5),(0x16674,13.75),(0x16688,(1.,.5,1.5)[seed]),(0x2c7c8,2.25),(0x1668c,(0.,.125,1.25)[seed]),(0x16690,(0.,-.25,-.875)[seed])):put(player+off,bits(v))
  put(0x4a52c8,held);put(0x4a6dc0,enemy if env else 0);put(enemy+0x18c,env==2);put(0x4a5788,bits(rate));put(0x490eb0,0x4a5788)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(0x441cf0,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(held=held,env=env,transition=transition,seed=seed,previous=previous,rate=rate,charge=charge,output=[get(player+k) for k in FIELDS],handles=[bool(get(player+o)) for o in (0x165ac,0x165b0)],events=events[:],animations=[[get(v+k) for k in (0x5e0,0x5e4,0x5e8,0x58,0x5c,0x490)]+[get(v+0x530)&8] for v in handles.values()]))
 (ROOT/'artifacts/th16/player-motion-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} original TH16 player movement cases')
if __name__=='__main__':main()
