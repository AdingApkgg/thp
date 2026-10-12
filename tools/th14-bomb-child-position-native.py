"""Actual recursive 412c60; production observes it through Marisa A cancellation."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,out,stack=0x70000000,0x70001000,0x70007000,0x7000f000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 rows=[]
 for count,flags,angle,variant in itertools.product((1,2,3,4),(0,0x8000,0x400000,0x408000),(0.,.125,-1.5707963705062866,3.1415927410125732),(0,1,2)):
  records=[]
  for j in range(count):
   p=obj+j*0x1000;m.mem_write(p,bytes(0x1000));values=[flags,bits(angle),*map(bits,(((-1)**j)*12.25,80.5+j,3.5)),*map(bits,(.125+j,-1.25,2.5)),*map(bits,(-.0625,j*.5,-2.5)),0]
   if variant==1:values[2:11]=list(map(bits,(1e8,-1e8,.5,-1e8,1e8,1.25,.125,-.125,-2.5)))
   if variant==2:values[2:11]=list(map(bits,(-0.,0.,-0.,0.,-0.,0.,-0.,0.,-0.)))
   records.append(values);put(p+0x1c,flags);put(p+0x50,values[1]);put(p+0x594,obj+(j-1)*0x1000 if j else 0)
   for offsets,values3 in ((0x59c,values[2:5]),(0x3c,values[5:8]),(0x4ec,values[8:11])):
    m.mem_write(p+offsets,struct.pack('<3I',*values3))
  put(stack,end);put(stack+4,out);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj+(count-1)*0x1000)
  m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(0x412c60,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(records=records,position=list(struct.unpack('<3I',m.mem_read(out,12)))))
 (ROOT/'artifacts/th14/bomb-child-position-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} native recursive child positions.')
if __name__=='__main__':main()
