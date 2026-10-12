"""Retail HUD base-frame/demo/overlay/collection-hint requests; ANM services controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,game,front,old,replay,vm_base,stack=0x70000000,0x70001000,0x70002000,0x70005000,0x70006000,0x70010000,0x7002f000;m.mem_map(base,0x30000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 handles={};allocated=[];bindings=[];logo_phase=False
 def hook(uc,a,size,data):
  if logo_phase and a==0x42f19e:uc.emu_stop();return
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x47fcb0:
   vm=vm_base+len(allocated)*0x1000;allocated.append(vm);uc.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:
   vm=get(sp+4);bindings.append(get(sp+8));put(vm+0x580,vm);cleanup=8
  elif a==0x46fe50:pass
  elif a==0x47e890:
   p,vm=get(sp+4),get(sp+8);handle=1+len(handles);handles[handle]=vm;put(p,handle);uc.reg_write(UC_X86_REG_EAX,p);cleanup=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0));cleanup=4
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook)
 def reset():
  m.mem_write(base,bytes(0x2e000));handles.clear();handles[1]=old;allocated.clear();bindings.clear()
  put(game+0x2a4,front);put(0x4f56cc,base);m.mem_write(0x4f5815,b'\0');m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,game)
 def created():return [dict(script=s,flags=get(vm+0x1c)&0x200,position=[get(vm+p) for p in (0x59c,0x5a0,0x5a4)],rotation=get(vm+0x50)) for s,vm in zip(bindings,allocated)]
 base_rows=[]
 for prior in (0,1):
  reset();put(game+0x120,prior);m.emu_start(0x42ed3a,0x42edf6,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x42edf6
  base_rows.append(dict(prior=prior,created=created(),retained=bool(get(game+0x120))))
 rows=[]
 for stage,character,replay_mode,continues,demo,prior in itertools.product((1,2,7),range(3),(0,1,2),(0,1,9),(0,1),(0,1)):
  reset()
  for p,v in ((game+0xa0,prior),(0x4f58b8,0x40 if demo else 0),(0x4f58a4,stage),(0x4db558,replay),(replay+0x94,replay_mode),(0x4f5838,continues),(0x4f5828,character)):put(p,v)
  m.emu_start(0x42f19e,0x42f430,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x42f430
  rows.append(dict(stage=stage,character=character,replay=replay_mode,continues=continues,demo=demo,prior=prior,created=created(),retained=bool(get(game+0xa0))))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),baseRows=base_rows,rows=rows,scope='Retail42ed3a..42edf6 base frame0 retained in HUD+120 and42f19e..42f430 demo94, separate retained overlay111, first-stage hint67 iff replay+94/continues zero, character1 Y148 otherwise128 after initial update. All script/flags200/origin/rotation words compared with missing/existing retained roots. ANM allocation/binding/first update/registration/lookup controlled; unrelated HUD icon/timer/logo/indicator/difficulty setup and real ANM/GPU excluded. Production control_mode maps actual replay/demo input, with demo treated as replay by the session.')
 logo_rows=[];logo_phase=True
 for mode,flags in itertools.product((0,8,9),range(256)):
  reset();put(game+0x148,front);put(0x4d964c,mode);put(0x4f58b8,flags)
  try:m.emu_start(0x42f0cf,0x42f19e,count=100000)
  except Exception as exc:raise RuntimeError(f'logo mode={mode} flags={flags} ip={m.reg_read(UC_X86_REG_EIP):x} ebx={m.reg_read(UC_X86_REG_EBX):x}') from exc
  assert m.reg_read(UC_X86_REG_EIP)==0x42f19e
  logo_rows.append(dict(mode=mode,flags=flags,created=created()))
 result['logoRows']=logo_rows;result['logoScope']='Retail42f0cf..42f19e stage-logo resource script1, suppressed runtime8, flag40 demo or flag30==20 Spell Practice. Runtime modes0/8/9 and all low256 flag combinations. Resource locking disabled; ANM allocation/binding/first update/registration controlled. Logo script content, texture/GPU and thread synchronization excluded.'
 (ROOT/'artifacts/th14/hud-startup-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(base_rows)} base-frame / {len(rows)} startup / {len(logo_rows)} logo requests')
if __name__=='__main__':main()
