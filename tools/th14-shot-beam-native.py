"""Retail 4523a0/4523f0, with ANM and DirectSound delivery boundaries."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 end,obj,spec,area,vm,voice,player,env,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x70004000,0x70005000,0x70010000,0x70030000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 events=[];present=True
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vm if present else 0)
  elif a==0x47f140:events.append(['interrupt',get(sp+8)])
  elif a==end+0x100:events.append(['pan',get(sp+8)])
  elif a==0x46e550:events.append(['stop',get(sp+4)])
  else:events.append(['sound',get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
 for a,n in ((0x47f0a0,4),(0x47f140,8),(0x46e470,4),(0x46e550,4),(end+0x100,8),(0x4854a0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3')
  if a!=0x4854a0:m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(voice,voice+0x100);put(voice+0x140,end+0x100);put(0x4f97bc,voice);put(0x4db67c,player)
 def call(a):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
 def setup():
  for p,n in ((obj,0x100),(area,0x100),(vm,0x600),(spec,0x100),(player,0x19000),(env,0x200)):m.mem_write(p,bytes(n))
  put(obj+0xbc,spec);put(obj+0xc0,area);put(obj+0x14,73);put(area+0x10,0x85);put(area+0x24,bits(333));put(area+0x28,bits(12));put(area+0x2c,bits(17));put(area+0x30,bits(19));put(area+0x34,bits(.5));put(vm+0x18,7);put(vm+0x80,bits(23));put(vm+0x78,bits(2));events.clear()
 spawns=[]
 for flags,x in itertools.product((0,1,2,0xff,0xffffffff),(-192.,-12.25,0.,99.5,192.)):
  setup();put(obj+0x10,flags);put(obj+0xb0,bits(144));put(area+0x90,4);put(player+0x5e0,bits(x));call(0x4523a0)
  spawns.append(dict(args=[flags,x],result=[get(obj+0xb0),get(obj+0x10),get(area+0x24),get(area+0x90)],events=events[:]))
 rows=[]
 for n in range(2160):
  setup();option=1+n%8;state=(0,1,2)[n//8%3];length=(-1.,0.,18.,504.,511.,512.,522.,700.)[n//24%8];angle=(-3.2,-1.5707963705062866,0.,.37,3.2)[n//192%5];gate=n//960%9
  # Cover each retirement gate independently, plus frozen hit transitions,
  # missing ANM, no dialogue object and continued beam during a Bomb.
  gate=n%10;focused=int(gate==1);firing=int(gate!=2);count=option-1 if gate==3 else 8;power=4;cached=3 if gate==4 else power;blocked=int(gate==5);enemy=int(gate!=6);present=gate!=7;dialogue=gate!=8
  hit=n//10%2;last=n//20%2;x=(-192.,-12.25,0.,99.5,192.)[n//40%5];ox=-5000+n*3;oy=38000+n;put(spec+0x20,option);put(spec+0x14,bits(angle));put(obj+0xb0,bits(length));put(obj+0x98,state);put(obj+0xa4,hit);put(obj+0xa8,last)
  put(player+0x5e0,bits(x));put(player+0xd664+option*0xe4,ox);put(player+0xd668+option*0xe4,oy);put(player+0x1833c,0 if firing else -1);put(player+0x18334,count);put(player+0x18348+option*4,cached);put(player+0x184b0,focused);put(env+0x194,blocked);put(0x4db550,env if dialogue else 0);put(0x4db544,env if enemy else 0);put(0x4f5858,power*40);put(0x4f5860,40)
  call(0x4523f0)
  result=[*[get(obj+o) for o in (0x54,0x58,0x5c,0x70,0xb0,0x98,0xa4,0xa8,0x14)],*[get(area+o) for o in (0x10,0x24,0x2c,0x30,0x34)],*[get(vm+o) for o in (0x18,0x80,0x78)],get(player+0x18348+option*4)]
  rows.append(dict(args=[option,state,length,angle,focused,firing,count,cached,blocked if dialogue else 0,enemy,int(present),hit,last,x,ox,oy],result=result,events=events[:]))
 (ROOT/'artifacts/th14/shot-beam-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),spawns=spawns,rows=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(spawns)} beam spawns / {len(rows)} beam updates')
if __name__=='__main__':main()
