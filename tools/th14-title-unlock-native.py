"""Unmodified4591d0 equipment eligibility and459220 global Extra eligibility."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in im.sections:
  begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,im.data[raw:raw+n])
 ret,manager,stack=0x70000000,0x70001000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 put(0x4db68c,manager)
 def call(address,selection=0):
  put(stack,ret);put(stack+4,selection);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
  m.emu_start(address,ret,count=20000);assert m.reg_read(UC_X86_REG_EIP)==ret
  return m.reg_read(UC_X86_REG_EAX)
 rows=[]
 cases=[(-1,0,0,0),(-1,0,0,1)]+[(s,d,v,p) for s in range(7) for d in range(5) for v in (1,2,0x80000000,0xffffffff) for p in (0,1)]
 for selection,difficulty,flag,prefs in cases:
  m.mem_write(manager,bytes(8+7*0x5298+0x42c))
  if selection>=0:put(manager+8+selection*0x5298+0x7dc+difficulty*4,flag)
  if prefs:m.mem_write(manager+8+7*0x5298+0x1c,bytes([0x10]*6))
  rows.append(dict(selection=selection,difficulty=difficulty,flag=flag,prefs=prefs,available=[call(0x4591d0,s) for s in range(6)],unlocked=call(0x459220)))
 (ROOT/'artifacts/th14/title-unlock-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows),indent=2)+'\n')
 print(f'{len(rows)} native TH14 Extra eligibility cases')
if __name__=='__main__':main()
