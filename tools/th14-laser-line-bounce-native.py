"""Actual 43b060 / 43b730 and state portion of 43be20; factory/sound boundaries."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,stack=0x70000000,0x70001000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 words=lambda p,n:list(struct.unpack('<'+'I'*n,m.mem_read(p,4*n)))
 requests=[];sounds=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x43a750:assert get(sp+4)==0;requests.append(words(get(sp+8),213))
  else:sounds.append(get(sp+4))
  m.reg_write(UC_X86_REG_EAX,0)
 for a in (0x43a750,0x46e3d0):m.mem_write(a,b'\xc2\x08\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def call(a,stop=end):
  m.mem_write(stack-0x3000,bytes(0x3100));put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(a,stop,count=100000);assert m.reg_read(UC_X86_REG_EIP) in (stop,end)
  return m.reg_read(UC_X86_REG_EAX) if m.reg_read(UC_X86_REG_EIP)==end else 0
 fields=(0x594,0x598,0x5b4,0x1b8,0x1dc,0x1d8,0x1e0,0x54,0x58,0x5c,0x6c,0x70,0x78,0x7c,0x5a0,0x5a4,0x5a8)
 state=lambda:[get(obj+p) for p in fields]+words(obj+0x5c0,213)+[len(sounds)]
 variants=((0.,100.,0.,100.),(0.,100.,0.,256.),(0.,100.,0.,640.),(0.,100.,3.14159274,640.),(0.,100.,-1.57079637,128.),(0.,100.,1.57079637,640.),(0.,100.,-.75,640.),(0.,100.,2.4,640.),(-210.,-20.,-.75,640.),(210.,470.,.75,640.),(-192.,0.,0.,0.),(192.,448.,0.,0.),(-260.,100.,-1.57079637,256.),(260.,100.,-1.57079637,256.),(12.25,80.5,-3.15,640.),(12.25,80.5,200.,640.))
 rows=[]
 for flags,count,speed,variant,rate in itertools.product(range(32),(-1,0,1,3),(-1.,0.,4.),range(len(variants)),(.5,1.,1.25)):
  x,y,angle,length=variants[variant];r=[0]*213;r[:9]=list(map(bits,(x,y,3.25,angle,length,length,0.,24.,2.75)));r[-2:]=[0xffffffff,38]
  r[13:24]=[bits(speed),0,0,0,count&0xffffffff,flags,0,0,0x40,0,0];r[24+4]=7;r[24+8]=0x80
  m.mem_write(obj,bytes(0x2000));put(obj,0x4be434);m.mem_write(obj+0x5c0,struct.pack('<213I',*r));m.mem_write(obj+0x54,struct.pack('<3f',x,y,3.25));put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));put(obj+0x78,bits(2.75));put(obj+0x910,38)
  put(obj+0x5a0,29);put(obj+0x5a4,30);put(obj+0x5a8,bits(30.));put(obj+0x5ac,0x4d8f58);put(0x4d8f58,bits(rate))
  # Retail polar helper supplies constructor velocity, preserving the unwritten Z as zero.
  import math
  m.mem_write(obj+0x60,struct.pack('<3f',math.cos(struct.unpack('<f',struct.pack('<f',angle))[0])*2.75,math.sin(struct.unpack('<f',struct.pack('<f',angle))[0])*2.75,0.))
  requests.clear();sounds.clear();call(0x43b060);initial=state();saved=bytes(m.mem_read(obj,0x2000));result=call(0x43b730) if get(obj+0x598)&0x40 else 0
  bounced=state();emitted=requests[:];m.mem_write(obj,saved);requests.clear();sounds.clear();full_result=call(0x43be20,0x43c179)
  rows.append(dict(request=r,rate=rate,initial=initial,result=result,state=bounced,requests=emitted,fullResult=full_result,fullState=state(),fullRequests=requests[:]))
 (ROOT/'artifacts/th14/laser-line-bounce-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows))+'\n',encoding='utf8');print(f'{len(rows)} native laser ETEX 40 setup/bounce/frame cases.')
if __name__=='__main__':main()
