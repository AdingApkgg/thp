"""Original primary bullet draw preparation, stopping immediately before the GPU dispatcher."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,im.data[raw:raw+n])
 base=0x70000000;bullet=base+0x1000;stack=base+0x1f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 rows=[]
 for rotate in (0,1):
  for scaled in (0,1):
   for angle in (-500.,-3.1415927410125732,0.,.375,3.1415927410125732,500.):
    for scale in (-1.,0.,.5,1.,2.5):
     m.mem_write(bullet,bytes(0x3000));put(bullet+0x20,0x40*scaled);put(bullet+0x44,0x40*rotate)
     floats(bullet+0xbc0,-12.25,70.5,.25);floats(bullet+0xbdc,angle);floats(bullet+0x13bc,scale)
     floats(bullet+0x64,3.25,-9.5,.125);floats(bullet+0x78,-.625);floats(bullet+0x88,1.1,-.625,.75,1.25)
     m.reg_write(UC_X86_REG_ESI,bullet);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
     m.emu_start(0x41734a,0x4173ec,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x4173ec
     words=[get(bullet+o) for o in (0x40,0x64,0x68,0x6c,0x78,0x88,0x8c,0x90,0x94)]
     rows.append(dict(rotate=rotate,scaled=scaled,angle=angle,scale=scale,words=words))
 out=ROOT/'artifacts/th14/bullet-draw-prep-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} bullet draw preparation cases.')
if __name__=='__main__':main()
