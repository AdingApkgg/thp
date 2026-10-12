"""Exact retail 44d621..44d67a displacement/factor calculation, not full movement."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,im.data[raw:raw+n])
 player,stack=0x70001000,0x7003f000;m.mem_map(0x70000000,0x40000)
 rows=[]
 for dx,dy,x,y,factor in itertools.product((-2147483648,-512,-100,0,100,512,2147483647),(-512,-100,0,100,512),(-12.,-.37,0.,.37,12.),(-3.,0.,3.),(0.,.2,.33000001311302185,1.,1.25)):
  m.mem_write(player+0xd6dc,struct.pack('<fff',factor,x,y));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,player);m.reg_write(UC_X86_REG_EDX,dx&0xffffffff);m.reg_write(UC_X86_REG_ECX,dy&0xffffffff);m.reg_write(UC_X86_REG_ESI,1);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x44d621,0x44d67a,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x44d67a
  rows.append(dict(args=[dx,dy,x,y,factor],result=[m.reg_read(UC_X86_REG_EBX),struct.unpack('<I',m.mem_read(stack+0x14,4))[0]]))
 (ROOT/'artifacts/th14/reimu-a-movement-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} movement displacement calculations.')
if __name__=='__main__':main()
