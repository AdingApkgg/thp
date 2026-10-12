"""Retail ETEX 100 / 41a830, using pinned D3DX9_43 SSE normalization code."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll');m=Uc(UC_ARCH_X86,UC_MODE_32)
 for image in (img,dll):
  for _,b,size,raw,n in image.sections:
   start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,image.data[raw:raw+n])
 end,obj,sprite,stack=0x70000000,0x70001000,0x70005000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 # DLL CPU-dispatch selection is controlled; execute its actual SSE body.
 put(0x4b12f0,0x101bafc4)
 def call(a):
  m.mem_write(stack-0x3000,bytes(0x3100));put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end;return m.reg_read(UC_X86_REG_EAX)
 state=lambda:[get(obj+p) for p in (0xc04,0xc20,0x1258,0x125c,0x1260,0x128c)]
 positions=((-210.,40.),(-202.,40.),(-192.,40.),(192.,40.),(202.,40.),(210.,40.),(0.,-20.),(0.,0.),(0.,448.),(0.,468.),(-210.,-20.),(210.,470.))
 rows=[]
 for pos,angle,dimension,count,early,rate in itertools.product(positions,(0.,.1,1.57079637,3.14159274,-1.57079637,200.),((20.,12.),(8.,64.),(64.,8.)),(-1,0,1,7),(0,1),(0.,.5,.99,1.,1.01,1.25)):
  m.mem_write(obj,bytes(0x2000));put(obj+0x54,sprite);put(sprite+0x38,bits(dimension[0]));put(sprite+0x34,bits(dimension[1]));m.mem_write(obj+0xbc0,struct.pack('<3f',*pos,3.25));put(obj+0xbdc,bits(angle));put(0x4d8f58,bits(rate))
  put(obj+0xc28+0x10,count);put(obj+0xc28+0x14,early);put(obj+0xc28+0x20,0x100);call(0x418140);initial=state();result=call(0x41a830)
  rows.append(dict(position=pos,angle=angle,dimension=dimension,count=count,early=early,rate=rate,initial=initial,result=result,state=state()))
 (ROOT/'artifacts/th14/bullet-offscreen-hold-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),normalizerDllPath=dll.path,normalizerDllSha256=hashlib.sha256(dll.data).hexdigest(),normalizerAddress='0x101bafc4',cases=rows))+'\n',encoding='utf8');print(f'{len(rows)} native ETEX 100 setup/offscreen-hold cases.')
if __name__=='__main__':main()
