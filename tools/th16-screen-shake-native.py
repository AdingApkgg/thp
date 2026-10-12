"""Retail 517 dispatch, shake constructor, timer, RNG and raw camera offsets."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 group=img.data[next(raw+0x422d70-base+517-300 for _,base,size,raw,n in img.sections if base<=0x422d70<base+size)]
 assert img.u32(0x422ab8+group*4)==0x421681
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,obj,callback,stack=0x70000000,0x70001000,0x70002000,0x7000f000;m.mem_map(base,0x10000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 fput=lambda p,v:m.mem_write(p,struct.pack('<f',v))
 args=[];created=[]
 def hook(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x4749ac:m.reg_write(UC_X86_REG_EAX,obj)
  elif address==0x401730:
   created.append(get(sp+4));m.reg_write(UC_X86_REG_EAX,callback)
  elif address==0x4251d0:m.reg_write(UC_X86_REG_EAX,args[get(sp+4)]&0xffffffff)
 for p,cleanup in ((0x4749ac,0),(0x401730,4),(0x401300,8),(0x4251d0,4)):
  m.mem_write(p,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=p,end=p)
 cases=[]
 for duration,start,end in ((30,12,0),(1,8,-4),(0,1,2),(-1,2,3),(17,-11,7),(200,2147483647,-2147483648),(2147483647,-2147483648,2147483647)):
  for rate in (.5,.99,1,1.01,1.25):
   for seed in (0,1,65535):
    for stopped in (0,1):
     m.mem_write(base,bytes(0xf000));args[:]=[duration,start,end];created.clear();put(0x4c0f40,0);put(0x4a6d80,seed);put(0x4a6d84,0);fput(0x4a5788,rate);put(0x4a5884,0)
     put(stack,base+0xe000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base+0x3000);put(base+0x3000+0x40ec,base+0x4000);put(base+0x4004,base+0x5000)
     m.emu_start(0x421681,0x422a9b,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b;assert created==[0x45cd30]
     initial=[get(obj+p) for p in (0x18,0x1c,0x20,0x2c,0x30,0x34,0x3c)]
     fput(0x4c1788,3);fput(0x4c178c,-5);fput(0x4d9d34,1.5);put(0x4c0f40,stopped);rows=[]
     for frame in range(40):
      put(stack,base+0xe000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj)
      m.emu_start(0x45cd30,base+0xe000,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base+0xe000
      rows.append([m.reg_read(UC_X86_REG_EAX),get(obj+0x2c),get(obj+0x30),get(obj+0x34),get(0x4c1788),get(0x4c178c),get(0x4a6d80),get(0x4a6d84)])
      if rows[-1][0]==7:break
     cases.append(dict(duration=duration,start=start,end=end,rate=rate,seed=seed,stopped=stopped,initial=initial,rows=rows))
 out=ROOT/'artifacts/th16/screen-shake-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases))+'\n',encoding='utf8');print(f'{len(cases)} retail shake timelines, {sum(len(c["rows"]) for c in cases)} frames.')
if __name__=='__main__':main()
