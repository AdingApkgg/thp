"""Retail42fec5..43014e visibility/position-mode/immediate update control."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,game,manager,boss,player,spell,first,second,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x70009000,0x7000a000,0x7000b000,0x7000c000,0x7001f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 sounds=[];sprites=[];updates=[]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP);ecx=uc.reg_read(UC_X86_REG_ECX)
  if a==0x4113e0:put(ecx+0x4a0,get(sp+4));cleanup=4
  elif a==0x46e3d0:sounds.append(get(sp+4));cleanup=8
  elif a==0x46f1e0:sprites.append([0 if get(sp+4)==first else 1,get(sp+8)]);cleanup=8
  elif a==0x46fe50:updates.append([0 if ecx==first else 1,get(ecx+0x4a0)]);put(ecx+0x4a0,0);uc.reg_write(UC_X86_REG_EAX,0);cleanup=0
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook);rows=[]
 cases=[(seconds,previous,mode,flags,y,0,3) for seconds,previous,mode,flags,y in itertools.product((4,9,10),(4,10),range(4),(0,1,0x100,0x101),(0,127.99,128,159.99,160,288,288.01,320,320.01,400))]
 cases += [(seconds,10,mode,flags,400,gate,resources) for seconds,mode,flags,gate,resources in itertools.product((-1,4),range(4),(0,1),range(4),range(4))]
 for seconds,previous,mode,flags,y,gate,resources in cases:
  m.mem_write(base,bytes(0x1e000));sounds.clear();sprites.clear();updates.clear()
  for p,v in ((0x4db544,manager),(manager+0x5c,boss if gate!=1 else 0),(manager+0x9c,1 if gate==2 else 0),(game+0x194,1 if gate==3 else 0),(game+0x98,first),(game+0x9c,second),(game+0x19c,seconds),(game+0x1a4,previous),(game+0x17c,0x80+mode*512),(0x4db534,spell),(spell+0x7c,flags),(player+0x5e4,bits(y)),(first+0x30,resources&1),(second+0x30,resources&2),(first+0x18,5),(second+0x18,5),(first+0x4a0,17),(second+0x4a0,17)):put(p,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,game);m.reg_write(UC_X86_REG_ECX,player)
  m.emu_start(0x42fec5,0x43014e,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x43014e
  rows.append(dict(seconds=seconds,previous=previous,mode=mode,flags=flags,y=y,gate=gate,resources=resources,state=[get(first+0x4a0),get(second+0x4a0),get(game+0x1a4),get(game+0x17c),get(first+0x18)&2,get(second+0x18)&2],sounds=sounds[:],sprites=sprites[:],updates=updates[:]))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Retail42fec5..43014e valid manager, missing/present boss, manager gate/dialogue/negative seconds, all four512/1024 modes, spell bit1/flip bit256, Y128/160/288/320 strict edges, seconds4/9/10 and repeat/change, both digit resource presence bits. Real helper435720/435700/41d750/41d7b0/4356d0 runs; controlled animation update records label then clears pending, sprite/audio/interrupt services controlled. State/visibility/pending, update counts and sprite/audio requests compared; actual ANM label/color/motion and manager timing require real-resource integration.')
 (ROOT/'artifacts/th14/hud-timer-control-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} original countdown visibility/mode cases')
if __name__=='__main__':main()
