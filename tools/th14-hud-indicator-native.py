"""Retail430dfe..4310bd retained front111 indicator state/position/alpha."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,game,manager,boss,player,spell,vm,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x7000a000,0x7000b000,0x7000c000,0x7001f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,vm if get(sp+4)==1 else 0);cleanup=4
  elif a==0x4113e0:put(uc.reg_read(UC_X86_REG_ECX)+0x4a0,get(sp+4));cleanup=4
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook);rows=[]
 cases=[(1,0,mode,active,value,12.25,0,0) for mode,active,value in itertools.product(range(4),range(2),(-1,0,199,200,201,399,400,401,699,700,701,999,1000,1001,1999,2000,2001))]
 cases += [(1,0,mode,active,500,x,x+distance,0) for mode,active,x,distance in itertools.product(range(4),range(2),(-193,-192,0,192,193,12.25),(0,1,63.99,64,65))]
 cases += [(present,flags,0,0,500,12.25,0,children) for present,flags,children in itertools.product(range(2),(0,1,0x20,0x21,0x10),range(3))]
 for present,flags,mode,active,value,x,px,children in cases:
  m.mem_write(base,bytes(0x1e000))
  for p,v in ((0x4db544,manager),(manager+0x5c,boss if present else 0),(boss+0x5244,flags),(boss+0x516c,value),(boss+0x1234,bits(x)),(player+0x5e0,bits(px)),(0x4db67c,player),(0x4db534,spell),(spell+0x7c,active),(0x4f56cc,base),(game+0xa0,1),(game+0x17c,0xa500|mode*2),(vm+0x18,7),(vm+0x534,0xc0123456),(vm+0x4a0,17),(vm+0x59c,bits(23)),(vm+0x5a0,bits(31))):put(p,v)
  for n in range(2):
   node=vm+0x700+n*0x10;child=vm+0x800+n*0x700;put(node,child);put(node+4,node+0x10 if n==0 else 0);put(child+0x18,7)
  if children:put(vm+0x584,vm+0x700)
  if children==2:put(vm+0x588,vm+0x710)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,game);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x430dfe,0x4310bd,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x4310bd
  rows.append(dict(present=present,flags=flags,mode=mode,spell=active,value=value,x=x,playerX=px,children=children,state=[get(game+0x17c),get(vm+0x18)&2,get(vm+0x534),get(vm+0x4a0),get(vm+0x59c),get(vm+0x5a0)],childVisible=[bool(get(vm+0x800+n*0x700+0x18)&2) for n in range(2)]))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Retail430dfe..4310bd actual indicator front111 retained HUD+a0, primary boss pointer/flags21, spell thresholds2000/1000/400 and normal700/400/200 for all four states, raw doubled X(x+32+192)/Y960, alpha distance64 edges and boss X+-192 bounds, missing-boss child visibility with root/child-list branches. Registry lookup and interrupt delivery controlled, on-interrupt callback absent; excludes actual ANM/renderer/GPU.')
 (ROOT/'artifacts/th14/hud-indicator-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} original indicator cases')
if __name__=='__main__':main()
