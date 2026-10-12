"""Own4184a0 pools,430960 ordinary factory and430d90 free-list recycling."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);manager,pos,stack,ret=0x70000000,0x71f00000,0x71ffd000,0x71ffe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 def slot(p):return (p-manager-0x14)//0xc78 if p else -1
 def memset(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP);p=get(sp+4);machine.mem_write(p,bytes(get(sp+12)));machine.reg_write(UC_X86_REG_EAX,p)
 m.mem_write(0x477920,b'\xc3');m.hook_add(UC_HOOK_CODE,memset,begin=0x477920,end=0x477920)
 def call(a,ecx,args=()):
  put(stack,ret)
  for n,v in enumerate(args):put(stack+4+n*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.emu_start(a,ret,count=200000);assert m.reg_read(UC_X86_REG_EIP)==ret
 put(0x4a6ddc,manager);call(0x4184a0,manager);chains=[]
 for off in (0xe4b958,0xe4b968):
  p=get(manager+off);chain=[]
  while p:chain.append(slot(p));p=get(p+4)
  chains.append(chain)
 item=manager+0x14+599*0xc78;head=manager+0xe4b954;events=[]
 put(0x4a6dac,manager);put(0x4a6db8,manager)
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x40d460:put(get(sp+4)+0x24,get(sp+8))
  elif a==0x40e5c0:
   p=get(sp+12);events.extend([0,get(sp+8),get(p),get(p+4),get(p+8)])
   put(get(sp+4),0);machine.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x45e150:events.extend([1,get(sp+4)])
 for a,cleanup in ((0x40d460,8),(0x40e5c0,24),(0x45e150,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 cases=[]
 for kind,count,drop,x,full,force in itertools.product((*range(1,9),15),(0,0xffffffff),(0,0x7fffffff),(-200,17.25,200),(False,True),(-1,1)):
  m.mem_write(item,bytes(0xc78));put(item,head);put(item+8,head);put(item+4,0 if full else item-0xc78);put(item-0xc78+8,item);put(manager+0xe4b958,0 if full else item)
  put(item+0xc64,0x12345678);put(item+0xc24,bits(.25));put(manager+0x1c972e0,count);put(0x4a587c,drop)
  p=(x,61.5,2);angle=.75;speed=2.2
  for n,v in enumerate(p):put(pos+n*4,bits(v))
  events.clear();call(0x430960,0,(kind,pos,0,bits(angle),bits(speed),0,force))
  output=[get(item+off) for off in (0xc08,0xc0c,0xc10,0xc14,0xc18,0xc1c,0xc20,0xc24,0xc28,0xc2c,0xc30,0xc38,0xc50,0xc54,0xc58,0xc60,0xc64,0xc68)]+[get(manager+0x1c972e0),slot(get(manager+0xe4b958))&0xffffffff,get(0x4a587c),get(item+0x530),get(item+0x34),get(item+0x630)]
  cases.append(dict(kind=kind,count=count,drop=drop,position=p,full=full,force=force,angle=angle,speed=speed,output=output,events=list(events)))
 call(0x4184a0,manager);allocations=[]
 for n in range(602):
  p=get(manager+0xe4b958);call(0x430960,0,(1,pos,0,bits(0),bits(1),0,0));allocations.append(slot(p))
 count_after=get(manager+0x1c972e0);recycle=manager+0x14+337*0xc78;call(0x430d90,recycle);call(0x430960,0,(1,pos,0,bits(0),bits(1),0,0))
 recycled=dict(slot=337,state=get(recycle+0xc50),head=slot(get(manager+0xe4b958)),count=get(manager+0x1c972e0))
 (ROOT/'artifacts/th16/item-ordinary-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,allocations=allocations,countAfter=count_after,recycled=recycled),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own TH16 ordinary item factories')
if __name__=='__main__':main()
