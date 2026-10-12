"""Execute retail MSG portrait/text close and visibility handlers, including actual panel retirement."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x20000);dialogue=base;instruction=base+0x1000;stack=base+0x1f000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 vms={100+i:base+0x2000+i*0x1000 for i in range(13)};interrupts=[]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,vms.get(get(sp+4),0));pop=4
  elif a==0x47f140:interrupts.append([get(sp+4),get(sp+8)]);pop=8
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x47f0a0,0x47f140):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4f56cc,base+0x12000);rows=[]
 for op,selection in itertools.product((3,4,5,6,23,24,30),range(4)):
  m.mem_write(dialogue,bytes(0x200));put(dialogue+0x158,instruction);put(instruction+4,selection)
  for i in range(13):
   put(dialogue+0x40+i*4,100+i);vm=vms[100+i];m.mem_write(vm,bytes(0x900));put(vm+0x584,vm+0x800);put(vm+0x800,vm+0x700);put(vm+0x804,0)
  interrupts.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,dialogue);m.reg_write(UC_X86_REG_ECX,instruction);m.reg_write(UC_X86_REG_ESI,base+0x12000);start=img.u32(0x433930+op*4)
  if start!=0x43369d:m.emu_start(start,0x43369d,count=5000)
  rows.append(dict(input=[op,selection],handles=[get(dialogue+0x40+i*4) for i in range(13)],interrupts=interrupts[:],retired=[[get(vm+0x1c)&32,get(vm+0x700+0x1c)&32] for vm in vms.values()]))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows)
 (ROOT/'artifacts/th14/dialogue-lifecycle-native.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native lifecycle',len(rows))
if __name__=='__main__':main()
