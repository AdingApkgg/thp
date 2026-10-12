"""Actual TH14 type 0/2/3/5 fade alpha and timer callbacks."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,control,stack=0x70001000,0x70002000,0x7000f000;m.mem_map(0x70000000,0x10000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 rows=[]
 for kind,duration,rate in itertools.product((0,2,3,5),(-1,0,1,7,32,60,127,300),(.3,.5,.99,1,1.01,1.25)):
  m.mem_write(base,bytes(0x100));put(base+0x18,255 if kind==3 else 0);put(base+0x1c,duration)
  put(base+0x30,-1);put(base+0x3c,0x4d8f58);put(0x4d8f58,bits(rate));put(0x4db558,control)
  states=[]
  for frame in range(1300):
   stopped=frame==5;frozen=frame in (10,11,12,13)
   put(0x4f56c8,int(stopped));put(control+0x80,4 if frozen else 0)
   put(stack,0x70000000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
   m.emu_start(0x46c400 if kind in (0,3) else 0x46c970,0x70000000,count=1000)
   assert m.reg_read(UC_X86_REG_EIP)==0x70000000
   states.append(dict(stopped=stopped,frozen=frozen,result=m.reg_read(UC_X86_REG_EAX),words=[get(base+off) for off in (0x18,0x30,0x34,0x38)]))
   # Stop requests are probed but ignored by this local lifetime fixture.
   if states[-1]['result']==7 and not stopped:break
  rows.append(dict(kind=kind,duration=duration,rate=rate,states=states))
 out=ROOT/'artifacts/th14/screen-fade-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows)),encoding='utf-8')
 print('native fades:',len(rows),'timelines /',sum(len(r['states']) for r in rows),'frames')
if __name__=='__main__':main()
