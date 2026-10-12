"""Retail413860 initializer + 411e70 timelines; ETEX8 math/timers execute natively."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OFFSETS=(0xc20,0xc24,0xc28,0xc2c,0xc30,0xc34,0xc38,0xc3c,0xc68,0xc60,0x24,0x1460,0x1464,0x1468,0xfa0,0xfa4,0xfa8,0xfd0,0x1030,0x1034,0x1038,0x1044,0x1048,0x1064)
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);bullet,anm,file,sprites,stack,ret=0x70001000,0x70010000,0x70004000,0x70006000,0x71ffd000,0x71ffe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def fput(p,v):m.mem_write(p,struct.pack('<f',v))
 events=[]
 def boundary(machine,address,size,user):
  if address==0x4124b0:events.append(1);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x45f980:events.append(2);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x412670:events.append(3)
  elif address==0x45e150:events.append(100+get(machine.reg_read(UC_X86_REG_ESP)+4))
 for address,cleanup in ((0x4124b0,4),(0x45f980,0),(0x412670,0),(0x45e150,8),(0x47499b,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4c0f48,anm);put(anm+0x184f4f0,file);put(file+0x11c,sprites);put(0x490eb0,0x4a5788)
 def call(address):
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);events.clear();m.emu_start(address,ret,count=100000)
  assert m.reg_read(UC_X86_REG_EIP)==ret
 def snapshot():return dict(output=[get(bullet+o) for o in OFFSETS],events=list(events))
 cases=[]
 for n in range(768):
  rate=(0,.25,.5,.99,1,1.01,1.5,2)[n%8];duration=(0,1,3,17,100,-1)[(n//8)%6];index=(n//48)%2;concurrent=(n//96)%2;active=(n//192)%2
  accel=(-.25,0,.5,1.125)[(n//7)%4];turn=(-7,-.01,0,.5,7)[(n//11)%5];angle=(-3.1415927,-.3,0,3.1415927,500)[(n//13)%5];sound=12 if n%3 else -1
  m.mem_write(bullet,bytes(0x2000));fput(0x4a5788,rate);put(bullet+0x20,3);put(bullet+0x24,2);put(bullet+0xc58,10000);put(bullet+0xc72,1)
  for j,v in enumerate((7.125,9.25,.1)):fput(bullet+0xc20+j*4,v)
  for j,v in enumerate((-1.25,2.5,.125)):fput(bullet+0xc2c+j*4,v)
  fput(bullet+0xc38,2.25);fput(bullet+0xc3c,angle);put(bullet+0xc60,index);put(bullet+0xc80,sound);put(bullet+0xc68,active)
  put(bullet+0xfa0,15 if active else 0);put(bullet+0xfa4,16 if active else 0);fput(bullet+0xfa8,16 if active else 0)
  put(bullet+0x1464,17);fput(bullet+0x1468,17.5)
  t=bullet+0xc88+index*0x2c;fput(t,accel);fput(t+4,turn);put(t+0x10,duration);put(t+0x20,8);put(t+0x24,concurrent)
  call(0x413860);initial=snapshot();timeline=[]
  for frame in range(32):call(0x411e70);timeline.append(snapshot())
  cases.append(dict(n=n,rate=rate,duration=duration,index=index,concurrent=concurrent,active=active,accel=accel,turn=turn,angle=angle,sound=sound,initial=initial,timeline=timeline))
 out=ROOT/'artifacts/th16/bullet-eight-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases))+'\n',encoding='utf-8');print(f'{len(cases)} native ETEX8 initializers / {len(cases)*32} full bullet frames')
if __name__=='__main__':main()
