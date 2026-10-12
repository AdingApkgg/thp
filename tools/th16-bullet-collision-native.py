"""Full4124b0 primary VM, with player/graze/effect boundaries; actual4173f0."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x1600000);manager,bullet,vm,stack,ret=0x70000000,0x71500000,0x71504000,0x715fd000,0x715fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 events=[];probe_result=0
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a in (0x4438c0,0x4439e0):
   p=get(sp+4);sx=machine.reg_read(UC_X86_REG_XMM2)&0xffffffff if a==0x4439e0 else get(get(sp+8));sy=0 if a==0x4439e0 else get(get(sp+8)+4)
   events.append([0,int(a==0x4439e0),get(p),get(p+4),get(p+8),sx,sy]);machine.reg_write(UC_X86_REG_EAX,probe_result)
  elif a==0x4174d0:put(machine.reg_read(UC_X86_REG_ECX)+0x490,get(sp+4))
  elif a==0x444cf0:
   p=get(sp+4);events.append([2,get(p),get(p+4),get(p+8)])
  elif a==0x40e5c0:
   p=get(sp+12);events.append([1,get(sp+8),get(p),get(p+4),get(p+8)]);put(get(sp+4),123);machine.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x46f2e0:machine.reg_write(UC_X86_REG_EAX,vm)
 for a,cleanup in ((0x4438c0,12),(0x4439e0,8),(0x4174d0,4),(0x444cf0,4),(0x40e5c0,24),(0x46f2e0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4a6dac,manager);m.mem_write(0x4d9dc4,bytes(12));cases=[]
 for flags,delay,probe_result,effect,rate,nativeflags,width in itertools.product((0,2,6,0x12,0x42,0x52,0x56),(0,1,-1),(0,1,2,7),(-1,4),(0,.5,1,2),(0,0x60000,0xffffffff),(-1,0,8)):
  m.mem_write(bullet,bytes(0x2000));m.mem_write(vm,bytes(0x700));put(bullet+0x20,flags);put(bullet+0x24,delay);put(bullet+0xc72,1);put(bullet+0xc5c,effect);put(bullet+0x558,nativeflags);put(bullet+0x4b8,9)
  for off,vals in ((0x54,(7,8,9)),(0xc20,(1.25,-2.5,.125)),(0xc2c,(1.25,-.75,.5)),(0xc40,(width,12)),(0x141c,(1.5,))):
   for n,v in enumerate(vals):put(bullet+off+n*4,bits(v))
  put(0x4a5788,bits(rate));put(stack,ret);put(stack+4,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);events.clear();m.emu_start(0x4124b0,ret,count=2000);assert m.reg_read(UC_X86_REG_EIP)==ret
  interpolation=[get(vm+off) for off in list(range(0x8c,0xbc,4))+[0xc8,0xcc,0xd0,0xdc,0xe0]] if any(e[0]==1 for e in events) else []
  cases.append(dict(flags=flags,delay=delay,probe=probe_result,effect=effect,rate=rate,nativeflags=nativeflags,width=width,result=m.reg_read(UC_X86_REG_EAX),output=[get(bullet+off) for off in (0x20,0xc72,0x4b8,0x558,0x54,0x58,0x5c)],events=list(events),interpolation=interpolation))
 out=ROOT/'artifacts/th16/bullet-collision-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own bullet collision consumers')
if __name__=='__main__':main()
