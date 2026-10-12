"""Own416840 primary cancellation and416c20/416d20 circle eligibility."""
import hashlib,importlib,json,struct,itertools
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);manager,bullet,node,center,stack,ret=0x70000000,0x71f00000,0x71f03000,0x71f04000,0x71ffd000,0x71ffe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,vs):m.mem_write(p,struct.pack('<'+'f'*len(vs),*vs))
 events=[]
 def boundary(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x45f980:events.append([0,get(bullet+0x4b8)]);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x40e5c0:
   p=get(sp+12);events.append([1,get(sp+8),get(p),get(p+4),get(p+8)]);put(get(sp+4),123);machine.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif address==0x45e1f0:events.append([2,get(sp+4),machine.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  elif address==0x416840:events.append([3])
 for address,cleanup in ((0x45f980,0),(0x40e5c0,24),(0x45e1f0,4)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4a6dac,manager);rows=[]
 for state,flags,rate,position,effect,rewards in itertools.product((1,2,3,4),(3,0x203),(0,.25,.5,.99,1,1.01,1.5,2),((0,224,2),(-220,470,.125),(3.25,-9.5,-2),(-224,0,0),(224,0,0),(0,-32,0),(0,480,0)),(-1,6,275),(0,1,3)):
  m.mem_write(bullet,bytes(0x2000));put(bullet+0x20,flags);put(bullet+0xc72,state);put(bullet+0xc5c,effect);floats(bullet+0xc20,position);floats(bullet+0xc2c,(1.25,-.75,.5));put(bullet+0x144c,19);put(bullet+0x1450,20);floats(bullet+0x1454,(20.5,));put(bullet+0x145c,1);floats(0x4a5788,(rate,));put(stack,ret);put(stack+4,rewards);put(manager+0x1403b14,0xffffffff)
  events.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);m.emu_start(0x416840,ret,count=10000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(state=state,flags=flags,rate=rate,position=position,effect=effect,rewards=rewards,output=[get(bullet+o) for o in (0x20,0xc20,0xc24,0xc28,0x144c,0x1450,0x1454,0x4b8,0xc72)]+[get(manager+0x1403b14)],events=list(events)))
 # Execute both circle walkers with their downstream cancellation as a sink.
 m.mem_write(0x416840,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=0x416840,end=0x416840);circles=[]
 positions=((bits(0),bits(0)),(bits(14),bits(0)),(bits(14.00001),bits(0)),(bits(0),bits(14)),(bits(10),bits(10)),(0x80000000,0),(0x7fc12345,0),(0x7f800000,0))
 for state in range(6):
  for delay in (0,1,-1):
   for delayed in (0,1):
    for hitbox in (bits(-1),0,bits(8),0x7f800000):
     for radius in (bits(-1),0,bits(10),0x7fc12345):
      for x,y in positions:
       m.mem_write(bullet,bytes(0x2000));put(bullet+0xc72,state);put(bullet+0x24,delay);put(bullet+0xc40,hitbox);put(bullet+0xc20,x);put(bullet+0xc24,y);put(manager+0x70,node);put(node,bullet);put(node+4,0);put(center,0);put(center+4,0);put(stack,ret);put(stack+4,center);put(stack+8,0)
       events.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM2,radius);m.emu_start(0x416d20 if delayed else 0x416c20,ret,count=2000);assert m.reg_read(UC_X86_REG_EIP)==ret
       circles.append(dict(state=state,delay=delay,delayed=delayed,hitbox=hitbox,radius=radius,x=x,y=y,match=bool(events)))
 requests=[];arg=0;enemy=center+0x100;laser=center+0x2000;bp=stack+0x800
 put(0x4a6ee0,laser);put(laser+0x14,0)
 def request_hook(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x425200:machine.reg_write(UC_X86_REG_XMM0,arg)
  elif address==0x416c20:
   p=get(sp+4);events.append([4,machine.reg_read(UC_X86_REG_XMM2)&0xffffffff,get(sp+8),get(p),get(p+4),get(p+8)])
  elif address==0x416f40:events.append([5])
 for address,cleanup in ((0x425200,4),(0x416c20,8),(0x416f40,4)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,request_hook,begin=address,end=address)
 for op in (613,615,616):
  for arg in (0,bits(-1),bits(10),bits(800),0x7fc12345,0x7f800000):
   for position in ((0,0,0),(bits(1),bits(2),bits(3))):
    for n,v in enumerate(position):put(enemy+0x44+n*4,v)
    events.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_EDI,enemy)
    m.emu_start(0x421655 if op==613 else 0x42219e if op==615 else 0x42221d,0x422a9b,count=3000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
    requests.append(dict(op=op,radiusBits=arg,position=position,events=list(events)))
 out=ROOT/'artifacts/th16/bullet-cancel-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,circles=circles,requests=requests),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} cancel consumers; {len(circles)} circle eligibility cases; {len(requests)} ECL requests')
if __name__=='__main__':main()
