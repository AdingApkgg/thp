"""Retail spell begin/update/end. ANM allocation/binding, text/audio/result delivery
are controlled boundaries; spell bodies, record writes and timers execute natively.
This proves state/numerics, not resource scripts, fonts, audio mixing or score.dat.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE=0x70000000
SPELL,GAME,SPECIAL,MANAGER,BOSS,REPLAY,SCORE,ASCII,TEXT,BULLETS,PLAYER,STACK,NAME=tuple(BASE+n for n in (0x1000,0x2000,0x8000,0x9000,0xa000,0xc000,0x10000,0x40000,0x5a000,0x5b000,0x5c000,0x8f000,0x8e000))
VMBASE=BASE+0x60000
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(BASE,0x90000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 handles={};bindings=[];sounds=[];titles=[];timers=[];results=[];closed=[];allocated=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);ecx=m.reg_read(UC_X86_REG_ECX)
  if a==0x47fcb0:
   vm=VMBASE+len(allocated)*0x2000;allocated.append(vm);m.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:
   vm,script=get(sp+4),get(sp+8);bindings.append([ecx,script]);put(vm+0x30,ecx);m.mem_write(vm+0x4aa,struct.pack('<H',script));put(vm+0x580,vm)
   if ecx==BULLETS and script==13:
    for offset,child,number,nxt in ((0x580,vm,13,vm+0x680),(0x680,vm+0x700,11,vm+0x690),(0x690,vm+0x780,12,0)):
     put(vm+offset,child);put(vm+offset+4,nxt);m.mem_write(child+0x4aa,struct.pack('<H',number))
  elif a==0x47e890:
   out,vm=get(sp+4),get(sp+8);handle=100+len(handles);handles[handle]=vm;put(out,handle);m.reg_write(UC_X86_REG_EAX,out)
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0))
  elif a==0x46fe50:
   if ecx in (GAME+0x600,GAME+0xd00):timers.append(get(ecx+0x4a0))
  elif a==0x47f140:titles.append([get(sp+4),get(sp+8)])
  elif a==0x47f6e0:closed.append(ecx-SPELL);put(ecx,0)
  elif a==0x46e3d0:sounds.append(get(sp+4))
  elif a==0x434430:results.append([get(sp+8)==0,get(sp+4)])
 for a,cleanup in ((0x47fcb0,0),(0x40af00,8),(0x47e890,8),(0x47f0a0,4),(0x46fe50,0),(0x47f140,8),(0x47f6e0,0),(0x46e3d0,8),(0x434430,8),(0x47dc40,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def reset():
  m.mem_write(BASE,bytes(0x8e000));handles.clear();bindings.clear();sounds.clear();titles.clear();timers.clear();results.clear();closed.clear();allocated.clear()
  for addr,value in ((0x4db534,SPELL),(0x4db550,GAME),(0x4db52c,SPECIAL),(0x4db544,MANAGER),(0x4db688,REPLAY),(0x4db68c,SCORE),(0x4db520,ASCII),(0x4d967c,TEXT),(0x4db53c,BULLETS+0x800),(0x4db528,GAME+0x4000),(0x4db67c,PLAYER),(0x4f56cc,MANAGER+0x800),(0x4d8f58,bits(1)),(GAME+0x98,GAME+0x600),(GAME+0x9c,GAME+0xd00),(ASCII+0x191e4,ASCII+0x18000),(BULLETS+0x810,BULLETS),(MANAGER+0x5c,BOSS)):
   put(addr,value)
  for slot in range(8):put(MANAGER+0xa0+slot*4,BASE+0x5d000+slot*0x180)
  m.mem_write(0x4f5815,b'\0');m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
 def call(addr,args=()):
  put(STACK,BASE)
  for n,v in enumerate(args):put(STACK+4+n*4,v)
  m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SPELL)
  try:m.emu_start(addr,BASE,count=100000)
  except Exception:
   print('native failure',hex(m.reg_read(UC_X86_REG_EIP)),hex(m.reg_read(UC_X86_REG_EAX)),hex(m.reg_read(UC_X86_REG_ECX)),bindings);raise
  assert m.reg_read(UC_X86_REG_EIP)==BASE
 def state():return [get(SPELL+0x7c),get(SPELL+0x78),get(SPELL+0x80),get(SPELL+0x84),get(SPELL+0x88),get(SPELL+0x90),*words(SPELL+0x24,3),get(SPELL+0x34),*words(SPELL+0xac,3)]
 begins=[]
 for selection in range(6):
  for sf in (0,1,8,0x10,0x23,0x40,0x80,0x1ff):
   for runflags in (0,0x10,0x20,0x30,0xff):
    for special in (0,1,2):
     reset();n=len(begins);stage=(1,2,5,6,7,333,400,-1,-2147483648)[n%9];difficulty=(0,1,2,3,4,-1,2147483647)[n%7];id=(0,2,52,63,129)[n%5];duration=(2400,1800,600,300,0)[n%5];replay=(n%4==1)
     put(0x4f58a4,stage);put(0x4f58ac,0);put(0x4f5834,difficulty);put(0x4f5828,selection//2);put(0x4f582c,selection%2);put(0x4f58b8,runflags);put(REPLAY+0x10,int(replay));put(SPECIAL+0x40,special)
     # Bonus stage is varied independently of the controlled stage-one asset boundary.
     put(0x4db69c,0x4d5988+0xcc)
     put(SPELL+0x7c,sf);put(SPELL+0x34,n%2);m.mem_write(NAME,b'Native spell\0');m.mem_write(BOSS+0x1234,struct.pack('<fff',12.25,-14.5,4.75))
     seeds=[(-1,0,99998,99999,100000)[(n+j)%5] for j in range(8)]
     for t,base in enumerate((SCORE+0x980+selection*0x5298+id*0x9c,SCORE+0x1f910+id*0x9c)):
      for j in range(4):put(base+0x80+j*4,seeds[t*4+j])
     call(0x41cb70,(id,NAME,duration,99,0,1))
     records=[get(base+0x80+j*4) for base in (SCORE+0x980+selection*0x5298+id*0x9c,SCORE+0x1f910+id*0x9c) for j in range(4)]
     begins.append(dict(input=[id,duration,selection,stage,difficulty,sf,runflags,special,int(replay),n%2,*seeds],state=state(),records=records,timers=timers[:],sounds=sounds[:],bindings=[[('ascii' if a==ASCII+0x18000 else 'text' if a==TEXT else 'effect' if a==BULLETS else str((a-(BASE+0x5d000))//0x180)),b] for a,b in bindings]))
 factories=[]
 for stage in range(1,8):
  for section in (-1,0,5,6,24):
   for id in (0,2,52,63,64):
    descriptor=0x4d5988+stage*0xcc
    # Invalid cross-stage special ids can index resource -1 in retail.
    if 52<=id<=63 and img.u32(descriptor+0x60)==0xffffffff:continue
    reset();put(0x4f58a4,stage);put(0x4f58ac,section);put(0x4f5828,0);put(0x4f582c,0);put(0x4f5834,1);put(0x4f58b8,0);put(0x4db69c,descriptor);m.mem_write(NAME,b'Native spell\0');m.mem_write(BOSS+0x1234,struct.pack('<fff',12.25,-14.5,4.75))
    call(0x41cb70,(id,NAME,2400,99,0,1))
    created=[]
    for (resource,script),vm in zip(bindings,allocated):
     file=2 if resource==ASCII+0x18000 else 0 if resource==TEXT else 8 if resource==BULLETS else 10+(resource-(BASE+0x5d000))//0x180-2
     created.append([file,script,get(vm+0x1c)&0x200,*words(vm+0x59c,3),get(vm+0x50)])
    circle=handles[get(SPELL+0x20)]
    factories.append(dict(input=[stage,section,id],created=created,sounds=sounds[:],childTimeouts=[get(circle+0x700+0x4b4),get(circle+0x780+0x4b4)]))
 updates=[]
 for sf in (0,1,3,9,0x21,0x101,0x105,0x125,0xff):
  for elapsed in (0,59,60,118,119,120,299,300,301,2399):
   for rate in (.5,.99,1,1.01,1.25):
    for y in (95,96,128,129,319,320,352,353):
     reset();n=len(updates);bonus=(5000000,4999977,-17,2147483647,-2147483648)[n%5];initial=(5000000,999999999,-77,2147483647,-2147483648)[n%5];duration=(2400,1800,301,600,99999)[n%5];special=n%3
     put(SPELL+0x7c,sf);put(SPELL+0x80,bonus);put(SPELL+0x84,initial);put(SPELL+0x88,duration);put(SPELL+0x90,123);put(SPELL+0x24,elapsed-1);put(SPELL+0x28,elapsed);put(SPELL+0x2c,bits(elapsed+.25));put(SPELL+0x30,0x4d8f58);put(SPELL+0x34,1);put(0x4d8f58,bits(rate));put(SPECIAL+0x40,special);put(PLAYER+0x5e4,bits(y));put(GAME+0x4000+0x4224,0x81)
     for i in range(3):put(SPELL+0x14+4*i,11+i)
     circle=(12.25,-14.5,4.75);boss=(-33.125,144.25,-9.5);m.mem_write(SPELL+0xac,struct.pack('<fff',*circle));m.mem_write(BOSS+0x1234,struct.pack('<fff',*boss));handles[20]=VMBASE;put(SPELL+0x20,20)
     call(0x41c5b0)
     updates.append(dict(input=[sf,elapsed,bits(rate),bits(y),bonus,initial,duration,special],state=state(),background=get(GAME+0x4000+0x4224),titles=[label for _,label in titles],circle=words(VMBASE+0x59c,3)))
 ends=[]
 for sf in (0,1,2,3,0x21,0x23,0x81,0x83,0xff):
  for runflags in (0,0x10,0x20,0x30):
   for replay in (0,1):
    for score in (0,500000,999999900,999999999):
     reset();n=len(ends);id=2;selection=n%6;bonus=(5000000,177,-10,2147483647,-2147483648)[n%5];seeds=[(-1,0,99998,99999,100000)[(n+j)%5] for j in range(8)]
     put(SPELL+0x7c,sf);put(SPELL+0x78,id);put(SPELL+0x80,bonus);put(SPELL+0x10,10);put(SPELL+0x20,20)
     for i in range(3):put(SPELL+0x14+i*4,11+i)
     put(0x4f5830,score);put(0x4f5828,selection//2);put(0x4f582c,selection%2);put(0x4f58b8,runflags);put(REPLAY+0x10,replay)
     for t,base in enumerate((SCORE+0x980+selection*0x5298+id*0x9c,SCORE+0x1f910+id*0x9c)):
      for j in range(4):put(base+0x80+j*4,seeds[t*4+j])
     health_flags=0xfffffffe if n%2 else 0x21
     put(BOSS+0x3f8c,health_flags);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EDI,BOSS)
     m.emu_start(0x4289ea,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
     records=[get(base+0x80+j*4) for base in (SCORE+0x980+selection*0x5298+id*0x9c,SCORE+0x1f910+id*0x9c) for j in range(4)]
     ends.append(dict(input=[sf,runflags,replay,score,bonus,selection,*seeds],healthFlags=health_flags,endHealthFlags=get(BOSS+0x3f8c),flags=get(SPELL+0x7c),score=get(0x4f5830),records=records,background=get(GAME+0x4000+0x4224),timers=timers[:],titles=[label for _,label in titles],closed=closed[:],results=results[:],sounds=sounds[:]))
 commands=[];read_indices=[];captured=[];args=[]
 def ecl_boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x483f30:
   index=get(sp+4);read_indices.append(index);m.reg_write(UC_X86_REG_EAX,args[index]&0xffffffff)
  else:
   name=get(sp+8);text=bytes(m.mem_read(name,64)).split(b'\0')[0]
   captured.extend([get(sp+4),get(sp+12),get(sp+16),get(sp+20),get(sp+24)]);captured.append(list(text))
 for a,cleanup in ((0x483f30,4),(0x41cb70,24)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup));m.ctl_remove_cache(a,a+8);m.hook_add(UC_HOOK_CODE,ecl_boundary,begin=a,end=a)
 instruction,owner,context=BASE+0x7d000,BASE+0x7e000,BASE+0x7f000
 for op in (522,537,538,539):
  for difficulty in range(5):
   for text in (b'',b'Native spell',b'\x97\xea\x96\xb2',b'x'*63,b'ab\0ignored'):
    for health in (0,177,2147483647):
     for timer_mode in (0,1):
      reset();read_indices.clear();captured.clear();n=len(commands);args[:]=[8,2400,-177];size=(len(text)+4)&~3;plain=(text+b'\0').ljust(size,b'\0');encrypted=[];key,step=0x77,7
      for b in plain:encrypted.append(b^key);key=(key+step)&255;step=(step+16)&255
      raw=struct.pack('<iHHHBBI',0,op,32+size,0,255,4,0)+struct.pack('<iiiI',*args,size)+bytes(encrypted);m.mem_write(instruction,raw)
      put(BOSS+0x40ec,owner);put(owner+4,context);put(SPELL+0x34,1);put(BOSS+0x3f74,health);put(BOSS+0x3f8c,0xfffffffe if n%2 else 0x20);put(BOSS+0x2cc,timer_mode);put(BOSS+0x2c8,0x4d8f58 if timer_mode else 0);put(0x4f5834,difficulty)
      for offset,value in ((0x1c,BOSS),(0x10,owner),(0x28,instruction)):put(STACK+offset,value)
      m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EDI,BOSS);m.reg_write(UC_X86_REG_EDX,owner);m.reg_write(UC_X86_REG_ESI,instruction);m.emu_start(0x4288b3,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
      commands.append(dict(op=op,difficulty=difficulty,health=health,flags=0xfffffffe if n%2 else 0x20,timerMode=timer_mode,raw=list(raw),call=captured[:],reads=read_indices[:],state=[get(BOSS+0x3f8c),get(BOSS+0x3f80),*words(BOSS+0x2bc,3),get(BOSS+0x2cc)]))
 orientations=[]
 for flags in (0,1,0x100,0x1ff,0xa5a5a5a5,0xffffffff):
  for value in (-2147483648,-3,-2,-1,0,1,2,3,2147483647):
   reset();put(SPELL+0x7c,flags);call(0x421c90,(value,));orientations.append(dict(flags=flags,value=value,result=get(SPELL+0x7c)))
 invalidations=[]
 for flags in (0,1,7,8,9,255,256,0xffffffff,0x80000000):
  reset();put(SPELL+0x7c,flags);m.reg_write(UC_X86_REG_ESP,STACK);m.emu_start(0x4289fb,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28;invalidations.append(dict(flags=flags,result=get(SPELL+0x7c)))
 out=ROOT/'artifacts/th14/spell-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),begins=begins,factories=factories,updates=updates,ends=ends,commands=commands,orientations=orientations,invalidations=invalidations))+'\n',encoding='utf8');print(f'{len(begins)} begin, {len(factories)} visual factories, {len(updates)} update, {len(ends)} end, {len(commands)} ECL cases')
if __name__=='__main__':main()
