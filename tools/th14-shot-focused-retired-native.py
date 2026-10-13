"""Retired target identity 74 is absent; a distinct live target 73 remains.

Retail TH14 spawn 451af0/update 451cd0. ANM lookup/interrupt are boundaries;
nearest/id lookup, target flags, math and timer operations execute natively.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,spec,area,vm,player,manager,enemy,resource,group,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x70004000,0x70010000,0x70030000,0x70040000,0x70060000,0x70070000,0x700ff000;m.mem_map(end,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 interrupts=[]
 def boundary(machine,a,size,user):
  if a==0x47f140:interrupts.append(get(m.reg_read(UC_X86_REG_ESP)+8))
  else:m.reg_write(UC_X86_REG_EAX,vm)
 for a,cleanup in ((0x47f0a0,4),(0x47f420,0),(0x47f140,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def timer(p,value):put(p,value-1);put(p+4,value);floats(p+8,value);put(p+12,0x4d8f58);put(p+16,1)
 def call(a):
  m.mem_write(stack-0x2000,bytes(0x2100));put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
 def setup(power,flag,targetpos,rate=1):
  interrupts.clear();m.mem_write(obj,bytes(0x100));m.mem_write(area,bytes(0x100));m.mem_write(vm,bytes(0x600));m.mem_write(player,bytes(0x19000));m.mem_write(manager,bytes(0x3000));m.mem_write(enemy,bytes(0x6000))
  put(0x4db544,manager);put(manager+0xd0,enemy+0x14d8);put(enemy+0x14d8,enemy);put(enemy+0x11e4,73);put(enemy+0x5244,flag);floats(enemy+0x1234,*targetpos,0)
  put(0x4db67c,player);put(0x4db52c,manager+0x1000);put(0x4db550,manager+0x2000);put(player+0x684,1);put(player+0x688,resource);put(resource+0x20,4)
  for j in range(10):put(resource+0xe0+j*4,group+j*0x200);floats(group+j*0x200+0xbc,40+j*2);m.mem_write(group+j*0x200+0xb2,struct.pack('<h',20+j))
  put(0x4f5858,power*40);put(0x4f5860,40);floats(0x4d8f58,rate);put(obj+0x14,1);put(obj+0xbc,spec);put(obj+0xc0,area);floats(spec+0xc,40);put(area+0x10,0xa5)
  floats(obj+0x54,0,100,0);floats(obj+0x6c,8,-1.25);put(obj+0x98,1);timer(obj+0x18,0);timer(obj+0x2c,0);timer(obj+0x40,0);put(vm+0x18,7);floats(vm+0x60,1,1)
 def state():
  target=get(obj+0x9c)
  return [int(target==enemy),get(obj+0xa0),get(obj+0x70),get(obj+0xb8),get(area+0x10),get(area+0x14),get(area+0x18),*[get(obj+0x40+j*4) for j in range(3)],get(vm+0x60),get(vm+0x64),get(vm+0x18),get(obj+0x6c),get(obj+0x98),get(player+0x1834c),get(obj+0xac),*[get(obj+0x2c+j*4) for j in range(3)]]
 spawns=[]
 for power in range(5):
  for flag in (0,1,0x20,0x4000000,0x8000000,0x400000):
   for pos in ((0,100),(0,-60),(0,-59.875),(40,0),(-80,140),(192,448)):
    setup(power,flag,pos);call(0x451af0);spawns.append(dict(power=power,flags=flag,targetPosition=pos,result=state()))
 updates=[]
 for n in range(2304):
  power=1+n%4;flag=(0,1,0x4000000,0x400000)[n//4%4];pos=((0,100),(10,100),(120,100),(240,100),(-20,40),(0,448))[n//16%6];rate=(0.,.5,1.,1.25)[n//96%4]
  setup(power,flag,pos,rate);age=(-1,0,9,10,30,31,240)[n%7];decay=(4,5,10)[n//7%3];steering=(0,11,12)[n//21%3]
  focused=n//63%2;firing=n//126%2;blocked=n//252%2;life=1+n//504%2;target=1;cached=power if n//2016%2 else 0
  timer(obj+0x18,age);timer(obj+0x40,decay);timer(obj+0x2c,steering);put(obj+0x9c,enemy if target else 0);put(obj+0xa0,74 if target else 0);put(obj+0xb8,bits(8));put(obj+0xac,19);put(area+0x14,bits(40));put(player+0x184b0,focused);put(player+0x1833c,0 if firing else 0xffffffff);put(player+0x1834c,cached);put(player+0x684,life);put(manager+0x2000+0x194,blocked)
  bomb=n//128%3;put(manager+0x1000+0x40,bomb)
  before=state();call(0x451cd0);updates.append(dict(power=power,flags=flag,targetPosition=pos,rate=rate,age=age,decay=decay,steering=steering,focused=focused,firing=firing,blocked=blocked,life=life,target=target,cached=cached,bomb=bomb,before=before,result=state(),interrupts=interrupts[:]))
 out=ROOT/'artifacts/th14/shot-focused-retired-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),spawns=spawns,updates=updates),indent=2)+'\n',encoding='utf-8');print(f'{len(spawns)} focused spawns, retired-target {len(updates)} focused updates.')
if __name__=='__main__':main()
