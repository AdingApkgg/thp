"""Own413d1f offscreen hold setup and full411e70/4162d0 timelines."""
import hashlib,importlib,itertools,json,math,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OFFSETS=(0xc20,0xc24,0xc28,0xc2c,0xc30,0xc34,0xc68,0xc60,0x24,0xc58,0x1460,0x1464,0x1468,0xfa0,0xfa4,0xfa8,0x12b8,0x12bc,0x12c0,0x12ec)
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);bullet,anm,file,sprites,stack,ret,norm=0x70001000,0x70010000,0x70004000,0x70006000,0x71ffd000,0x71ffe000,0x71ffe100
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def fput(p,v):m.mem_write(p,struct.pack('<f',v))
 def fget(p):return struct.unpack('<f',m.mem_read(p,4))[0]
 events=[]
 def boundary(machine,address,size,user):
  if address==0x4124b0:events.append(1);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x45f980:events.append(2);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x412670:events.append(3)
  elif address==norm:
   sp=machine.reg_read(UC_X86_REG_ESP);dest=get(sp+4);src=get(sp+8);x,y=fget(src),fget(src+4)
   f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
   length=f32(math.sqrt(f32(f32(x*x)+f32(y*y))));inverse=f32(1/length) if length else 0
   fput(dest,f32(x*inverse));fput(dest+4,f32(y*inverse));machine.reg_write(UC_X86_REG_EAX,dest)
 for address,cleanup in ((0x4124b0,4),(0x45f980,0),(0x412670,0),(0x47499b,0),(norm,8)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x48b29c,norm);put(0x4c0f48,anm);put(anm+0x184f4f0,file);put(file+0x11c,sprites);put(0x490eb0,0x4a5788)
 def call(address):
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);events.clear();m.emu_start(address,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  return dict(result=m.reg_read(UC_X86_REG_EAX),output=[get(bullet+o) for o in OFFSETS],events=events[:])
 locations=((-220,40),(220,40),(0,-100),(0,470),(-200.5,224),(200.5,224),(0,-18),(0,466),(0,224),(7.125,9.25))
 cases=[]
 for n in range(1920):
  rate=(0,.25,.5,.99,1,1.01,1.5,2)[n%8];duration=(-1,0,1,3,8,100)[n//8%6];mode=(0,1,8,-1)[n//48%4];x,y=locations[n//192%10];angle=(-3.1415927,-1.5707964,-.3,0,.3,1.5707964,3.1415927,200)[n//13%8];active=n//7%2;index=n//11%2;concurrent=n//17%2;grace=n//23%2
  m.mem_write(bullet,bytes(0x2000));fput(0x4a5788,rate);put(bullet+0x20,3);put(bullet+0x24,2);put(bullet+0xc58,grace);put(bullet+0xc72,1);fput(bullet+0x141c,1.5)
  m.mem_write(bullet+0xc20,struct.pack('<3f',x,y,.1));m.mem_write(bullet+0xc2c,struct.pack('<3f',-1.25,2.5,.125));fput(bullet+0xc38,2.25);fput(bullet+0xc3c,angle);put(bullet+0xc60,index);put(bullet+0xc80,-1);put(bullet+0xc68,active)
  put(bullet+0xfa0,15 if active else 0);put(bullet+0xfa4,16 if active else 0);fput(bullet+0xfa8,16 if active else 0);put(bullet+0x1464,17);fput(bullet+0x1468,17.5)
  t=bullet+0xc88+index*0x2c;put(t+0x10,duration);put(t+0x14,mode);put(t+0x20,0x100);put(t+0x24,concurrent);fput(sprites+0x38,17);fput(sprites+0x34,36)
  initial=call(0x413860);timeline=[]
  for frame in range(32):
   result=call(0x411e70);timeline.append(result)
   if result['result']==0xffffffff:break
  cases.append(dict(input=[rate,duration,mode,x,y,angle,active,index,concurrent,grace],initial=initial,timeline=timeline))
 (ROOT/'artifacts/th16/bullet-hold-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} own offscreen-hold initializers / {sum(len(r["timeline"]) for r in cases)} frames')
if __name__=='__main__':main()
