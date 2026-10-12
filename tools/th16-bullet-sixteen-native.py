"""Whole413860 +411e70, ETEX16 and positional-audio ETEX2048."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OFFSETS=(0xc20,0xc24,0xc28,0xc2c,0xc30,0xc34,0xc38,0xc3c,0xc68,0xc60,0x24,0x1460,0x1464,0x1468,0xfa0,0xfa4,0xfa8,0xfd0,0x1078,0x107c,0x1080,0x108c,0x1090,0x10ac,0x10b0,0x10b4,0x10b8,0x10bc,0x1314,0x1318,0x131c,0x1320,0x1324)
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);bullet,anm,file,sprites,player,stack,ret=0x70001000,0x70010000,0x70004000,0x70006000,0x70008000,0x71ffd000,0x71ffe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def fput(p,v):m.mem_write(p,struct.pack('<f',v))
 events=[]
 def boundary(machine,address,size,user):
  if address==0x4124b0:events.append([1,0,0]);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x45f980:events.append([2,0,0]);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x412670:events.append([3,0,0])
  elif address==0x45e150:events.append([4,get(machine.reg_read(UC_X86_REG_ESP)+4),0])
  elif address==0x45e1f0:events.append([5,get(machine.reg_read(UC_X86_REG_ESP)+4),machine.reg_read(UC_X86_REG_XMM2)&0xffffffff])
 for address,cleanup in ((0x4124b0,4),(0x45f980,0),(0x412670,0),(0x45e150,8),(0x45e1f0,4),(0x47499b,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4c0f48,anm);put(anm+0x184f4f0,file);put(file+0x11c,sprites);put(0x490eb0,0x4a5788);put(0x4a6ef8,player);m.mem_write(player+0x610,struct.pack('<fff',-15.5,400,0))
 def call(address):
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);events.clear();m.emu_start(address,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
 def snapshot():return dict(output=[get(bullet+o) for o in OFFSETS],events=list(events))
 cases=[]
 for n in range(2048):
  rate=(0,.25,.5,.99,1,1.01,1.5,2)[n%8];duration=(0,1,3,17,100,-1)[(n//8)%6];index=(n//48)%2;concurrent=(n//96)%2;active=(n//192)%2;audio=n>=512
  saved=n//29%2;accel=(-1000000,-999990,-.25,0,.5,1.125)[(n//7)%6];mode=(0,1,2,3,4)[(n//17)%5];limit=(0,1,2,3,-1)[(n//19)%5];spare=123;direction=(-1000000,-999990,-7,-.01,0,.5,7,999990,1000000,9999990,10000000)[(n//11)%11];angle=(-3.1415927,-.3,0,3.1415927,500)[(n//13)%5];sound=12 if n%3 else -1
  m.mem_write(bullet,bytes(0x2000));fput(0x4a5788,rate);put(bullet+0x20,3);put(bullet+0x24,2);put(bullet+0xc58,10000);put(bullet+0xc72,1)
  for j,v in enumerate((7.125,9.25,.1)):fput(bullet+0xc20+j*4,v)
  for j,v in enumerate((-1.25,2.5,.125)):fput(bullet+0xc2c+j*4,v)
  fput(bullet+0xc38,2.25);fput(bullet+0xc3c,angle);put(bullet+0xc60,index);put(bullet+0xc80,sound);put(bullet+0xc68,active)
  put(bullet+0xfa0,15 if active else 0);put(bullet+0xfa4,16 if active else 0);fput(bullet+0xfa8,16 if active else 0);fput(bullet+0x1018,.125)
  put(bullet+0x1464,17);fput(bullet+0x1468,17.5)
  fput(bullet+0x1314,3.75);fput(bullet+0x1318,-.5);m.mem_write(bullet+0x131c,struct.pack('<3f',11.25,40.5,7.25))
  t=bullet+0xc88+index*0x2c
  if saved:put(t+0x20,0x800000);put(t+0x24,concurrent);t+=0x2c
  if audio:put(t+0x10,24);put(t+0x20,2048);put(t+0x24,concurrent);t+=0x2c
  fput(t,direction);fput(t+4,accel);fput(t+8,.25);put(t+0x10,duration);put(t+0x14,limit);put(t+0x18,mode);put(t+0x1c,spare);put(t+0x20,16);put(t+0x24,concurrent)
  call(0x413860);initial=snapshot();timeline=[]
  for frame in range(64):call(0x411e70);timeline.append(snapshot())
  cases.append(dict(n=n,rate=rate,duration=duration,index=index,concurrent=concurrent,active=active,accel=accel,direction=direction,angle=angle,sound=sound,audio=audio,mode=mode,limit=limit,spare=spare,saved=saved,initial=initial,timeline=timeline))
 (ROOT/'artifacts/th16/bullet-sixteen-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} native ETEX16/2048 initializers / {len(cases)*64} frames')
if __name__=='__main__':main()
