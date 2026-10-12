"""Retail free-list initialization, factory unlink and per-array-slot recycling.
Factory 4508f0 and single-shot 4510b0 are controlled result boundaries.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,im.data[raw:raw+n])
 end,player,spec,stack=0x70000000,0x70001000,0x70021000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 slots=lambda p:(p-player-0x6c8)//0xd0
 success=True;step=0;mode=0;attempts=[];updates=[]
 def sink(machine,a,size,user):
  obj=m.reg_read(UC_X86_REG_ECX);slot=slots(obj)
  if a==0x4508f0:
   attempts.append(slot);put(obj+0x98,int(success));m.reg_write(UC_X86_REG_EAX,0 if success else 1)
  elif a==0x4510b0:
   updates.append(slot);retired=mode==2 or (slot%2==step%2 if mode==1 else (slot+step)%11==0)
   if retired:put(obj+0x98,0)
   m.reg_write(UC_X86_REG_EAX,int(retired))
  else:m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x4508f0,12),(0x4510b0,0),(0x47f0a0,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 m.reg_write(UC_X86_REG_ESI,player);m.emu_start(0x44cdb7,0x44ce1f,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x44ce1f
 def state():
  chain=[];node=get(player+0xd6cc)
  while node:
   slot=slots(node);assert slot not in chain and 0<=slot<256;chain.append(slot);node=get(node+4)
  active=[i for i in range(256) if get(player+0x6c8+i*0xd0+0x98)];assert len(chain)+len(active)==256
  return dict(free=chain,active=active)
 initial=state();rows=[]
 actions=[(0,1) for _ in range(270)]+[(1,1,0)]+[(0,int(i%7!=0)) for i in range(150)]
 for i in range(70):actions.extend([(0,int(j%13!=0)) for j in range(9)]+[(1,i%3,i)])
 for args in actions:
  attempts.clear();updates.clear();put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player)
  if args[0]==0:
   success=bool(args[1]);put(stack+4,spec);put(stack+8,0);put(stack+12,player+0x5e0);m.emu_start(0x450e40,end,count=10000)
  else:
   mode,step=args[1:];m.emu_start(0x451380,end,count=10000)
  assert m.reg_read(UC_X86_REG_EIP)==end;rows.append(dict(args=args,attempts=attempts[:],updates=updates[:],**state()))
 out=ROOT/'artifacts/th14/shot-pool-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),initial=initial,rows=rows)),encoding='utf-8');print(f'{len(rows)} retail shot-pool operations')
if __name__=='__main__':main()
