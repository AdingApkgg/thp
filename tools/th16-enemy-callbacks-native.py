"""Complete retail4252d0 proximity callback and4202b6 selector, without external sinks."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);enemy,links,player,manager,bullets,stack,ret=0x70001000,0x70004000,0x70005000,0x70010000,0x70020000,0x71ffd000,0x71ffe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 put(0x4a6dac,manager);put(0x4a6ef8,player);cases=[]
 for n in range(512):
  count=n%7;radius=(0.,1.,-1.,32.,-32.,float('inf'),float('nan'),.25)[n%8];px=(-192.,0.,15.5,192.)[(n//8)%4];py=(0.,48.25,400.)[(n//32)%3]
  put(enemy+0x29c,bits(radius));put(player+0x610,bits(px));put(player+0x614,bits(py));put(manager+0x70,links if count else 0);rows=[]
  for k in range(count):
   b=bullets+k*0x2000;link=links+k*12;dx=(0.,.25,1.,32.,-32.,float('nan'))[(n+k)%6];dy=(0.,.125,1.,-32.)[(n+2*k)%4]
   values=[bits(px+dx),bits(py+dy),bits(.5),((n+k)%4)-1,(n+k)%18,(0,1,16,0x80000000,0xffffffff)[(n+k)%5]];rows.extend(v&0xffffffff for v in values)
   for o,v in zip((0xc20,0xc24,0xc28,0xc4c,0xc60,0xc68),values):put(b+o,v)
   put(link,b);put(link+4,link+12 if k+1<count else 0);put(link+8,link-12 if k else 0)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.emu_start(0x4252d0,ret,count=10000);assert m.reg_read(UC_X86_REG_EIP)==ret
  assert m.reg_read(UC_X86_REG_EAX)==0;assert get(manager+0x1403b1c)==get(manager+0x1403b20)==0
  cases.append(dict(n=n,count=count,radiusBits=bits(radius),playerBits=[bits(px),bits(py)],input=rows,output=[get(bullets+k*0x2000+o) for k in range(count) for o in (0xc4c,0xc60,0xc68)]))
 index=0
 def arg(machine,address,size,user):machine.reg_write(UC_X86_REG_EAX,index)
 m.mem_write(0x4251d0,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,arg,begin=0x4251d0,end=0x4251d0);selectors=[]
 for index in (0,1):
  for mode in (0,1,0x80000000,0xffffffff):
   put(enemy+0x4518,0xdeadbeef);put(enemy+0x451c,mode);m.reg_write(UC_X86_REG_EDI,enemy);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4202b6,0x422a9b,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
   assert get(enemy+0x4518)==(0 if index==0 else 0x4252d0);selectors.append(dict(index=index,mode=mode,output=[index,get(enemy+0x451c)]))
 empty_resets=[];put(0x4a6ee0,manager)
 for seed in range(32):
  initial=bytearray(b''.join(struct.pack('<I',(seed*0x1234567+n*0x34567)&0xffffffff) for n in range(0x600//4)));initial[0x14:0x18]=bytes(4);m.mem_write(manager,bytes(initial));m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x422550,0x422a9b,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b;assert bytes(m.mem_read(manager,0x600))==bytes(initial);empty_resets.append(seed)
 (ROOT/'artifacts/th16/enemy-callbacks-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,selectors=selectors,emptyResets=empty_resets),separators=(',',':'))+'\n',encoding='utf8');print(len(cases),'retail proximity lists /',len(selectors),'callback selectors /',len(empty_resets),'empty laser resets')
if __name__=='__main__':main()
