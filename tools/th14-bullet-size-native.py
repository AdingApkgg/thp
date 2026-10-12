"""Retail ETEX 400000 setup and real size-update block 416781..4167c4."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,im.data[raw:raw+n])
 base=0x70000000;bullet=base+0x1000;stack=base+0x1f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 m.mem_write(0x4854a0,b'\xc3')
 offsets=(0xc04,0xc20,0x20,0x138c,0x1390,0x1394,0x1398,0x139c,0x13a0,0x13a4,0x13a8,0x13b4,0x13b8,0x13bc)
 def state():return [get(bullet+n) for n in offsets]
 def call(a,end=base):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);m.reg_write(UC_X86_REG_ESI,bullet);m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
 rows=[]
 for mode in range(32):
  for duration in (-1,0,1,30):
   for rate in (.5,1.,1.25):
    for start,target in ((1.,1.),(1.,2.5),(2.5,1.)):
     m.mem_write(bullet,bytes(0x3000));floats(0x4d8f58,rate);put(bullet+0x20,0x12);floats(bullet+0x139c,.625);floats(bullet+0x13bc,1.)
     t=bullet+0xc28;floats(t,start,target,0.,0.);put(t+0x10,duration);put(t+0x14,mode);put(t+0x20,0x400000)
     m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
     call(0x418140);initial=state();frames=[]
     for frame in range(96):
      call(0x416781,0x4167c4);frames.append(state())
     rows.append(dict(mode=mode,duration=duration,rate=rate,start=start,target=target,initial=initial,frames=frames))
 out=ROOT/'artifacts/th14/bullet-size-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} size setups / {len(rows)*96} updates.')
if __name__=='__main__':main()
