"""Actual retail Sakuya A startup/common update; controlled ANM, audio and item/cancel delivery."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,im.data[raw:raw+n])
 end,player,bomb,spell,enemy,vm,aux,stack=0x70000000,0x70001000,0x70021000,0x70023000,0x70025000,0x70027000,0x70028000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 point=lambda p:[get(p+j*4) for j in range(3)]
 events=[];lasers=[];created=0;missing_main=False;missing_aux=False
 def sink(machine,a,size,user):
  nonlocal created
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47ed10:
   created+=1;events.append(['animation',get(sp+8),*point(get(sp+12))]);put(get(sp+4),created);m.reg_write(UC_X86_REG_EAX,get(sp+4))
   if created==3:put(aux+0x60,bits(1));put(aux+0x560,1)
  elif a==0x46e3d0:events.append(['sound',get(sp+4),0])
  elif a==0x46e470:events.append(['sound',get(sp+4),1])
  elif a==0x47f0a0:
   handle=get(sp+4);m.reg_write(UC_X86_REG_EAX,0 if not handle else (0 if missing_main else vm) if handle==1 else (0 if handle==2 and missing_aux else aux))
  elif a==0x47f140:put(vm+0x4a0,get(sp+8))
  elif a==0x47f6e0:put(m.reg_read(UC_X86_REG_ECX),0);put(vm+0x1c,get(vm+0x1c)|0x20)
  elif a==0x41b3f0:events.append(['cancel',*point(get(sp+4)),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,get(sp+8)])
  elif a==0x43ab80:lasers.append(['cancel',*point(get(sp+4)),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,get(sp+8)]);assert get(sp+12)==1
  elif a==0x4397b0:events.append(['item',get(sp+4),*point(get(sp+8)),get(sp+16),get(sp+20)]);assert get(sp+24)==0
 for a,n in ((0x47ed10,28),(0x46e3d0,8),(0x46e470,4),(0x47f0a0,4),(0x47f140,8),(0x47f6e0,0),(0x41b3f0,8),(0x43ab80,12),(0x4397b0,24)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 def timer(p,t,rate=1):
  for off,v in ((0,t-1),(4,t),(8,bits(float(t))),(12,0x4d8f58),(16,1)):put(p+off,v)
 def reset():
  nonlocal created
  m.mem_write(end,bytes(0xf0000));events.clear();lasers.clear();created=0
  for p,v in ((0x4db67c,player),(0x4db52c,bomb),(0x4db534,spell),(0x4db544,enemy),(0x4db550,end+0x32000),(bomb,0x4bd7e0),(player+0x10,end),(enemy+0x14,7),(0x4d8f58,bits(1))):put(p,v)
  m.mem_write(player+0x5e0,struct.pack('<fff',12.25,400,3));m.mem_write(bomb+0x624,struct.pack('<fff',12.25,400,3));put(bomb+0x40,1)
 def call(entry):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bomb);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(entry,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
 starts=[]
 for flags,t in itertools.product((0,1,0x23),(0,59,60,120)):
  reset();put(spell+0x7c,flags);put(spell+0x28,t);put(spell+0x80,12345);call(0x415610)
  starts.append(dict(flags=flags,time=t,events=events[:],result=[get(spell+0x7c),get(spell+0x80),get(enemy+0x14),get(player+0x182c4),get(player+0x182d4)]))
 rows=[]
 for n,(t,active,mode,life,missing_main,missing_aux,rate,dialogue) in enumerate(itertools.product((-1,0,59,60,119,120,719,720,721),(0,1,2),(0,1),(1,4),(False,True),(False,True),(.5,1,1.25),(False,True))):
  reset();created=2;aux_age=(0,39,40,41)[n%4];spell_flag=n//4%2
  put(bomb+0x40,active);put(bomb+0x44,1);put(bomb+0x4c,2);put(bomb+0x638,mode);timer(bomb+0x18,t);put(0x4d8f58,bits(rate));put(end+0x32194,int(dialogue));put(spell+0x7c,spell_flag)
  m.mem_write(player+0x5e0,struct.pack('<fff',14.25,300,4));put(player+0x684,life);timer(player+0x68c,9);timer(player+0x182c0,10);put(player+0x182d4,0x28);put(player+0xd6dc,bits(.75));put(vm+0x60,bits(1.75));put(aux+0x60,bits(2.5));put(aux+0x560,aux_age)
  call(0x412200);assert lasers==[e for e in events if e[0]=='cancel']
  result=[get(bomb+0x40),get(bomb+0x638),get(bomb+0x1c),get(bomb+0x20),*point(bomb+0x624),get(player+0x182d4),get(player+0x684),get(player+0x690),get(player+0x182c4),get(player+0xd6dc),get(vm+0x60),get(vm+0x4a0),int(get(bomb+0x4c)!=0 and (get(bomb+0x4c)!=2 or not missing_aux)),int(get(bomb+0x44)!=0)]
  rows.append(dict(args=[t,active,mode,life,int(missing_main),int(missing_aux),aux_age,int(dialogue),spell_flag,rate],events=events[:],result=result))
 (ROOT/'artifacts/th14/sakuya-a-controller-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),start=starts,ticks=rows),indent=2)+'\n',encoding='utf8');print(f'{len(starts)} startup and {len(rows)} Sakuya A common update cases.')
if __name__=='__main__':main()
