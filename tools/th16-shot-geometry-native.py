"""403d30/4049c0 geometry, no service interceptions; all original math executes."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,stack=0x70000000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[]
 cases=[]
 for w,h,angle,dx,dy,radius in itertools.product((0.,4.,32.),(0.,8.,48.),(0.,.5,-1.25,3.1415927410125732),(-32.,-16.,-2.,0.,2.,16.,32.),(-24.,-4.,0.,4.,24.),(0.,4.,16.)):
  cases.append((0,2.25+dx,300.5+dy,w,h,angle,radius,0.,0.,0.))
 for w,h,angle,dx,dy,ow,oh,other_angle in itertools.product((0.,32.),(0.,48.),(0.,.5,-1.25),(-32.,-16.,0.,16.,32.),(-24.,0.,24.),(0.,16.),(0.,32.),(0.,.5,-1.25)):
  cases.append((1,2.25+dx,300.5+dy,w,h,angle,0.,ow,oh,other_angle))
 for case in cases:
  kind,x,y,w,h,angle,radius,ow,oh,other_angle=case
  for reg,value in zip((UC_X86_REG_XMM0,UC_X86_REG_XMM1,UC_X86_REG_XMM2,UC_X86_REG_XMM3),(2.25,300.5,w,h)):m.reg_write(reg,bits(value))
  args=(angle,x,y,ow,oh,other_angle) if kind else (angle,x,y,radius);put(stack,ret)
  for n,v in enumerate(args):put(stack+4+n*4,bits(v))
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x4049c0 if kind else 0x403d30,ret,count=200000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(input=case,output=m.reg_read(UC_X86_REG_EAX)))
 (ROOT/'artifacts/th16/shot-geometry-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 shot geometry cases')
if __name__=='__main__':main()
