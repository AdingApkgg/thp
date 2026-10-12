"""Own413cb5 ETEX64 setup and full411e70/415bb0 wall consumers."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OFFSETS=(0xc20,0xc24,0xc28,0xc2c,0xc30,0xc34,0xc38,0xc3c,0xc68,0xc60,0x24,0xc58,0x1460,0x1464,0x1468,0xfa0,0xfa4,0xfa8,0x10d4,0x10dc,0x10e0,0x10f4,0x10f8,0x1100,0xc4c)
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);bullet,manager,anm,file,sprites,stack,ret=0x70001000,0x70008000,0x70010000,0x70004000,0x70006000,0x71ffd000,0x71ffe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def fs(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 events=[]
 def boundary(machine,a,size,user):
  if a==0x4124b0:events.append([1,0]);machine.reg_write(UC_X86_REG_EAX,0)
  elif a==0x45f980:events.append([2,0]);machine.reg_write(UC_X86_REG_EAX,0)
  elif a==0x412670:events.append([3,0])
  elif a==0x45e150:events.append([4,get(machine.reg_read(UC_X86_REG_ESP)+4)])
 for a,n in ((0x4124b0,4),(0x45f980,0),(0x412670,0),(0x47499b,0),(0x45e150,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4a6dac,manager);put(0x4c0f48,anm);put(anm+0x184f4f0,file);put(file+0x11c,sprites);put(0x490eb0,0x4a5788);fs(sprites+0x34,36,17)
 def call(a):
  events.clear();put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);m.emu_start(a,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  return dict(result=m.reg_read(UC_X86_REG_EAX),output=[get(bullet+o) for o in OFFSETS],events=events[:])
 positions=((-200.,-8.),(-192.,0.),(-191.99,.01),(192.,448.),(191.99,447.99),(200.,456.),(0.,0.),(0.,448.),(-150.,100.),(150.,400.))
 rows=[]
 for n in range(2560):
  rate=(0,.25,.5,.99,1,1.01,1.5,2)[n%8];mask=n//8%64;limit=(-1,0,1,2,5)[n//17%5];speed=(-999999.,-999990.,-999989.,-991.,-990.,-989.,0.,2.75)[n//13%8];x,y=positions[n//7%10];angle=(-3.1415927,-1.5707964,-.3,0,.3,1.5707964,3.1415927,200)[n//11%8];bw,bh=((0.,0.),(-1.,300.),(200.,350.),(300.,0.),(384.,448.))[n//19%5];active=n//3%2;index=n//5%2;concurrent=n//23%2;sound=(-1,17)[n//29%2]
  m.mem_write(bullet,bytes(0x2000));fs(0x4a5788,rate);fs(manager+0x48,bw,bh);put(bullet+0x20,3);put(bullet+0x24,2);put(bullet+0xc58,64);put(bullet+0xc72,1);fs(bullet+0x141c,1.5)
  fs(bullet+0xc20,x,y,.1);fs(bullet+0xc2c,-1.25,2.5,.125);fs(bullet+0xc38,2.25,angle);put(bullet+0xc60,index);put(bullet+0xc80,sound);put(bullet+0xc68,active);put(bullet+0xc4c,9)
  put(bullet+0xfa0,15 if active else 0);put(bullet+0xfa4,16 if active else 0);fs(bullet+0xfa8,16 if active else 0);put(bullet+0x1464,17);fs(bullet+0x1468,17.5)
  t=bullet+0xc88+index*0x2c;fs(t,speed,280.,320.,0.);put(t+0x10,limit);put(t+0x14,mask);put(t+0x20,64);put(t+0x24,concurrent);put(t+0x2c+0x10,37);put(t+0x2c+0x20,32768)
  initial=call(0x413860);timeline=[]
  for frame in range(32):
   row=call(0x411e70);timeline.append(row)
   if row['result']==0xffffffff:break
  rows.append(dict(input=[rate,mask,limit,speed,x,y,angle,bw,bh,active,index,concurrent,sound],initial=initial,timeline=timeline))
 (ROOT/'artifacts/th16/bullet-bounce-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} own bounce initializers / {sum(len(r["timeline"]) for r in rows)} full frames')
if __name__=='__main__':main()
