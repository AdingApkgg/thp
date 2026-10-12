"""Retail45ef40 Replay menu; ANM/catalog/audio/platform services controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,sup,resource,vm,entry,decoded,stack=0x70000000,0x70001000,0x70050000,0x70070000,0x70071000,0x70080000,0x70090000,0x700ff000;m.mem_map(base,0x100000)
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
  elif a==0x47e890:put(get(sp+4),79);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=4
  elif a in (0x47f140,0x47f1b0):events.append(['interrupt',get(sp+4),get(sp+8)]);pop=8
  elif a==0x48f980:m.mem_write(get(sp+4),bytes([get(sp+8)&255])*get(sp+12));pop=0
  elif a==0x403c30:events.append(['scan']);pop=8
  elif a==0x46e3d0:events.append(['sound',get(sp+4)]);pop=8
  elif a==0x46ef90:events.append(['audio',get(sp+4),get(sp+8)]);pop=12
  elif a==0x41eea0:put(get(sp+4),79);uc.reg_write(UC_X86_REG_EAX,get(sp+4));events.append(['fade']);pop=16
  elif a==0x420d20:events.append(['loading']);pop=0
  elif a==0x456350:events.append(['mode',get(sp+4)]);pop=4
  elif a in (0x454b60,0x4854fe):pop=0
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def setup(state,timer,selected=0,page=0,mask=0,spell=0,flags=0,last=0,background=0):
  m.mem_write(base,bytes(0xfe000));put(0x4db520,sup);put(sup+0x191e4,resource);put(0x4f56cc,sup+0x1a000);put(0x4d8f58,0x3f800000);m.mem_write(0x4f5815,b'\0');put(0x4db6b0,last)
  for off,v in ((0x1c,11),(0x24,state),(0x28,selected),(0x30,7 if state==4 else 25),(0x34,4),(0x74,10),(0xb4,1),(0xf8,1),(0x1d8,page),(0x1e0,3),(0x2a8,1),(0x2b4,timer-1),(0x2b8,timer),(0x2bc,0x3f800000),(0x2c0,0x4d8f58),(0x2c4,1),(0x5c8c,flags),(0x5aec,page*25+17),(0x5af0,3),(0x420,background),(0x6dc,0)):put(menu+off,v)
  if state==4:put(menu+0xb4,2);put(menu+0x38,17);put(menu+0x78,25)
  put(entry+0x1c,decoded);m.mem_write(entry+0x220,b'th14_01.rpy\0');m.mem_write(decoded+10,bytes([spell]));put(decoded+0x90,1)
  if mask:
   for n in range(75):put(menu+0x5af4+n*4,entry)
   for n in range(7):put(entry+0x100+n*0x28,decoded+0x94 if mask&(1<<n) else 0)
  put(0x4d6884,0);put(0x4d6880,0);events.clear()
 def call():
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x45ef40,base,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP))
 def snap():return dict(screen=get(menu+0x1c),substate=get(menu+0x24),selected=get(menu+0x28),count=get(menu+0x30),page=get(menu+0x1d8),depth=get(menu+0xb4),disabled=get(menu+0xfc),flags=get(menu+0x5c8c),file=get(menu+0x5aec),stage=get(menu+0x5af0),last=get(0x4db6b0),events=events[:])
 init=[]
 for last,background in itertools.product((0,24,25,49,50,74),(0,1086)):
  setup(0,0,last=last,background=background);call();init.append(dict(last=last,background=background,result=snap()))
 controls=[]
 for selected,page,mask,spell,pressed in itertools.product((0,1,24),range(3),(0,1,4,64,127),(0,2),(0,16,32,64,128,1,2)):
  setup(2,17,selected,page,mask,spell);put(0x4d6884,pressed);call();controls.append(dict(selected=selected,page=page,mask=mask,spell=spell,pressed=pressed,result=snap()))
 stages=[]
 for selected,timer,pressed in itertools.product(range(7),(14,15),(0,16,32,1,2)):
  setup(4,timer,selected,0,127);put(0x4d6884,pressed);call();stages.append(dict(selected=selected,timer=timer,pressed=pressed,result=snap()))
 boundaries=[]
 for state,timer,flags in itertools.product((1,3,5),(2,5,6,7,31,32),(0,8)):
  setup(state,timer,mask=127 if state==3 else 0,flags=flags);call();boundaries.append(dict(substate=state,timer=timer,flags=flags,result=snap()))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),init=init,controls=controls,stages=stages,boundaries=boundaries,scope='Actual45ef40 Replay callback, real cursor/history/disabled-stage helpers, three pages/empty and nonempty records, spell-record auto-start, scanner-ready gates, stage selection, playback request. ANM/catalog/thread/file/audio/fade/loading/mode services controlled; not scanner-thread/GPU/audio/full campaign equivalence.')
 (ROOT/'artifacts/th14/title-replay-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(init)} entries, {len(controls)} controls, {len(stages)} stage inputs, {len(boundaries)} readiness/time boundaries')
if __name__=='__main__':main()
