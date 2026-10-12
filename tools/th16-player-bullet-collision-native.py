"""Actual retail TH16 4438c0/4439e0 rectangle/circle. Hit application is a sink."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,player,hud,pos,size,header,stack=[0x70000000+n for n in (0,0x1000,0x20000,0x21000,0x22000,0x23000,0x3f000)];m.mem_map(end,0x40000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 hits=[]
 def hit(machine,a,size,user):hits.append(m.reg_read(UC_X86_REG_ECX)==player)
 m.mem_write(0x443f10,b'\xc3');m.hook_add(UC_HOOK_CODE,hit,begin=0x443f10,end=0x443f10)
 put(0x4a6ef8,player);put(player+0x2c788,header);put(0x4a6dcc,hud)
 rows=[]
 positions=((0,0),(1,0),(4,0),(4.000001,0),(8,5),(24,0),(24.75,0),(40,0),(40.75,0),(41,0),(100,-100),(float('nan'),0),(0,float('nan')),(float('inf'),0),(float('-inf'),0))
 for circle in (0,1):
  for variant in range(6):
   radius=(0,.75,1.25)[variant%3];factor=(0.5,1,2)[variant%3];scaled=int(variant>=3)
   width=(0,1,8,16,-8,float('nan'))[variant];height=width*.75
   for dx,dy in positions:
    for state in (0,1,2,3,4):
     for inv in (-1,0,1):
      for dialogue,probe in ((0,0),(1,0),(0,1),(1,1)):
       hits.clear();px,py=-12.25,80.5;p=(px+dx,py+dy)
       put(player+0x610,bits(px));put(player+0x614,bits(py));put(header+4,bits(radius));put(player+0x1664c,0x10 if scaled else 0);put(player+0x2c7c8,bits(factor))
       for o,v in zip((0x2c730,0x2c734,0x2c73c,0x2c740),(px-.75,py-1.25,px+.75,py+1.25)):put(player+o,bits(v))
       put(player+0x165a8,state);put(player+0x1663c,inv);put(hud+0x1c8,dialogue);put(pos,bits(p[0]));put(pos+4,bits(p[1]));put(size,bits(width));put(size+4,bits(height))
       put(stack,end);put(stack+4,pos);put(stack+8,probe if circle else size)
       if not circle:put(stack+12,probe)
       m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM2,bits(width));m.reg_write(UC_X86_REG_MXCSR,0x1f80)
       m.emu_start(0x4439e0 if circle else 0x4438c0,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
       rows.append(dict(input=[circle,*map(bits,(px,py,p[0],p[1],width,height,radius,factor)),scaled,state,inv,dialogue,probe],result=[m.reg_read(UC_X86_REG_EAX),int(bool(hits))]))
 out=ROOT/'artifacts/th16/player-bullet-collision-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail player bullet collision cases.')
if __name__=='__main__':main()
