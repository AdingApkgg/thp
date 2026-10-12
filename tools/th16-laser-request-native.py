"""Complete own ECL702 arm; 431760 factory is a captured boundary."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);data,stack,bp=0x70001000,0x70014000,0x70018000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 index=0;requests=[];reads=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x477920:p,value,n=(get(sp+o) for o in (4,8,12));m.mem_write(p,bytes([value&255])*n);m.reg_write(UC_X86_REG_EAX,p)
  elif a==0x4251d0:reads.append(get(sp+4));m.reg_write(UC_X86_REG_EAX,index)
  else:assert get(sp+4)==0;requests.append(bytes(m.mem_read(get(sp+8),0x358)).hex());m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x477920,0),(0x4251d0,4),(0x431760,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 cases=[]
 for n in range(384):
  index=n%16;reads.clear();requests.clear();m.mem_write(data,bytes(0x5000));initial=bytearray(b''.join(struct.pack('<I',(n*0x1234567+k*0x12345)&0xffffffff) for k in range(0x39c0//4)))
  # Keep angle finite, varied far beyond the first wrap; preserve arbitrary ETEX words.
  struct.pack_into('<I',initial,index*0x380+0x14,bits((-200.,-3.15,-.25,0.,.5,3.15,200.,10000.)[(n//16)%8]))
  m.mem_write(data+0x598,bytes(initial));position=(12.25,-14.5,4.75)
  m.mem_write(data+0x44,struct.pack('<fff',*position))
  origin=(-33.125,144.25,(0.,.9,1.,float('nan'),float('inf'),-1.)[(n//16)%6]);base=(7.25,-8.5,9.75)
  m.mem_write(data+0x3dd8+index*12,struct.pack('<fff',*base));m.mem_write(data+0x3e98+index*12,struct.pack('<fff',*origin));before=bytes(m.mem_read(data+0x598,0x39c0)).hex()
  put(bp-0x42c,data);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_EDX,data)
  m.emu_start(0x421912,0x422a9b,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b;assert bytes(m.mem_read(data+0x598,0x39c0)).hex()==before;assert len(requests)==1
  cases.append(dict(index=index,initial=before,positionBits=[bits(f) for f in position],request=requests[0],reads=reads[:]))
 (ROOT/'artifacts/th16/laser-request-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(len(cases),'own ECL702 requests')
if __name__=='__main__':main()
