"""Retail spell compact-result control44b0f0, unchanged native cursor/input clocks."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,front,score,stack=0x70000000,0x70001000,0x70005000,0x70010000,0x700ff000;m.mem_map(base,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<i',m.mem_read(p,4))[0]
 events=[]
 def hook(uc,a,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP);pop=None
  if a==0x44c1a0:events.append(['create',get(sp+8)]);put(get(sp+4),100);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=12
  elif a==0x47fb30:events.append(['choose',get(sp+8)]);put(get(sp+4),200);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=12
  elif a==0x47f140:events.append(['interrupt',get(sp+4),get(sp+8)]);pop=8
  elif a==0x46e3d0:events.append(['sound',get(sp+4)]);pop=8
  elif a==0x47f560:events.append(['hide']);pop=0
  elif a==0x447da0:events.append(['save']);pop=0
  elif a==0x454f50:uc.reg_write(UC_X86_REG_EAX,0);pop=0
  elif a==0x485ddf:m.mem_write(get(sp+4),b'th14_01.rpy\0');pop=0
  elif a==0x46ac20:uc.reg_write(UC_X86_REG_XMM0,0);pop=0
  elif a==0x4854a0:pop=0
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def run(state,timer,selected,pressed,repeat,completed):
  m.mem_write(base,bytes(0x40000));events.clear()
  for p,v in ((0x4db68c,score),(0x4db558,base+0x9000),(0x4f58b8,32),(0x4f5834,2),(0x4f58a4,3),(0x4f5830,12345),(0x4f5828,0),(0x4f582c,0),(0x4d6884,pressed),(0x4d6880,repeat),(0x4d964c,0),(menu+4,state),(menu+0x14,timer),(menu+0x20,1),(menu+0x1f4,completed),(menu+0x38,selected),(menu+0x3c,selected),(menu+0x40,3),(menu+0x108,1),(menu+0x1e8,100),(menu+0x1ec,101),(menu+0x3e4,front),(menu+0x2d8,0x3f800000)):put(p,v)
  m.mem_write(0x4d8f58,struct.pack('<f',1));put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x44b0f0,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP))
  return dict(state=get(menu+4),selected=get(menu+0x38),previous=get(menu+0x3c),count=get(menu+0x40),depth=get(menu+0xc4),disabled=get(menu+0x10c),timer=get(menu+0x14),destination=get(0x4d964c),events=events[:],recordChanged=any(m.mem_read(score,0x2422c)))
 entries=[]
 for completed,timer in itertools.product((0,1),(0,9,10,11,80)):
  state=30 if completed else 24;entries.append(dict(completed=completed,timer=timer,result=run(state,timer,2,0,0,completed)))
 controls=[]
 for completed,selected,(pressed,repeat) in itertools.product((0,1),range(3),((0,0),(16,0),(32,0),(0,16),(0,32),(0x102,0),(1,0),(0x80000,0),(0x103,0))):controls.append(dict(completed=completed,selected=selected,pressed=pressed,repeat=repeat,result=run(25,17,selected,pressed,repeat,completed)))
 exits=[]
 for completed,selected,timer in itertools.product((0,1),range(3),(0,11,12,13)):
  exits.append(dict(completed=completed,selected=selected,timer=timer,result=run(29,timer,selected,0,0,completed)))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),entries=entries,controls=controls,exits=exits,scope='Complete retail44b0f0 callback for SpellPr failure/completion initialization, compact three choices, movement/repeat/cancel/confirm including empty replay-slot scan, and twelve-frame Title/Retry exits. Original44a170 record dispatch,44a0e0 exit cleanup and native cursors/input/timer execute. ANM/audio/save/file/slowdown services controlled; no replay serialization, name input, GPU or natural capture equivalence.')
 (ROOT/'artifacts/th14/spell-end-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(entries)} entries / {len(controls)} controls / {len(exits)} exits')
if __name__=='__main__':main()
