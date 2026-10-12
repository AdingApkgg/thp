"""Actual 41b4f0 pool scan and two geometry tests; 41ac70 cancellation is a delivery sink."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,im.data[raw:raw+n])
 base=0x70000000;manager=base;ret=base+0xa10000;center=ret+0x100;sizeptr=ret+0x110;stack=ret+0x1000;m.mem_map(base,0xa20000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 calls=[]
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);calls.append([(m.reg_read(UC_X86_REG_ECX)-manager-0x8c)//0x13f4,get(sp+4)])
 m.mem_write(0x41ac70,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,sink,begin=0x41ac70,end=0x41ac70)
 put(0x4db530,manager);m.mem_write(center,struct.pack('<fff',12,200,0));m.mem_write(sizeptr,struct.pack('<fff',64,256,0))
 rows=[];previous=None
 positions=((12,200),(44,200),(48,200),(49,200),(12,68),(12,67),(-24,68),(48,332),(192,224),(196,224),(0,-1),(0,449))
 for state,delay,slot,scale,angle,p in itertools.product((0,1,2,3,4),(0,1),(0,1999),(0.,.5,1.,2.),(0.,.7853981852531433,1.5707963705062866,-1.5707963705062866),positions):
  if previous is not None:m.mem_write(previous+0xc0e,b'\0\0')
  b=manager+0x8c+slot*0x13f4;previous=b;calls.clear();m.mem_write(b,bytes(0x13f4));put(b+0x24,delay);put(b+0xbe0,bits(8));put(b+0x13bc,bits(scale));m.mem_write(b+0xbc0,struct.pack('<fff',*p,2));m.mem_write(b+0xc0e,struct.pack('<H',state))
  put(stack,ret);put(stack+4,center);put(stack+8,sizeptr);put(stack+12,1);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM3,bits(angle));m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x41b4f0,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(args=[state,delay,slot,scale,angle,*p],calls=calls[:]))
 (ROOT/'artifacts/th14/bullet-rectangle-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} retail rotated rectangle/pool eligibility cases.')
if __name__=='__main__':main()
