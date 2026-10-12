"""Retail42f430..42f68b HUD difficulty initialization; ANM services controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,game,front,old,vm_base,stack=0x70000000,0x70001000,0x70002000,0x70005000,0x70010000,0x7001f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 handles={};allocated=[];bindings=[]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x47fcb0:
   vm=vm_base+len(allocated)*0x1000;allocated.append(vm);uc.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:
   vm=get(sp+4);bindings.append(get(sp+8));put(vm+0x580,vm);cleanup=8
  elif a==0x46fe50:pass
  elif a==0x47e890:
   p,vm=get(sp+4),get(sp+8);handle=2+len(handles)-1;handles[handle]=vm;put(p,handle);uc.reg_write(UC_X86_REG_EAX,p);cleanup=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0));cleanup=4
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook);rows=[]
 for difficulty,initial,prior,pending in itertools.product(range(5),(0,1),(0,1),(0,7)):
  m.mem_write(base,bytes(0x1e000));handles.clear();handles[1]=old if prior else 0;allocated.clear();bindings.clear()
  for p,v in ((game+0x2a4,front),(game+0x108,1 if prior else 0),(old+0x4a0,pending),(0x4f5834,difficulty),(0x4d9658,initial),(0x4f56cc,base)):put(p,v)
  m.mem_write(0x4f5815,b'\0');m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,game);m.emu_start(0x42f430,0x42f68b,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x42f68b
  rows.append(dict(difficulty=difficulty,initial=initial,prior=prior,pending=pending,oldPending=get(old+0x4a0),created=[dict(script=s,flags=get(vm+0x1c)&0x200,position=[get(vm+p) for p in (0x59c,0x5a0,0x5a4)],rotation=get(vm+0x50),pending=get(vm+0x4a0)) for s,vm in zip(bindings,allocated)]))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Retail42f430..42f68b difficulty-intro option branch and label creation for all five difficulties, with missing/existing old intro and two prior interrupt values. Native script selection79+difficulty/85+difficulty, flag200, zero origin/rotation and repeated intro interrupt3 compared. ANM allocation/template binding/first update/registration/lookup controlled, no child callbacks, actual ANM frames or GPU. Initial-stage option supplied at original global4d9658; mapping the full caller to this option excluded.')
 (ROOT/'artifacts/th14/hud-difficulty-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} original HUD difficulty entries')
if __name__=='__main__':main()
