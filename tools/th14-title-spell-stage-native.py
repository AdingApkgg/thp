"""Actual462c00/463020 stage/loadout selector; ANM service controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,sup,resource,vm,stack=0x70000000,0x70001000,0x70050000,0x70070000,0x70071000,0x700ff000;m.mem_map(base,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def hook(uc,a,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP);this=uc.reg_read(UC_X86_REG_ECX);pop=None
  if a==0x458d70:
   script=get(sp+4);put(this+0x2c8+script*4,1000+script);events.append(['create',script]);pop=4
  elif a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,vm);pop=0
  elif a==0x40af00:events.append(['ascii',get(sp+8)]);pop=8
  elif a==0x46fe50:pop=0
  elif a==0x47e890:put(get(sp+4),1261);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=4
  elif a in (0x47f140,0x47f1b0):events.append(['interrupt',get(sp+4),get(sp+8)]);pop=8
  elif a==0x46e3d0:events.append(['sound',get(sp+4)]);pop=8
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def setup(state,timer,stage=0,loadout=0,resume=-1,background=0):
  m.mem_write(base,bytes(0xfe000));put(0x4db520,sup);put(sup+0x191e4,resource);put(0x4f56cc,sup+0x1a000);put(0x4d8f58,0x3f800000);m.mem_write(0x4f5815,b'\0');put(0x4f5828,loadout>>1);put(0x4f582c,loadout&1);put(0x4d5ff0,resume);put(0x4d5ff4,2)
  for off,v in ((0x1c,17),(0x24,state),(0x28,stage),(0x30,7),(0x34,3),(0x74,10),(0xb4,1),(0xf8,1),(0x5c90,loadout),(0x5c98,6),(0x5d60,1),(0x5d68,0),(0x2b4,timer-1),(0x2b8,timer),(0x2bc,0x3f800000),(0x2c0,0x4d8f58),(0x2c4,1),(0x460,1102),(0x5e0,1198 if background else 0),(0x6d4,1259 if background else 0),(0x6dc,1261 if background else 0)):put(menu+off,v)
  put(0x4d6884,0);put(0x4d6880,0);events.clear()
 def call():
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x462c00,base,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP))
 def snap():return dict(screen=get(menu+0x1c),substate=get(menu+0x24),selected=get(menu+0x28),count=get(menu+0x30),depth=get(menu+0xb4),loadout=get(menu+0x5c90),stage=get(menu+0x5d68),last=get(0x4d5ff4),resume=get(0x4d5ff0),events=events[:])
 entries=[]
 for resume,loadout,background in itertools.product((-1,0,6),range(6),(0,1)):
  setup(0,0,loadout=loadout,resume=resume,background=background);call();entries.append(dict(resume=resume,loadout=loadout,background=background,result=snap()))
 controls=[]
 for stage,loadout,pressed in itertools.product(range(7),range(6),(0,16,32,64,128,1,2,16|64,32|128,64|1,128|2)):
  setup(2,17,stage,loadout,background=1);put(0x4d6884,pressed);call();controls.append(dict(stage=stage,loadout=loadout,pressed=pressed,result=snap()))
 boundaries=[]
 for state,timer,stage in itertools.product((1,3,4),(5,6,10,11,19,20),(0,6)):
  setup(state,timer,stage,background=1);call();boundaries.append(dict(state=state,timer=timer,stage=stage,result=snap()))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),entries=entries,controls=controls,boundaries=boundaries,scope='Full actual462c00 and463020: seven stage/six loadout selection, history, 10/20/6 clock gates, cancellation, resumed stage route. Real cursor/stack/timer helpers; ANM allocation/lookup/interrupt services controlled. Does not prove subsequent spell selection/difficulty/gameplay or rendered ANMs.')
 (ROOT/'artifacts/th14/title-spell-stage-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(entries)} entries, {len(controls)} controls, {len(boundaries)} boundaries')
if __name__=='__main__':main()
