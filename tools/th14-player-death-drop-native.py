"""Actual retail death-frame 3 through the item factory/options boundaries.
Executes 44dda3..44de99, including native 44ed80 / 4a753a angle calculation.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,stack=0x70000000,0x7003f000;m.mem_map(base,0x40000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 requests=[];rebuild=[]
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x4397b0:
   p=get(sp+8)
   # The unused third argument is not initialized by this native call site.
   requests.append([get(sp+4),get(p),get(p+4),get(p+8),get(sp+16),get(sp+20),get(sp+24)])
  else:rebuild.append(m.reg_read(UC_X86_REG_ECX)==base)
  m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x4397b0,24),(0x44f970,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
  m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 rows=[]
 powers=(-2147483648,-1,0,1,49,50,99,100,200,400,2147483647)
 steps=(-2147483648,-101,-1,0,1,99,100,101,2147483647)
 positions=((-180,400,0),(-12.5,480,2),(0,0,0),(0,400,0),(180,128,-1),(0,2**30,0),(-0.0,400,-0.0),(23.75,-10.5,3))
 for power in powers:
  for step in steps:
   for variant,p in enumerate(positions):
    requests.clear();rebuild.clear();m.mem_write(base,bytes(0x20000));m.mem_write(stack-0x1000,bytes(0x1100))
    for j,f in enumerate(p):put(base+0x5e0+j*4,bits(f))
    lives=(-1,0,4)[variant%3]
    put(0x4f5858,power);put(0x4f5860,step);put(0x4f5864,lives);put(0x4db660,base+0x20000)
    m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESP,stack)
    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.emu_start(0x44dda3,0x44de99,count=100000)
    assert m.reg_read(UC_X86_REG_EIP)==0x44de99 and len(requests)==7 and rebuild==[True]
    rows.append(dict(power=power,step=step,lives=lives,position=[bits(f) for f in p],result=get(0x4f5858),requests=requests[:]))
 out=ROOT/'artifacts/th14/player-death-drop-native.json';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} retail death-frame-3 cases / {len(rows)*7} item requests.')
if __name__=='__main__':main()
