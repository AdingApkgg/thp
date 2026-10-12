"""Original primary bullet draw preparation, stopping immediately before the GPU dispatcher."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
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
     m.mem_write(bullet,bytes(0x3000));put(bullet+0x20,0x40*scaled);put(bullet+0x55c,0x80*rotate)
     floats(bullet+0xc20,-12.25,70.5,.25);floats(bullet+0xc3c,angle);floats(bullet+0x141c,scale)
     floats(bullet+0x608,3.25,-9.5,.125);floats(bullet+0x54,13.5,27.25,-.75);floats(bullet+0x68,-.625);floats(bullet+0x78,1.1,-.625,.75,1.25)
     m.reg_write(UC_X86_REG_ESI,bullet);
     for register,address in ((UC_X86_REG_XMM1,0x4945b8),(UC_X86_REG_XMM2,0x494588),(UC_X86_REG_XMM3,0x494534)):
      m.reg_write(register,get(address))
     m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
     m.emu_start(0x412b62,0x412c02,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x412c02
     words=[get(bullet+o) for o in (0x558,0x608,0x60c,0x610,0x68,0x78,0x7c,0x80,0x84,0x54,0x58,0x5c)]
     rows.append(dict(rotate=rotate,scaled=scaled,angle=angle,scale=scale,words=words))
 out=ROOT/'artifacts/th16/bullet-draw-prep-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} bullet draw preparation cases.')
if __name__=='__main__':main()
