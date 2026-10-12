"""Retail MSG7/8/9 and13/14 portrait interrupts and text reset writes."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x10000);dialogue=base;instruction=base+0x1000;stack=base+0xf000;vms={90:base+0x2000,95:base+0x2800,**{100+i:base+0x3000+i*0x800 for i in range(4)},**{110+i:base+0x5000+i*0x800 for i in range(4)}}
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 interrupts=[];interrupt_kinds=[]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,vms.get(get(sp+4),0));pop=4
  elif a in (0x47f140,0x47f1b0):interrupts.append([get(sp+4),get(sp+8)]);interrupt_kinds.append('synchronous-family' if a==0x47f1b0 else 'deferred-family');pop=8
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x47f0a0,0x47f140,0x47f1b0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[];put(0x4f56cc,base+0x9000)
 for op,selection,flags,value in itertools.product((7,8,9,13,14),range(4),(0,2,63,0xffffffff),(-1,0,1,19,65519,2147483647,-2147483648)):
  m.mem_write(dialogue,bytes(0x200));put(dialogue+0x158,instruction);put(instruction+4,selection if op==8 else value);put(instruction+8,selection);put(dialogue+0x40,90);put(dialogue+0x54,95)
  for i in range(4):put(dialogue+0x44+i*4,100+i);put(dialogue+0x58+i*4,110+i);vm=vms[110+i];m.mem_write(vm,bytes(0x700));m.mem_write(vm+0x59c,struct.pack('<fff',50+i,70+i,0));m.mem_write(vm+0x4ec,struct.pack('<fff',.5,4.,2.))
  for n in range(3):m.mem_write(dialogue+0x15c+n*12,struct.pack('<fff',16+n,24+n,32+n))
  for off,val in ((0x190,2),(0x184,flags),(0x188,17),(0x18c,19)):put(dialogue+off,val)
  interrupts.clear();interrupt_kinds.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,dialogue);m.reg_write(UC_X86_REG_ECX,instruction);m.reg_write(UC_X86_REG_ESI,base+0x9000);start=img.u32(0x433930+op*4);m.emu_start(start,0x43369d,count=5000);assert m.reg_read(UC_X86_REG_EIP)==0x43369d
  rows.append(dict(input=[op,selection,flags,value],interrupts=interrupts[:],interruptKinds=interrupt_kinds[:],state=[get(dialogue+off) for off in (0x190,0x184,0x188,0x18c)],lines=[[get(vms[110+i]+off) for off in (0x59c,0x5a0,0x5a4,0x4ec,0x4f0,0x4f4)] for i in range(4)]))
 (ROOT/'artifacts/th14/dialogue-speaker-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n');print('PASS native speaker/expression',len(rows))
if __name__=='__main__':main()
