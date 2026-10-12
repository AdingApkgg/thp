"""Run retail MSG 2/20/31 selection, stopping before ANM allocation."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,manager,instruction,stack=0x70000000,0x70001000,0x70002000,0x7000f000;m.mem_map(base,0x10000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 for n in range(-1,16):put(manager+0xa0+n*4,base+0x3000+(n+1)*0x100)
 put(0x4db544,manager);m.mem_write(0x4f5815,b'\0');rows=[]
 for stage in range(1,8):
  put(0x4db69c,0x4d5988+stage*0xcc)
  for op,start,stop in ((2,0x432c5e,0x432c8d),(20,0x433536,0x433561),(31,0x432d4d,0x432d70)):
   assert img.u32(0x433930+op*4)==start
   for selection in (range(3) if op!=31 else [1]):
    put(instruction+4,selection);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,instruction)
    m.emu_start(start,stop,count=1000);assert m.reg_read(UC_X86_REG_EIP)==stop
    resource=(m.reg_read(UC_X86_REG_EBX) if op!=2 else get(stack+0x20));file=(resource-(base+0x3000))//0x100-1
    rows.append(dict(stage=stage,selection=selection,opcode=op,file=file,script=get(stack+0x10)))
 fades=[]
 for stage in range(1,8):
  for op,start in ((22,0x433633),(27,0x43366e)):
   assert img.u32(0x433930+op*4)==start
   for value in ([0] if op==22 else [0,0x80000000,0x3e800000,0x41000000,0xbf800000,0x7f800000]):
    put(0x4f58a4,stage);put(instruction+4,value);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,instruction);m.reg_write(UC_X86_REG_XMM1,0x40000000)
    m.emu_start(start,0x445840,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x445840
    fades.append(dict(stage=stage,opcode=op,value=value,result=m.reg_read(UC_X86_REG_XMM1)&0xffffffff))
 # MSG 32 executes through the shared reset epilogue. Replace only ANM
 # handle lookup and interrupt delivery, retaining all retail state writes.
 dialogue=base+0x6000;vms=[base+0x7000+n*0x800 for n in range(4)];interrupts=[]
 def hook(uc,a,size,data):
  if a not in (0x47f140,0x47f0a0):return
  sp=uc.reg_read(UC_X86_REG_ESP);handle=get(sp+4)
  if a==0x47f140:
   interrupts.append([handle,get(sp+8)]);cleanup=8
  else:
   assert 103<=handle<=106;uc.reg_write(UC_X86_REG_EAX,vms[handle-103]);cleanup=4
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook);speaker_resets=[]
 assert img.u32(0x433930+32*4)==0x433107
 for selection in range(3):
  for flags in (0,2,0x3f,0xffffffff):
   for displacement in (0,0x80000000,0x3f800000,0x7fc00000):
    m.mem_write(dialogue,bytes(0x200));put(dialogue+0x158,instruction);put(instruction+4,selection)
    for n in range(8):put(dialogue+0x4c+n*4,100+n)
    put(dialogue+0x184,flags);put(dialogue+0x188,17);put(dialogue+0x18c,19);put(0x4f56cc,manager)
    for n,vm in enumerate(vms):
     for off,value in ((0x4ec,0x3f000000+n),(0x4f0,displacement),(0x4f4,0x40000000+n),(0x59c,0x42c80000+n),(0x5a0,0x43480000+n),(0x5a4,0x43960000+n)):put(vm+off,value)
    interrupts.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,dialogue)
    m.emu_start(0x433107,0x43369d,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x43369d
    speaker_resets.append(dict(selection=selection,flags=flags,displacement=displacement,state=[get(dialogue+off) for off in (0x190,0x184,0x188,0x18c)],interrupts=interrupts[:],lines=[[get(vm+off) for off in (0x4ec,0x4f0,0x4f4,0x59c,0x5a0,0x5a4)] for vm in vms]))
 out=ROOT/'artifacts/th14/dialogue-assets-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,fades=fades,speakerResets=speaker_resets),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail dialogue asset selections; {len(fades)} music fade deliveries; {len(speaker_resets)} MSG 32 resets.')
if __name__=='__main__':main()
