"""Full retail 46cf60 phased shake, timer and visual RNG, with controlled active stage flags."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,im.data[raw:raw+n])
 end,obj,stage,stack=0x70000000,0x70001000,0x70002000,0x7000f000;m.mem_map(end,0x10000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 rows=[]
 for (amplitude,ramp,hold,fall),rate,seed,stopped in itertools.product(((3,60,240,30),(6,0,0,20),(-11,17,31,3)),(.5,.99,1,1.01,1.25),(0,1,65535),(0,1)):
  m.mem_write(obj,bytes(0x100));put(0x4db558,stage);put(stage+0x80,0);put(0x4f56c8,stopped);put(0x4d8f58,bits(rate));put(0x4db510,seed);put(0x4db514,0);put(0x4f7a6c,bits(1.5));put(0x4d9610,bits(3));put(0x4d9614,bits(-5))
  for off,v in ((0x1c,amplitude),(0x20,ramp),(0x24,hold),(0x28,fall),(0x30,-1),(0x34,0),(0x38,0),(0x3c,0x4d8f58),(0x40,1)):put(obj+off,v)
  frames=[]
  for frame in range(700):
   put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(0x46cf60,end,count=20000);assert m.reg_read(UC_X86_REG_EIP)==end
   result=[m.reg_read(UC_X86_REG_EAX),get(obj+0x30),get(obj+0x34),get(obj+0x38),get(0x4d9610),get(0x4d9614),get(0x4db510),get(0x4db514)];frames.append(result)
   if result[0]==7:break
  rows.append(dict(args=[amplitude,ramp,hold,fall,rate,seed],stopped=stopped,frames=frames))
 (ROOT/'artifacts/th14/screen-shake-hold-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} phased shake timelines / {sum(len(r["frames"]) for r in rows)} native frames.')
if __name__=='__main__':main()
