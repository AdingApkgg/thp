"""Retail 44f0b0 geometric and state gates; hit application 44f7a0 is recorded."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,player,bomb,origin,stack=0x70000000,0x70001000,0x70020000,0x70021000,0x7003f000;m.mem_map(end,0x40000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 hits=[]
 def hit(machine,a,size,user):hits.append(m.reg_read(UC_X86_REG_ECX)==player)
 m.mem_write(0x44f7a0,b'\xc3');m.hook_add(UC_HOOK_CODE,hit,begin=0x44f7a0,end=0x44f7a0)
 put(0x4db67c,player);put(0x4db550,bomb)
 rows=[]
 for variant in range(12):
  angle=(-3.15,-.125,0.,.5,1.57079637,200.)[variant%6];width=(0.,7.,14.,32.)[variant%4];length=(-1.,.125,4.,20.)[variant%4]
  half=(.75,1.25);base=(-12.25,80.5)
  for dx,dy in ((0.,0.),(-1.,0.),(1.,0.),(4.,3.5),(4.,3.5001),(0.,7.),(10.,10.),(-30.,0.),(0.,30.),(100.,-100.)):
   for state in (0,1,2,3,4):
    for invincibility in (-1,0,1):
     for bomb_active,probe in ((0,0),(1,0),(0,1),(1,1)):
      hits.clear();m.mem_write(stack-0x1000,bytes(0x1100))
      position=(base[0]+dx,base[1]+dy);put(player+0x5e0,bits(position[0]));put(player+0x5e4,bits(position[1]));put(player+0x648,bits(half[0]));put(player+0x64c,bits(half[1]));put(player+0x684,state);put(player+0x182c4,invincibility);put(bomb+0x194,bomb_active)
      put(origin,bits(base[0]));put(origin+4,bits(base[1]));put(stack,end);put(stack+4,origin);put(stack+8,bits(length));put(stack+12,probe)
      m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM2,bits(angle));m.reg_write(UC_X86_REG_XMM3,bits(width));m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
      m.emu_start(0x44f0b0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
      rows.append(dict(input=[*map(bits,(*position,*base,*half,angle,width,length)),state,invincibility,bomb_active,probe],result=[m.reg_read(UC_X86_REG_EAX),int(bool(hits))]))
 out=ROOT/'artifacts/th14/player-laser-collision-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail player-laser collision cases.')
if __name__=='__main__':main()
