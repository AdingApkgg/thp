"""Full4350b0 boss-name selection and430c55..430d6b remaining markers."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,game,front,old,vm_base,stack=0x70000000,0x70001000,0x70002000,0x70004000,0x70010000,0x7002f000;m.mem_map(base,0x30000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 handles={};allocated=[];bindings=[];interrupts=[]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x47fcb0:vm=vm_base+len(allocated)*0x1000;allocated.append(vm);uc.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:vm=get(sp+4);bindings.append(get(sp+8));put(vm+0x580,vm);cleanup=8
  elif a==0x46fe50:pass
  elif a==0x47e890:p,vm=get(sp+4),get(sp+8);handle=100+len(allocated);handles[handle]=vm;put(p,handle);uc.reg_write(UC_X86_REG_EAX,p);cleanup=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0));cleanup=4
  elif a==0x47f140:interrupts.append([get(sp+4),get(sp+8)]);cleanup=8
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook)
 def reset():
  m.mem_write(base,bytes(0x2e000));handles.clear();allocated.clear();bindings.clear();interrupts.clear();put(game+0x2a4,front);put(0x4f56cc,base);m.mem_write(0x4f5815,b'\0');m.reg_write(UC_X86_REG_ESP,stack)
 def created():return [dict(script=s,flags=get(vm+0x1c)&0x200,position=[get(vm+p) for p in (0x59c,0x5a0,0x5a4)],rotation=get(vm+0x50)) for s,vm in zip(bindings,allocated)]
 names=[]
 for stage,section,spell,subtype,prior in itertools.product(range(1,8),(-1,0,4,5,6,24),(-1,0,51,52,63,64),range(2),range(3)):
  reset();put(game+0xdc,prior);handles[1]=old
  for p,v in ((0x4f58a4,stage),(0x4f58ac,section),(0x4f5844,spell),(0x4f582c,subtype),(0x4db69c,0x4d5988+stage*0xcc)):put(p,v)
  put(stack,base);m.reg_write(UC_X86_REG_ECX,game);m.emu_start(0x4350b0,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
  names.append(dict(stage=stage,section=section,spell=spell,subtype=subtype,prior=prior,created=created(),retained=bool(get(game+0xdc))))
 markers=[]
 for remaining,pattern in itertools.product((-1,0,1,2,5,9,10,11,100),range(4)):
  reset();put(game+0x158,remaining)
  before=[]
  for n in range(10):
   handle=n+1 if pattern==1 or (pattern==2 and n%2==0) or pattern==3 else 0;before.append(bool(handle));put(game+0xe0+n*4,handle)
  m.reg_write(UC_X86_REG_EDI,game);m.emu_start(0x430c55,0x430d6b,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x430d6b
  markers.append(dict(remaining=remaining,pattern=pattern,before=before,created=created(),interrupts=interrupts[:],retained=[bool(get(game+0xe0+n*4)) for n in range(10)]))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),names=names,markers=markers,scope='Full4350b0 retains live boss-name handle, clears stale handle, selects seven retail descriptors+5c/+80 including stage4 section5, spell52..63 and negative-spell subtype1 branches.430c55..430d6b ten remaining markers68..77 with creation/retention/interrupt1 independent of boss presence. Exact scripts/flags200/origin/rotation/retained slots; ANM allocation/binding/first update/lookup/registration/interrupt delivery controlled. Excludes full boss health-circle callback, name caller gating, actual ANM frames/children/GPU.')
 (ROOT/'artifacts/th14/hud-boss-labels-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(names)} original boss-name / {len(markers)} remaining-marker cases')
if __name__=='__main__':main()
