"""Actual retail 4518d0 homing, native nearest/ID lookup and math; no stubs.
Enemy list and object layouts are controlled. Includes 4538f0 delayed turn.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,im.data[raw:raw+n])
 end,obj,spec,manager,enemy,second,stack=0x70000000,0x70001000,0x70002000,0x70010000,0x70040000,0x70050000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 def call(a):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end and m.reg_read(UC_X86_REG_EAX)==0
 rows=[]
 for n in range(8192):
  state=(1,2)[n%2];present=n//2%2;listed=n//4%2;target=n//8%4;flag=(0,1,0x20,0x4000000,0x8000000,0x400000,0xffffffff)[n//32%7];age=(0,39,40,59,60,61,120)[n//224%7]
  angle=(-3.1415927410125732,-2.37,-.7853981852531433,0.,.2617993950843811,3.1415927410125732,1000.)[n//13%7];speed=(3.9,4.,8.,15.95,16.,40.)[n//37%6]
  x,y=((-256,100),(255.875,100),(0,-156),(0,-155.875),(0,100),(5,95),(100,200),(-80,140))[n//7%8];other=n//59%3
  m.mem_write(end,bytes(0xf0000))
  for p,v in ((0x4db544,manager if present else 0),(manager+0xd0,enemy+0x14d8 if listed else 0),(enemy+0x14d8,enemy),(enemy+0x14dc,second+0x14d8 if other else 0),(enemy+0x11e4,73),(enemy+0x5244,flag),(second+0x14d8,second),(second+0x11e4,99),(obj+0x98,state),(obj+0x1c,age),(obj+0x9c,enemy if target else 0),(obj+0xa0,(17,73,999,99)[target])):put(p,v)
  floats(obj+0x54,0,100,3);floats(obj+0x6c,speed,angle);floats(enemy+0x1234,x,y,0);floats(second+0x1234,float(x) if other==1 else -float(x),y,0)
  call(0x4518d0);p=get(obj+0x9c);rows.append(dict(args=[state,present,listed,target,flag,age,angle,speed,x,y,other],result=[1 if p==enemy else 2 if p==second else 0,get(obj+0xa0),get(obj+0x6c),get(obj+0x70)]))
 retired=[]
 for age in (0,6,39,59,60,120):
  for angle in (-3.1415927410125732,-1.2,0.,2.37):
   for speed in (3.9,4.,8.,15.95,16.,40.):
    m.mem_write(end,bytes(0xf0000))
    for p,v in ((0x4db544,manager),(manager+0xd0,second+0x14d8),(second+0x14d8,second),(second+0x11e4,99),(enemy+0x11e4,73),(obj+0x98,1),(obj+0x1c,age),(obj+0x9c,enemy),(obj+0xa0,73)):put(p,v)
    floats(obj+0x54,0,100,3);floats(obj+0x6c,speed,angle);floats(second+0x1234,5,95,0)
    call(0x4518d0);p=get(obj+0x9c);retired.append(dict(args=[age,angle,speed,5,95],result=[1 if p==enemy else 2 if p==second else 0,get(obj+0xa0),get(obj+0x6c),get(obj+0x70)]))
 turns=[]
 for age in (-2147483648,-1,0,5,60,2147483647):
  for delay in (-2147483648,-1,0,5,60,2147483647):
   for state in (1,2):
    for angle in (-3.2,.37,1000.):
     m.mem_write(obj,bytes(0x100));put(obj+0xbc,spec);put(obj+0x98,state);put(obj+0x1c,age);put(spec+0x38,delay);floats(obj+0x6c,8.125,angle);call(0x4538f0);turns.append(dict(args=[age,delay,state,angle],result=[get(obj+0x98),get(obj+0x6c),get(obj+0x70)]))
 (ROOT/'artifacts/th14/shot-homing-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows,retired=retired,turns=turns),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} retail homing updates / {len(retired)} retired-target cases / {len(turns)} delayed turns.')
if __name__=='__main__':main()
