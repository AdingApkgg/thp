"""Execute retail TH16 easing4033f0 including its original CRT trig calls."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);stack=0x7001e000;durations=(1,7,64);elapsed=(-1.,0.,.125,.5,.99,1.,7.,31.,64.,99.);rows=[]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 for mode in range(-1,36):
  for di,duration in enumerate(durations):
   for ei,t in enumerate(elapsed):
    m.mem_write(stack,struct.pack('<I',0x70000000));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,mode&0xffffffff);m.reg_write(UC_X86_REG_XMM1,bits(t));m.reg_write(UC_X86_REG_XMM2,bits(duration));m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    m.emu_start(0x4033f0,0x70000000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x70000000
    rows.append([mode,di,ei,m.reg_read(UC_X86_REG_XMM0)&0xffffffff])
 out=ROOT/'artifacts/th16/easing-native.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Complete retail4033f0 easing function including original CRT trigonometric calls. Finite elapsed inputs, positive durations1/7/64 and modes-1..35, including default/unused easing slots; output compared bitwise. No interpolator timer, Hermite vector arithmetic, colors, VM tail, GPU or full gameplay claim.',durations=durations,elapsed=elapsed,rows=rows),separators=(',',':'))+'\n');print(len(rows),'native TH16 easing cases')
if __name__=='__main__':main()
