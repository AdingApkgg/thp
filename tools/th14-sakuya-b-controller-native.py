"""Retail Sakuya B startup and common tick. ANM/audio/cancel delivery boundaries."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main(selection=5):
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 base,player,bomb,spell,enemy,vm,laser,stack=0x70000000,0x70001000,0x70021000,0x70023000,0x70025000,0x70027000,0x70029000,0x700ff000
 bullet=0x71000000;m.mem_map(base,0x100000);m.mem_map(bullet,0xa00000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 point=lambda p:[get(p+i*4) for i in range(3)]
 events=[];created=0;missing=False
 def sink(machine,a,size,user):
  nonlocal created
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47ed10:
   if selection==2 and created==1:events.append(['shake',*[get(base+0x34000+off) for off in (0x1c,0x20,0x24,0x28)]])
   created+=1;events.append(['animation',get(sp+8),*point(get(sp+12))]);put(get(sp+4),created);m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x46e3d0:events.append(['sound',get(sp+4),0])
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,0 if missing else vm)
  elif a==0x415d79:events.append(['freeze',1])
  elif a==0x415e37:events.append(['freeze',0])
  elif a==0x41b3f0:events.append(['cancel',*point(get(sp+4)),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,get(sp+8)])
  elif a==0x450130:
   events.append(['circle',*point(get(sp+4)),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,m.reg_read(UC_X86_REG_XMM3)&0xffffffff,get(sp+8),get(sp+12)]);put(base+0x30010,3);m.reg_write(UC_X86_REG_EAX,base+0x30000)
  elif a==0x47f140:put(vm+(0x4a0 if get(sp+4)==1 else 0x4a4),get(sp+8))
  elif a==0x450270:
   events.append(['rectangle',*point(get(sp+4)),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,m.reg_read(UC_X86_REG_XMM3)&0xffffffff,get(sp+8),get(sp+12),get(sp+16)]);put(base+0x30010,1);m.reg_write(UC_X86_REG_EAX,base+0x30000)
  elif a==0x4854af:m.reg_write(UC_X86_REG_EAX,base+0x34000)
  elif a==0x401570:m.reg_write(UC_X86_REG_EAX,base+0x35000)
  elif a==0x48f980:
   dest=get(sp+4);m.mem_write(dest,bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,dest)
 for a,n in ((0x47ed10,28),(0x46e3d0,8),(0x47f0a0,4),(0x41b3f0,8),(0x450130,12),(0x47f140,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n));m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 for a in (0x415d79,0x415e37):m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 for a,n in ((0x450270,16),(0x4854af,0),(0x401570,4),(0x401120,8),(0x48f980,0),(0x4854a0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 def reset():
  nonlocal created
  m.mem_write(base,bytes(0xf0000));events.clear();created=0
  for p,v in ((0x4db67c,player),(0x4db52c,bomb),(0x4db534,spell),(0x4db544,enemy),(0x4db530,bullet),(0x4db664,laser),(0x4db550,base+0x32000),(bomb,{2:0x4bd818,3:0x4bd7fc,5:0x4bd7c4}[selection]),(player+0x10,base),(player+0x182d0,1),(player+0x182c4,10),(enemy+0x14,7),(0x4d8f58,0x3f800000)):put(p,v)
  m.mem_write(player+0x5e0,struct.pack('<fff',12.25,400,3));m.mem_write(bomb+0x624,struct.pack('<fff',12.25,400,3));put(bomb+0x40,1)
 def call(entry):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bomb);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(entry,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
 start=[]
 for flags,t in itertools.product((0,1,0x23),(0,59,60,120)):
  reset();put(spell+0x7c,flags);put(spell+0x28,t);put(spell+0x80,12345);call({2:0x412490,3:0x412e80,5:0x415c20}[selection])
  start.append(dict(flags=flags,time=t,events=events[:],result=[get(spell+0x7c),get(spell+0x80),get(enemy+0x14),get(player+0x182c4),get(bomb+0x638)],playerFlags=get(player+0x182d4)))
 ticks=[]
 for t,active,missing,rate,dialogue,advanced,dx in itertools.product({2:(-3,0,3,299,300,301,302),3:(-4,0,1,4,179,180,181,499,500,501),5:(-1,0,1,109,110,111,120)}[selection],(0,1,2),(False,True),(.5,1,1.25),(False,True) if selection==3 else (False,),(True,) if selection==5 else (False,True),(-128.,0.,128.) if selection==2 else (0.,)):
  reset();put(bomb+0x40,active);put(bomb+0x44,1);put(bomb+0x4c,2);put(bomb+0x18,t-int(advanced));put(bomb+0x1c,t);put(base+0x32194,int(dialogue));m.mem_write(bomb+0x20,struct.pack('<f',float(t)));put(bomb+0x24,0x4d8f58);m.mem_write(vm+0x60,struct.pack('<f',1.75));m.mem_write(0x4d8f58,struct.pack('<f',rate))
  if selection==2:
   put(bomb+0x638,0xbfc90fdb);put(player+0x182d4,0x24);put(player+0xd6dc,0x3f400000);m.mem_write(player+0x604,struct.pack('<f',dx));m.mem_write(player+0x5e0,struct.pack('<fff',14.25,300,4))
  call(0x412200)
  result=[get(bomb+0x40),get(bomb+0x44),get(bomb+0x1c),get(bomb+0x20)]
  if selection==3:result += [*point(bomb+0x624),get(bomb+0x638),get(vm+0x4a0),get(vm+0x4a4)]
  if selection==2:result += [*point(bomb+0x624),get(bomb+0x638),get(vm+0x4a0),get(vm+0x4a4),get(vm+0x50),get(player+0x182c4),get(player+0x182d4),get(player+0xd6dc)]
  ticks.append(dict(time=t,active=active,missing=missing,rate=rate,dialogue=dialogue,advanced=advanced,dx=dx,events=events[:],result=result))
 name={2:'marisa-a',3:'marisa-b',5:'sakuya-b'}[selection]
 (ROOT/f'artifacts/th14/{name}-controller-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),start=start,ticks=ticks),indent=2)+'\n',encoding='utf8');print(f'{len(start)} startup and {len(ticks)} {name} common tick cases.')
if __name__=='__main__':main()
