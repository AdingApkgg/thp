"""Complete retail dialogue constructor and portrait handle writes."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x20000);dialogue=base;manager=base+0x2000;resource=base+0x3000;instruction=base+0x4000;stack=base+0x1e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 vms={};copies=[];interrupts=[];updates=[]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);ecx=uc.reg_read(UC_X86_REG_ECX);result=0;pop=0
  if a==0x48f980:result=get(sp+4);m.mem_write(result,bytes([get(sp+8)&255])*get(sp+12))
  elif a==0x47fcb0:
   result=base+0x8000+len(vms)*0x800;vms[100+len(vms)]=result;m.mem_write(result,bytes(0x700))
  elif a==0x40af00:copies.append([ecx,get(sp+4),get(sp+8)]);pop=8
  elif a==0x46fe50:updates.append(ecx)
  elif a==0x47e890:
   result=get(sp+4);put(result,next(k for k,v in vms.items() if v==get(sp+8)));pop=8
  elif a==0x47f140:interrupts.append([get(sp+4),get(sp+8)]);pop=8
  elif a==0x47f0a0:result=vms.get(get(sp+4),0);pop=4
  elif a==0x41b880:pop=4
  elif a==0x43ac00:pop=8
  elif a in (0x424cb0,0x4350b0):pass
  else:return
  uc.reg_write(UC_X86_REG_EAX,result);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x48f980,0x47fcb0,0x40af00,0x46fe50,0x47e890,0x47f140,0x47f0a0,0x41b880,0x43ac00,0x424cb0,0x4350b0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4f56cc,manager);put(0x4d967c,resource);m.mem_write(0x4f5815,b'\0');put(stack,base+0x1f000);put(stack+4,instruction);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,dialogue);m.emu_start(0x431a70,base+0x1f000,count=50000);assert m.reg_read(UC_X86_REG_EIP)==base+0x1f000
 constructor=dict(scripts=[r[2] for r in copies],interrupts=interrupts[:],lines=[[get(vm+0x528)&0xffff,get(vm+0x1c)&0xa00,get(vm+0x5bc)] for vm in vms.values()],state=[get(dialogue+o) for o in (0x194,0x198,0x19c,0x1a0,0x1a4,0x1ac)])
 # Native 444211 loads text.anm into the exact constructor resource global.
 assert img.read(0x4be548,9)==b'text.anm\0'
 for n in range(-1,16):put(manager+0xa0+n*4,base+0x5000+(n+1)*0x100)
 put(0x4db544,manager);routes=[]
 for stage in range(1,8):
  put(0x4db69c,0x4d5988+stage*0xcc)
  for opcode,selection in [(op,s) for op in (2,20,31) for s in (range(3) if op!=31 else [1])]:
   vms.clear();copies.clear();updates.clear();interrupts.clear();m.mem_write(dialogue,bytes(0x200));put(dialogue+0x158,instruction);put(instruction+4,selection);m.mem_write(stack,bytes(512));put(stack+0xc,dialogue)
   m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,dialogue);m.reg_write(UC_X86_REG_ECX,instruction);m.emu_start(img.u32(0x433930+opcode*4),0x43369d,count=50000);assert m.reg_read(UC_X86_REG_EIP)==0x43369d
   routes.append(dict(stage=stage,selection=selection,opcode=opcode,handleWords=[get(dialogue+0x40+i*4) for i in range(13)],script=copies[0][2]))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),constructor=constructor,portraitRoutes=[r for r in routes if r['opcode']==2],assetRoutes=routes)
 (ROOT/'artifacts/th14/dialogue-initialize-native.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
