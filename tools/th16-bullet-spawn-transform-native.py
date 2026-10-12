"""Whole413860 for ETEX8192 request assembly, 32768 tags and finite65536 loops."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x200000);b,player,stack,ret=0x70001000,0x70005000,0x701fd000,0x701fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 requests=[];events=[]
 def boundary(machine,address,size,user):
  if address==0x414da0:
   p=get(machine.reg_read(UC_X86_REG_ESP)+4);requests.append(bytes(machine.mem_read(p,0x380)).hex());events.append([0,get(b+0xc60)])
  elif address==0x416840:events.append([1,get(b+0xc60)])
 for address,cleanup in ((0x414da0,4),(0x416840,4),(0x47499b,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4a6ef8,player);m.mem_write(player+0x610,struct.pack('<fff',-15.5,400,0));cases=[]
 for n in range(512):
  m.mem_write(b,bytes(0x2000));index=n%4;active=(0,1,16)[(n//4)%3];counter=(0,1,3)[(n//12)%3];concurrent=(n//36)%2
  angle=(-3.1415927,-.3,0.,500.)[(n//7)%4];direction=(-1000000.,-999990.,-7.,-.01,0.,7.,999990.,1000000.)[(n//11)%8];speed=(-1000000.,-999990.,0.,.5,4.)[(n//13)%5]
  put(b+0xc60,index);put(b+0xc64,counter);put(b+0xc68,active);put(b+0xc4c,7);put(b+0xc80,0xffffffff)
  for j,v in enumerate((7.125,9.25,.1)):put(b+0xc20+j*4,bits(v))
  put(b+0xc38,bits(2.25));put(b+0xc3c,bits(angle))
  for j in range(18):
   for k in range(8):put(b+0xc88+j*0x2c+k*4,(n*0x12345+j*99+k)&0xffffffff)
  t=b+0xc88+index*0x2c
  for off,v in zip((0,4,8,12,16,20,24,28,32,36,40),(bits(direction),bits(.375),bits(speed),bits(1.25),(n%6)-1,(0,1,9,17,-1)[n%5],(n%5)-1,(n%3)-1,8192,concurrent,0x12345678)):put(t+off,v)
  for off,v in ((0x3c,n%44),(0x40,n%16),(0x44,n%2),(0x4c,16384),(0x50,0),(0x54,0)):put(t+off,v)
  loop=t+0x58;put(loop+0x10,index);put(loop+0x14,1+n%4);put(loop+0x20,65536);put(loop+0x24,1)
  tag=loop+0x2c;put(tag+0x10,n-256);put(tag+0x20,32768);put(tag+0x24,1)
  program=bytes(m.mem_read(b+0xc88,0x318)).hex();requests.clear();events.clear();put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,b);m.emu_start(0x413860,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  cases.append(dict(n=n,index=index,active=active,counter=counter,angleBits=bits(angle),program=program,requests=list(requests),events=list(events),output=[get(b+o) for o in (0xc60,0xc64,0xc68,0xc4c)]))
 (ROOT/'artifacts/th16/bullet-spawn-transform-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(len(cases),'native spawn-transform programs /',sum(len(c['requests']) for c in cases),'whole emitter requests')
if __name__=='__main__':main()
