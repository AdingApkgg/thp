"""Retail 704..709 writes, actual registry lookup, controlled ECL arguments."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,second,manager,enemy,stack=0x70000000,0x70001000,0x70004000,0x70007000,0x70008000,0x700ff000;m.mem_map(end,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 args=[]
 def boundary(machine,a,size,user):m.reg_write(UC_X86_REG_EAX if a==0x42c1d0 else UC_X86_REG_XMM0,args[get(m.reg_read(UC_X86_REG_ESP)+4)])
 for a in (0x42c1d0,0x42c230):m.mem_write(a,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 fields=(0x54,0x58,0x5c,0x6c,0x70,0x74,0x78,0x80,*range(0x5c0,0x5ec,4))
 entries={704:0x429231,705:0x429288,706:0x4292d9,707:0x429306,708:0x429333,709:0x429360};rows=[]
 for op,entry in entries.items():
  for kind in (1,2,3):
   for selector in (0,1,2,3):
    for value in (0.,-0.,-1.,.125,3.141592741,200.,-9999.):
     m.mem_write(obj,bytes(0x2000));m.mem_write(second,bytes(0x2000));put(0x4db664,manager);put(manager+0x18,obj);put(obj+8,second);put(obj+0x14,kind);put(second+0x14,kind)
     for base,id in ((obj,0x10001),(second,0x10002)):
      for j,offset in enumerate(fields):put(base+offset,bits(12.25+j*.125))
      put(base+0x80,id)
     before=[[get(base+offset) for offset in fields] for base in (obj,second)];args[:]=[(0,0x10001,0x10002,0x10003)[selector],bits(value),bits(-value*.5)]
     m.mem_write(stack-0x2000,bytes(0x2100));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,enemy);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
     m.emu_start(entry,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
     rows.append(dict(op=op,kind=kind,args=args[:],before=before,result=[[get(base+offset) for offset in fields] for base in (obj,second)]))
 out=ROOT/'artifacts/th14/laser-control-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail laser controls, actual lookup and helper writes.')
if __name__=='__main__':main()
