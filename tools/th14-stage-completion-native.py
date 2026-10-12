"""Execute complete retail436f90 and its434c10 award; control ANM/exit services."""
import hashlib,importlib,json,struct,itertools
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x80000)
 score,ctl,hud,player,resource,vm,stack= [base+n for n in (0x1000,0x30000,0x31000,0x32000,0x33000,0x34000,0x7f000)]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def hook(uc,a,size,data):
  if a not in (0x47fcb0,0x40af00,0x46fe50,0x47e890,0x4358e0,0x448ef0,0x449f20):return
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:events.append(['animation',get(sp+8)]);cleanup=8
  elif a==0x47e890:put(get(sp+4),1234);uc.reg_write(UC_X86_REG_EAX,get(sp+4));cleanup=8
  elif a==0x448ef0:events.append(['replay_end'])
  elif a==0x449f20:events.append(['results'])
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook)
 inputs=[]
 for stage,difficulty,practice,replay in itertools.product(range(1,8),range(5),range(2),range(2)):
  inputs.append(dict(stage=stage,difficulty=difficulty,practice=practice,replay=replay,selection=len(inputs)%6,continues=(len(inputs)//6)%2,lives=2,bombs=3,score=0,count=0,clean=0))
 for stage,difficulty,lives,bombs,initial in itertools.product((6,7),range(5),(0,8,-1,2147483647),(0,8,-1),(999999000,0xffffffff)):
  inputs.append(dict(stage=stage,difficulty=difficulty,practice=0,replay=0,selection=len(inputs)%6,continues=0,lives=lives,bombs=bombs,score=initial,count=99998,clean=99998))
 for selection,difficulty,continues,count in itertools.product(range(6),range(5),(0,1),(99998,99999,100000,0xffffffff)):
  inputs.append(dict(stage=6,difficulty=difficulty,practice=0,replay=0,selection=selection,continues=continues,lives=2,bombs=3,score=0,count=count,clean=count))
 rows=[]
 for args in inputs:
  m.mem_write(score,bytes(0x24680));m.mem_write(ctl,bytes(0x600));m.mem_write(hud,bytes(0x600));m.mem_write(player,bytes(0x100));m.mem_write(vm,bytes(0x800))
  for address,value in ((0x4db68c,score),(0x4db558,ctl),(0x4db550,hud),(0x4db52c,player),(hud+0x2a4,resource),(ctl+0x94,args['replay']),
    (0x4f5828,args['selection']//2),(0x4f582c,args['selection']%2),(0x4f5834,args['difficulty']),(0x4f5838,args['continues']),(0x4f58a4,args['stage']),
    (0x4f5864,args['lives']),(0x4f5870,args['bombs']),(0x4f5830,args['score']),(0x4f58b8,args['practice']<<4),(0x4d964c,0),(0x4db69c,0)):
   put(address,value)
  m.mem_write(0x4f5815,b'\0');cr=score+8+args['selection']*0x5298
  put(cr+0x7c0+args['difficulty']*4,args['count']);put(cr+0x7dc+args['difficulty']*4,args['clean'])
  # The unused second byte and opaque bytes must survive a first-flag write.
  for i in range(1,49):m.mem_write(cr+0x7f4+i*8,b'\0\xa5')
  events.clear();put(stack,base);m.reg_write(UC_X86_REG_ESP,stack)
  m.emu_start(0x436f90,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
  rows.append(dict(**args,resultScore=get(0x4f5830),bonus=get(hud+0x2a8),countResult=get(cr+0x7c0+args['difficulty']*4),cleanResult=get(cr+0x7dc+args['difficulty']*4),
   pairs=[list(m.mem_read(cr+0x7f4+i*8,2)) for i in range(1,49)],events=events[:],nextStage=get(0x4f58a4),transition=get(0x4d964c),ending=bool(get(ctl+0x80)&0x4000),hudFlags=get(hud+0x17c)))
 clock=[];allocation=base+0x35000;callbacks=[base+0x36000,base+0x36100];allocated=[]
 def clock_hook(uc,a,size,data):
  if a not in (0x4854af,0x48f980,0x401570,0x401120,0x4011d0):return
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x4854af:uc.reg_write(UC_X86_REG_EAX,allocation)
  elif a==0x48f980:m.mem_write(get(sp+4),bytes([get(sp+8)&255])*get(sp+12))
  elif a==0x401570:uc.reg_write(UC_X86_REG_EAX,callbacks[len(allocated)]);allocated.append(get(sp+4));cleanup=4
  else:events.append(['register',a,get(sp+8)]);cleanup=8
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,clock_hook)
 for frame,replay,force,active in itertools.product((-1,0,178,179,180,378,379,380,2147483646,2147483647),range(2),range(2),range(2)):
  m.mem_write(ctl,bytes(0x600));m.mem_write(allocation,bytes(0x2000));put(ctl+0x80,0x4000 if active else 0);put(ctl+0x98,frame);put(ctl+0x94,replay);put(0x4d9684,0x2000 if force else 0);put(0x4d964c,0)
  events.clear();allocated.clear();put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ctl)
  m.emu_start(0x436620,0x436769,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x436769
  clock.append(dict(frame=frame,replay=replay,force=force,active=active,resultFrame=get(ctl+0x98),transition=get(0x4d964c),events=events[:],fade=[get(allocation+o) for o in (0x10,0x1c,0x20,0x24,0x28)] if allocated else None))
 result_clock=[];rate_pointer=base+0x37000
 for flags,frame,speed in itertools.product((0,0x80,0x100,0x200,0x400,0x700,0x180,0x680),(-1,0,119,120,2147483647),(.25,.5,1.,2.)):
  m.mem_write(hud,bytes(0x1000));put(hud+0x17c,flags);put(hud+0x184,frame);put(hud+0x180,frame-1);put(hud+0x18c,rate_pointer)
  m.mem_write(hud+0x188,struct.pack('<f',float(frame)));m.mem_write(rate_pointer,struct.pack('<f',speed));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,hud);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x42fdb0,0x42fe31,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x42fe31
  signed_frame=struct.unpack('<i',m.mem_read(hud+0x184,4))[0]
  result_clock.append(dict(flags=flags,frame=frame,speed=speed,words=[get(hud+0x184),get(hud+0x180),get(hud+0x188),int(not(flags&0x100) or signed_frame>119)]))
 out=ROOT/'artifacts/th14/stage-completion-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,clock=clock,resultClock=result_clock),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} retail stage completion and{len(clock)} ending-clock cases')
if __name__=='__main__':main()
