"""Execute retail callbacks 4: spawn 452c10 and update 452e00."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 end,obj,stack=0x70000000,0x70001000,0x7000f000;m.mem_map(end,0x10000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 def call(a):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
 spawns=[]
 for seed,angle,flags in itertools.product((0,1,17,12345,32767,65534,65535),(-3.2,-3.1415927410125732,-1.25,0,3.1415927410125732,3.2),(0,2,0x3c,0xff,0xffffffff)):
  m.mem_write(obj,bytes(0x100));put(obj+0x70,bits(angle));put(obj+0x10,flags);put(0x4db510,seed);put(0x4db514,123);put(0x4db508,54321);put(0x4db50c,77);call(0x452c10)
  spawns.append(dict(args=[seed,angle,flags],result=[get(obj+0x70),get(obj+0x10),get(0x4db510),get(0x4db514),get(0x4db508),get(0x4db50c)]))
 updates=[]
 for state,speed,advanced,rate in itertools.product((-1,0,1,2,3),(-2.,0.,.5,4.,16.,10000.),(0,1),(0,.5,1,1.25)):
  put(obj+0x98,state);put(obj+0x6c,bits(speed));put(obj+0x18,17-advanced);put(obj+0x1c,17);put(0x4d8f58,bits(rate));call(0x452e00)
  updates.append(dict(args=[state,speed,advanced,rate],result=[get(obj+0x98),get(obj+0x6c)]))
 (ROOT/'artifacts/th14/shot-spread-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),spawns=spawns,updates=updates),indent=2)+'\n',encoding='utf-8')
 print(f'{len(spawns)} spread spawns / {len(updates)} accelerating updates')
if __name__=='__main__':main()
