"""Retail460a00 Results /4613c0 ReplaySave, with ANM/audio/file/score services controlled."""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,score,supervisor,resource,vm,out,stack=0x70000000,0x70001000,0x70010000,0x70050000,0x70070000,0x70071000,0x70074000,0x7007f000;m.mem_map(base,0x80000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[];rank=0
 def hook(uc,a,size,data):
  pop=None;sp=uc.reg_read(UC_X86_REG_ESP);this=uc.reg_read(UC_X86_REG_ECX)
  if a==0x458d70:
   script=get(sp+4);put(this+0x2c8+script*4,1000+script);events.append(['create',script]);pop=4
  elif a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,vm);pop=0
  elif a==0x40af00:events.append(['ascii',get(sp+8)]);pop=8
  elif a==0x46fe50:pop=0
  elif a==0x47e890:put(get(sp+4),79);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,0);pop=4
  elif a in (0x47f140,0x47f1b0):events.append(['interrupt',get(sp+4),get(sp+8)]);pop=8
  elif a==0x447e00:uc.reg_write(UC_X86_REG_EAX,rank&0xffffffff);pop=0
  elif a==0x445710:events.append(['music',get(sp+8)]);pop=8
  elif a==0x445690:pop=8
  elif a==0x46e3d0:events.append(['sound',get(sp+4)]);pop=8
  elif a==0x455020:events.append(['recording-finish']);pop=0
  elif a==0x454b60:pop=0
  elif a==0x4854fe:pop=0
  elif a==0x454f50:uc.reg_write(UC_X86_REG_EAX,0);pop=0
  elif a==0x485ddf:uc.reg_write(UC_X86_REG_EAX,0);pop=0
  elif a==0x48f980:pop=0
  elif a==0x4a0380:pop=0
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def setup(selection,difficulty,continues,substate,timer=0):
  m.mem_write(base,bytes(0x7e000));put(0x4db68c,score);put(0x4db520,supervisor);put(supervisor+0x191e4,resource);put(0x4f56cc,out);put(0x4db688,0)
  put(0x4d8f58,0x3f800000);m.mem_write(0x4f5815,b'\0')
  for a,v in ((0x4f5828,selection//2),(0x4f582c,selection%2),(0x4f5834,difficulty),(0x4f5838,continues),(0x4d6884,0),(0x4d6880,0)):put(a,v)
  for off,v in ((0x1c,14),(0x24,substate),(0x2b4,timer-1),(0x2b8,timer),(0x2bc,0x3f800000),(0x2c0,0x4d8f58),(0x2c4,1),(0x30,30),(0xf8,1),(0x28,2),(0x5a00,0),(0x5a08,91),(0x5ad0,1)):put(menu+off,v)
  m.mem_write(score+0x2423c,b'        \0');events.clear()
 def call(a):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(a,base,count=200000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP))
 def snapshot():return dict(screen=get(menu+0x1c),substate=get(menu+0x24),selected=get(menu+0x28),nameSelected=get(menu+0x5a00),nameLength=get(menu+0x59f4),unranked=get(menu+0x59f8),name=bytes(m.mem_read(menu+0x59e8,9)).hex(),savedName=bytes(m.mem_read(score+0x2423c,9)).hex(),events=events[:])
 init=[]
 for selection,difficulty,r in itertools.product(range(6),range(5),(-1,0,9)):
  rank=r;setup(selection,difficulty,0,0);call(0x460a00);init.append(dict(selection=selection,difficulty=difficulty,rank=rank,result=snapshot()))
 exits=[]
 for selection,difficulty,continues,timer in itertools.product(range(6),range(5),(0,1,9),(5,6)):
  setup(selection,difficulty,continues,3,timer)
  for script in (100,152+selection,158+difficulty):put(menu+0x2c8+script*4,1000+script)
  put(menu+0x6dc,79);call(0x460a00);exits.append(dict(selection=selection,difficulty=difficulty,continues=continues,timer=timer,result=snapshot()))
 names=[]
 for selected,length,pressed in itertools.product(range(91),(0,7,8),(1,2)):
  setup(0,1,0,2,17);put(menu+0x5a00,selected);put(menu+0x59f4,length);m.mem_write(menu+0x59e8,b'ABCDEFGH\0');put(0x4d6884,pressed);call(0x460a00);names.append(dict(selected=selected,length=length,pressed=pressed,result=snapshot()))
 replay=[]
 for substate,timer,pressed in ((0,0,0),(1,6,0),(1,7,0),(2,17,2),(4,5,0),(4,6,0)):
  setup(0,1,0,substate,timer);put(menu+0x1c,15);put(0x4d6884,pressed);put(menu+0x6dc,79);put(menu+0x45c,1101);call(0x4613c0);replay.append(dict(substate=substate,timer=timer,pressed=pressed,result=snapshot()))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),init=init,exits=exits,names=names,replay=replay,scope='Actual retail460a00 Results and4613c0 ReplaySave callbacks, actual state/timer/cursor methods and name/save-name memory writes. Score insertion rank, ANM factory/lookup/interrupt, music/sound, replay/file/allocation services controlled. Observes script ids, root ascii19, routing with continue count and keyboard name actions. Does not prove score insertion, replay serialization, asynchronous scanner, GPU pixels/audio or full native menu equivalence.')
 (ROOT/'artifacts/th14/results-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(init)} retail Results entries, {len(exits)} exits, {len(names)} name inputs, {len(replay)} ReplaySave boundaries')
if __name__=='__main__':main()
