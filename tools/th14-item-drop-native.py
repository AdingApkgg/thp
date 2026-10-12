"""Retail ECL 509 -> 421560/4215b0, actual RNG and scatter math.
Only ItemManager's 4397b0 allocation factory and memset are controlled sinks.
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
 base,stack=0x70000000,0x7000f000;m.mem_map(base,0x10000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 m.mem_write(0x4db508,struct.pack('<HHI',54321,0,123))
 requests=[]
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x4397b0:
   p=get(sp+8);requests.append([get(sp+4),get(p),get(p+4),get(p+8),get(sp+16),get(sp+20),get(sp+24)]);m.reg_write(UC_X86_REG_EAX,0)
  else:m.mem_write(get(sp+4),bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,get(sp+4))
 for a,cleanup in ((0x4397b0,24),(0x48f980,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 rows=[]
 for seed in (0,1,12345,65535):
  for flags in (0,0x10,0x20,0x21,0x30):
   for n in range(8):
    requests.clear();m.mem_write(base,bytes(0x8000))
    primary=n%3;counts=[n%4,(n*3)%5,*[0]*10,100+n];position=(12.25,99.5,2) if n%2 else (-180,80,0);spread=(32+n*3.25,32-n*.75)
    for off,f in zip((0x44,0x48,0x4c),position):put(base+off,bits(f))
    for k,v in enumerate([primary,*counts]):put(base+0x3f90+k*4,v)
    for k,f in enumerate(spread):put(base+0x3fc8+k*4,bits(f))
    m.mem_write(0x4db510,struct.pack('<HHI',seed,0,0));put(0x4f58b8,flags);put(0x4db660,base+0x8000)
    m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack)
    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.emu_start(0x4277fd,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
    rows.append(dict(seed=seed,flags=flags,primary=primary,counts=counts,position=position,spread=spread,requests=requests[:],result=[*[get(base+0x3f90+k*4) for k in range(14)],int.from_bytes(m.mem_read(0x4db510,2),'little'),get(0x4db514)]))
 assert int.from_bytes(m.mem_read(0x4db508,2),'little')==54321 and get(0x4db50c)==123, 'item path consumed the ANM/shake stream'
 out=ROOT/'artifacts/th14/item-drop-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail ECL 509/drop scatter cases.')
if __name__=='__main__':main()
