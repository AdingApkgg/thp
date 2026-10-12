"""Full TH16 465c40/4660b0 quads with406c40/406a70 transforms and464dd0 rotation."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x40000);vm,parent,out,stack,ret=0x70001000,0x70002000,0x70003000,0x7003d000,0x7003e000;m.mem_write(0x47499b,b'\xc3')
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 for a,v in ((0x4d9d50,320),(0x4d9d54,16),(0x4d9d48,111),(0x4d9d4c,23)):put(a,v)
 cases=[]
 for mode,resolution,origin,anchor,relation,rate in itertools.product((0,1),(0,1,2,3,4,7),range(4),range(9),range(6),(1.,1.5)):
  m.mem_write(vm,bytes(0x2000));m.mem_write(out,bytes(48));flags2=(resolution<<20)|(origin<<18)|(0x800000 if relation==4 else 0)|(0x10000 if relation==5 else 0)
  put(vm+0x530,3|((anchor%3)<<21)|((anchor//3)<<23));put(vm+0x534,flags2)
  put(vm+0x5b0,parent if relation in (1,3,5) else 0);put(vm+0x5ac,parent if relation in (2,3,4,5) else 0)
  for p in (vm,parent):
   floats(p+0x5e0,127.25,200.75,.375);floats(p+0x2c,3.25,-9.5,.125);floats(p+0x4e0,4.5,2.25,.25)
   floats(p+0x38,.125,-.25,.375);floats(p+0x50,1.1,-.625,.75,1.25);floats(p+0x70,31.75,47.625);floats(p+0x80,2.3,-7.1)
  floats(parent+0x50,.5,2,3,4);floats(0x4d9d34,rate)
  put(stack,ret)
  for n,v in enumerate((vm,out,out+12,out+24,out+36)):put(stack+4+n*4,v)
  for reg,v in ((UC_X86_REG_ESP,stack),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)):m.reg_write(reg,v)
  m.emu_start(0x465c40 if mode==0 else 0x4660b0,ret,count=10000);assert m.reg_read(UC_X86_REG_EIP)==ret
  cases.append(dict(mode=mode,resolution=resolution,origin=origin,anchor=anchor,relation=relation,rate=rate,output=list(struct.unpack('<12I',m.mem_read(out,48)))))
 (ROOT/'artifacts/th16/quad-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(len(cases),'own TH16 quad cases')
if __name__=='__main__':main()
