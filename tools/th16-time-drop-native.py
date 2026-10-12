"""TH16 time-scaled drop configuration and scalar consumers; no item factory claim."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);data,stack,ret,ratep=0x70001000,0x7001e000,0x7001f000,0x7001d000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 args=[]
 def arg(machine,address,size,user):machine.reg_write(UC_X86_REG_EAX,args[get(machine.reg_read(UC_X86_REG_ESP)+4)]&0xffffffff)
 m.mem_write(0x4251d0,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,arg,begin=0x4251d0,end=0x4251d0)
 offsets=(0x403c,0x4040,0x4044,0x404c,0x4050,0x3fd0,0x4054)
 setters=[]
 for flags in (0,1,0x80000000,0x80000001):
  for args in ((0,0,0),(1,10,1),(60,3,0),(-1,-2,-3),(0x7fffffff,17,4),(-0x80000000,-17,11)):
   for o,v in zip(offsets,(31,32,0x41a40000,flags,99,77,55)):put(data+o,v)
   put(data+0x4048,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,data);m.emu_start(0x422a26,0x422a9b,count=1000)
   setters.append(dict(flags=flags,args=args,output=[get(data+o) for o in offsets]))
 ticks=[];put(0x490eb0,ratep)
 for rate in (0,.25,.5,.99,1,1.01,1.5,2):
  for current in (-1,0,1,2,60):
   for fraction in (float(current),current+.5):
    put(data+0x403c,99);put(data+0x4040,current);put(data+0x4044,struct.unpack('<I',struct.pack('<f',fraction))[0]);put(data+0x4048,0);put(ratep,struct.unpack('<I',struct.pack('<f',rate))[0])
    if current>0:
     put(stack,ret);put(stack+4,0);m.reg_write(UC_X86_REG_ECX,data+0x403c);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x40d490,ret,count=1000)
    ticks.append(dict(rate=rate,current=current,fraction=fraction,output=[get(data+o) for o in offsets[:3]]))
 decays=[]
 for duration in (1,30,60,0x7fffffff):
  for current in (-1,0,1,15,30,60):
   for amount,minimum in ((10,1),(3,0),(-17,3),(0x7fffffff,-1),(-0x80000000,17)):
    for off,v in ((0x524c,current),(0x525c,duration),(0x5260,minimum),(0x51dc,amount)):put(data+off,v)
    m.reg_write(UC_X86_REG_EDI,data);m.emu_start(0x41d5ee,0x41d620,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x41d620
    decays.append(dict(duration=duration,current=current,amount=amount,minimum=minimum,output=get(data+0x51dc)))
 immunity_setters=[]
 for flags in (0,1,0x80000000,0x80000001):
  for duration in (-2147483648,-999999,-1,0,1,2,60,16777217,2147483647):
   args=[duration]
   for off,v in zip((0,4,8,12,16),(31,32,0x41a40000,ratep,flags)):put(data+0x3ffc+off,v)
   m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_ESP,stack)
   m.emu_start(0x4206bf,0x422a9b,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
   immunity_setters.append(dict(flags=flags,duration=duration,output=[get(data+0x3ffc+o) for o in (0,4,8,16)]))
 damage_setters=[]
 for total in (-2147483648,-1,0,1,17,2147483647):
  for step in (-2147483648,-1,0,1,50,2147483647):
   args=[step];put(data+0x3f88,total);put(data+0x4058,7);put(data+0x405c,9);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_ESP,stack)
   m.emu_start(0x422a61,0x422a9b,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
   damage_setters.append(dict(total=total,step=step,output=[get(data+o) for o in (0x3f88,0x4058,0x405c)]))
 health_setters=[]
 for flags in (0,0x800000,0x40000000,0xffffffff):
  for health in (-2147483648,-1,0,1,1000,2147483647):
   args=[health];put(data+0x4060,flags);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4205ee,0x422a9b,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
   health_setters.append(dict(flags=flags,health=health,output=[get(data+o) for o in (0x3f74,0x3f78,0x3f7c,0x3f80,0x4060)]))
 damage_cases=[]
 for flags in (0,1,2,3,0xffffffff):
  for amount in (-2147483648,-1,0,1,50,2147483647):
   for total in (-2147483648,-1,0,2147483647):
    for o,v in zip(range(0,28,4),(997,1000,100,6979,101,total,flags)):put(data+o,v)
    put(stack,ret);put(stack+4,amount);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,data);m.emu_start(0x41a6d0,ret,count=1000);assert m.reg_read(UC_X86_REG_EIP)==ret
    damage_cases.append(dict(flags=flags,amount=amount,total=total,output=[get(data+o) for o in (0,12,20)]))
 out=ROOT/'artifacts/th16/time-drop-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),setters=setters,ticks=ticks,decays=decays,damageSetters=damage_setters,damageCases=damage_cases,healthSetters=health_setters,immunitySetters=immunity_setters),indent=2)+'\n',encoding='utf-8');print(f'{len(setters)} native setters, {len(ticks)} countdowns, {len(decays)} death-count scalar cases; {len(damage_setters)} damage-drop setters; {len(damage_cases)} health consumers; {len(health_setters)} health setters; {len(immunity_setters)} damage immunity setters')
if __name__=='__main__':main()
