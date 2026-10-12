"""Complete444cf0 with recorded effect/popup/sound/item boundaries."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x100000);player,pos,manager,stack,ret=0x70000000,0x70040000,0x70050000,0x700fd000,0x700fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 events=[]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x40e5c0:
   p=get(sp+12);events.append([0,get(sp+8),get(p),get(p+4),get(p+8)]);put(get(sp+4),123);machine.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x44a460:
   p=get(sp+4);events.append([1,get(p),get(p+4),get(p+8),get(sp+8),get(sp+12)])
  elif a==0x45e1f0:events.append([2,get(sp+4),machine.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  else:
   p=get(sp+8);events.append([3,get(sp+4),get(p),get(p+4),get(p+8),get(sp+16),get(sp+20),get(sp+28)])
 for a,cleanup in ((0x40e5c0,24),(0x44a460,12),(0x45e1f0,4),(0x430960,28)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4a6ef8,player);put(0x4a6db8,manager);put(manager+12,manager+0x100);cases=[]
 positions=((0,0,0),(1.25,-3.5,2),(-184.125,413.75,-1),(192,16,0),(.0001,-.0001,0))
 for graze,chain,p,c in itertools.product((-2147483648,-1,0,99999998,99999999,100000000,2147483647),(-1,0,99999999,2147483647),positions,positions):
  put(0x4a57c0,graze);put(0x4a57c4,chain)
  for n,v in enumerate(p):put(player+0x610+n*4,bits(v))
  for n,v in enumerate(c):put(pos+n*4,bits(v))
  put(stack,ret);put(stack+4,pos);m.reg_write(UC_X86_REG_ESP,stack);events.clear();m.emu_start(0x444cf0,ret,count=3000);assert m.reg_read(UC_X86_REG_EIP)==ret
  cases.append(dict(graze=graze,chain=chain,player=p,contact=c,counters=[get(0x4a57c0),get(0x4a57c4)],events=list(events)))
 (ROOT/'artifacts/th16/player-graze-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own player grazes')
if __name__=='__main__':main()
