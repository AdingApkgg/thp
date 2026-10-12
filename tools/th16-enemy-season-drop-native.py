"""Own41c72f..41c7a6 with real402c70/402cf0 RNG and recorded430960 requests."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);data,stack=0x70001000,0x7001d000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 events=[]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP);p=get(sp+8)
  events.append([get(sp+4),get(p),get(p+4),get(p+8),get(sp+16),get(sp+20),get(sp+28)])
  machine.reg_write(UC_X86_REG_EAX,0)
 m.mem_write(0x430960,b'\xc2\x1c\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=0x430960,end=0x430960)
 cases=[]
 for step,next_,delta,seed,position,calls in itertools.product((-1,0,1,7,100,999),(-100,0,7,10000),(-1,0,1,9,257),(0,1,0x9630,0xffff),((0,192,0),(-184.125,413.75,-1)),(0,0xfffffffc)):
  total=next_+delta
  for off,v in ((0x4058,step),(0x405c,next_),(0x3f88,total)):put(data+off,v)
  for n,v in enumerate(position):put(data+0x44+n*4,bits(v))
  put(0x4a6d88,seed);put(0x4a6d8c,calls);events.clear();m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_ESP,stack)
  m.emu_start(0x41c72f,0x41c7a6,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x41c7a6
  cases.append(dict(step=step,next=next_,total=total,seed=seed,calls=calls,position=position,output=[get(data+0x405c),get(0x4a6d88),get(0x4a6d8c)],events=list(events)))
 (ROOT/'artifacts/th16/enemy-season-drop-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8')
 print(f'{len(cases)} own damage seasonal item request sequences')
if __name__=='__main__':main()
