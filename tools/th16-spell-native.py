"""Retail417f00/417930 with controlled ANM, HUD, title and audio delivery.
Resource requests and ECL arms are compared separately; no pixel/score-file claim.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE=0x70000000
SPELL,SCORE,REPLAY,ASCII,TEXT,EFFECT,MANAGER,BOSS,PLAYER,SPECIAL,STAGE,NAME,STACK,BP,CODE,OWNER,CONTEXT=tuple(BASE+n for n in (0x1000,0x10000,0x30000,0x31000,0x32000,0x33000,0x34000,0x35000,0x3b000,0x3d000,0x3e000,0x3f000,0x70000,0x78000,0x79000,0x7a000,0x7b000))
VMBASE=BASE+0x40000
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(BASE,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 bindings=[];handles={};timers=[];titles=[];sounds=[];reads=[];captured=[];args=[];closed=[];results=[];awards=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);ecx=m.reg_read(UC_X86_REG_ECX)
  if a==0x406380:
   vm=VMBASE+len(bindings)*0x1000;handle=100+len(bindings);bindings.append([ecx,get(sp+8),get(sp+12)]);handles[handle]=vm;put(get(sp+4),handle);m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x46efa0:m.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0))
  elif a==0x46f510:m.reg_write(UC_X86_REG_EAX,VMBASE+0xf000+(get(sp+4)-11)*0x1000)
  elif a==0x4175d0:timers.extend([2,2])
  elif a==0x417650:timers.extend([3,3])
  elif a==0x46f1c0:closed.append(get(sp+4))
  elif a==0x42bcf0:results.extend([get(sp+8)==0,get(sp+4)])
  elif a==0x43e080:
   amount=struct.unpack('<i',m.mem_read(sp+4,4))[0];awards.append(amount&0xffffffff)
   delta=abs(amount)//10*(-1 if amount<0 else 1);total=(get(0x4a57b0)+delta)&0xffffffff;total=total if total<0x80000000 else total-0x100000000;put(0x4a57b0,min(total,999999999))
  elif a==0x46f0b0:titles.append(get(sp+8))
  elif a==0x45e150:sounds.append(get(sp+4))
  elif a==0x473c90 or a==0x4251d0:
   index=get(sp+4);reads.append(index);m.reg_write(UC_X86_REG_EAX,args[index]&0xffffffff)
  elif a==0x417f00:
   text=bytes(m.mem_read(get(sp+8),64)).split(b'\0')[0];captured.extend([get(sp+4),get(sp+12),get(sp+16),list(text)])
 for a,cleanup in ((0x406380,16),(0x46efa0,4),(0x46f510,8),(0x4175d0,0),(0x417650,0),(0x46f1c0,4),(0x42bcf0,8),(0x43e080,4),(0x46dab0,4),(0x45e150,8),(0x46f0b0,8),(0x47499b,0),(0x473c90,4),(0x4251d0,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def reset():
  m.mem_write(BASE,bytes(0x6f000));bindings.clear();handles.clear();timers.clear();titles.clear();sounds.clear();reads.clear();captured.clear();closed.clear();results.clear();awards.clear()
  for address,value in ((0x4a6db0,SPELL),(0x4a6f0c,SCORE),(0x4a6f08,REPLAY),(0x4a6d98,ASCII),(ASCII+0x19240,ASCII+0x100),(0x4c17f8,TEXT),(0x4a6db8,EFFECT),(EFFECT+12,EFFECT+0x100),(0x4a6dc0,MANAGER),(0x4c0f48,BASE+0x60000),(0x4a6ef8,PLAYER),(0x4a6da8,SPECIAL),(0x4a6da0,STAGE),(0x490eb0,0x4a579c),(0x4a579c,bits(1)),(MANAGER+0x48,7),(MANAGER+0x180,MANAGER+0x200),(MANAGER+0x200,BOSS),(BOSS+0x5740,7)):
   put(address,value)
  for slot in range(7):put(MANAGER+0x164+slot*4,BASE+0x62000+slot*0x100)
  m.mem_write(BOSS+0x1250,struct.pack('<fff',12.25,-14.5,4.75));m.mem_write(NAME,b'Native spell\0');m.reg_write(UC_X86_REG_MXCSR,0x1f80)
 def call(address,arguments=()):
  put(STACK,BASE)
  for n,v in enumerate(arguments):put(STACK+4+n*4,v)
  m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SPELL)
  try:m.emu_start(address,BASE,count=100000)
  except Exception:print('failed',hex(m.reg_read(UC_X86_REG_EIP)),bindings);raise
  assert m.reg_read(UC_X86_REG_EIP)==BASE
 def state():return [get(SPELL+0x78),get(SPELL+0x74),get(SPELL+0x7c),get(SPELL+0x80),get(SPELL+0x84),get(SPELL+0x8c),*words(SPELL+0x20,3),get(SPELL+0x30),*words(SPELL+0xa8,3)]
 begins=[]
 for selection,sf,runflags,special in itertools.product(range(4),(0,1,8,0x10,0x23,0x40,0x80,0x1ff),(0,0x10,0x20,0x30,0xff),(0,1,2)):
  reset();n=len(begins);stage=(1,2,5,6,7,333,400,-1,-2147483648)[n%9];difficulty=n%5;id=(0,20,106,118)[n%4];duration=(2400,1800,600,300,0)[n%5];replay=n%4==1;mode=n%2
  for a,v in ((0x4a5790,stage),(0x4a5798,50),(0x4a57b4,difficulty),(0x4a57a4,selection),(0x4a57a8,0),(0x4a5bec,runflags),(REPLAY+12,int(replay)),(SPECIAL+0x30,special),(SPELL+0x78,sf),(SPELL+0x30,mode),(SPELL+0x2c,0)) :put(a,v)
  put(0x4a6f18,0x4a22d0+0xd4)
  seeds=[(-1,0,99998,99999,100000)[(n+j)%5] for j in range(8)]
  for t,base in enumerate((SCORE+0x8d8+selection*0x5318+id*0x9c,SCORE+0x15538+id*0x9c)):
   for j in range(4):put(base+0x80+j*4,seeds[t*4+j])
  call(0x417f00,(id,NAME,duration,0))
  records=[get(base+0x80+j*4) for base in (SCORE+0x8d8+selection*0x5318+id*0x9c,SCORE+0x15538+id*0x9c) for j in range(4)]
  begins.append(dict(input=[id,duration,selection,stage,difficulty,sf,runflags,special,int(replay),mode,*seeds],state=state(),records=records,timers=timers[:]))
 factories=[]
 for stage,section,variant in itertools.product(range(1,8),(-1,0,42,43,100),(0,1)):
  reset();put(0x4a5790,stage);put(0x4a5798,section);put(0x4a6f18,0x4a22d0+stage*0xd4);call(0x417f00,(20,NAME,2400,variant))
  created=[]
  for n,(r,script,layer) in enumerate(bindings):
   file=2 if r==ASCII+0x100 else 0 if r==TEXT else 8 if r==EFFECT+0x100 else 10+(r-(BASE+0x62000))//0x100-2
   created.append([file,script,0,*words(VMBASE+n*0x1000+0x5e0,3),get(VMBASE+n*0x1000+0x534)])
  assert all(layer==0xffffffff for _,_,layer in bindings)
  factories.append(dict(input=[stage,section,variant,3],created=created,sounds=sounds[:],childTimeouts=[get(VMBASE+0xf000+0x4a8),get(VMBASE+0x10000+0x4a8),get(SPELL+0x78)]))
 updates=[]
 for sf,elapsed,rate,y in itertools.product((0,1,3,9,0x21,0x101,0x105,0x125,0x201,0x301,0xff),(0,59,60,119,120,299,300,301),(.5,.99,1.,1.01,1.25),(95.,96.,128.,129.,319.,320.,352.,353.)):
  reset();n=len(updates);bonus=(5000000,4999977,-17,2147483647,-2147483648)[n%5];initial=(5000000,999999999,-77,2147483647,-2147483648)[n%5];duration=(2400,1800,301,600,99999)[n%5];special=n%3
  for a,v in ((SPELL+0x78,sf),(SPELL+0x7c,bonus),(SPELL+0x80,initial),(SPELL+0x84,duration),(SPELL+0x8c,123),(SPELL+0x20,elapsed-1),(SPELL+0x24,elapsed),(SPELL+0x28,bits(elapsed+.25)),(SPELL+0x2c,0),(SPELL+0x30,1),(0x4a579c,bits(rate)),(SPECIAL+0x30,special),(PLAYER+0x614,bits(y)),(STAGE+0x66c4,0x81),(SPELL+0x1c,20)):put(a,v)
  for k in range(3):put(SPELL+0x10+k*4,11+k)
  m.mem_write(SPELL+0xa8,struct.pack('<fff',12.25,-14.5,4.75));m.mem_write(BOSS+0x1250,struct.pack('<fff',-33.125,144.25,-9.5));handles[20]=VMBASE;call(0x417930)
  updates.append(dict(input=[sf,elapsed,bits(rate),bits(y),bonus,initial,duration,special],state=state(),background=get(STAGE+0x66c4),titles=titles[:],circle=words(VMBASE+0x5e0,3)))
 ends=[]
 for sf,runflags,replay,score in itertools.product((0,1,2,3,0x21,0x23,0x81,0x83,0xff),(0,0x10,0x20,0x30),(0,1),(0,500000,999999900,999999999)):
  reset();n=len(ends);selection=n%4;bonus=(5000000,177,-10,2147483647,-2147483648)[n%5];seeds=[(-1,0,99998,99999,100000)[(n+j)%5] for j in range(8)]
  for a,v in ((SPELL+0x78,sf),(SPELL+0x74,2),(SPELL+0x7c,bonus),(SPELL+0xc,0xc),(SPELL+0x1c,0x1c),(0x4a57b0,score),(0x4a57a4,selection),(0x4a57a8,0),(0x4a5bec,runflags),(REPLAY+12,replay)):put(a,v)
  for k in range(3):put(SPELL+0x10+k*4,11+k)
  for t,base in enumerate((SCORE+0x8d8+selection*0x5318+2*0x9c,SCORE+0x15538+2*0x9c)):
   for j in range(4):put(base+0x80+j*4,seeds[t*4+j])
  call(0x4182f0);records=[get(base+0x80+j*4) for base in (SCORE+0x8d8+selection*0x5318+2*0x9c,SCORE+0x15538+2*0x9c) for j in range(4)]
  ends.append(dict(input=[sf,runflags,replay,score,bonus,selection,*seeds],flags=get(SPELL+0x78),score=get(0x4a57b0),records=records,background=get(STAGE+0x66c4),timers=timers[:],titles=titles[:],closed=closed[:],results=results[:],sounds=sounds[:],awards=awards[:]))
 # Own ECL arms, with complete timer initialization and controlled begin sink.
 m.mem_write(0x417f00,b'\xc2\x10\x00');m.ctl_remove_cache(0x417f00,0x417f08);m.hook_add(UC_HOOK_CODE,boundary,begin=0x417f00,end=0x417f00);commands=[]
 for op,difficulty,text,health,mode in itertools.product((522,537,538,539),range(5),(b'',b'Native spell',b'\x97\xea\x96\xb2',b'x'*63,b'ab\0ignored'),(0,177,2147483647),(0,1)):
  reset();n=len(commands);args[:]=[20,2400,1];size=(len(text)+4)&~3;plain=(text+b'\0').ljust(size,b'\0');key,step=0x77,7;encrypted=[]
  for b in plain:encrypted.append(b^key);key=(key+step)&255;step=(step+16)&255
  raw=struct.pack('<iHHHBBI',0,op,32+size,0,255,4,0)+struct.pack('<iiiI',*args,size)+bytes(encrypted);m.mem_write(CODE,raw)
  flags=0xfffffffe if n%2 else 0x20
  for a,v in ((BOSS+0x44b8,OWNER),(OWNER+12,CONTEXT),(BOSS+0x3f74,health),(BOSS+0x3f8c,flags),(BOSS+0x2cc,mode),(BOSS+0x2c8,0),(0x4a57b4,difficulty),(BP-0x42c,BOSS),(BP-0x40c,OWNER),(BP-0x418,CODE)):put(a,v)
  m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EBP,BP);m.reg_write(UC_X86_REG_EDI,BOSS);m.reg_write(UC_X86_REG_EDX,OWNER);m.reg_write(UC_X86_REG_ESI,CODE);m.emu_start(0x421757,0x422a9b,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  commands.append(dict(op=op,difficulty=difficulty,health=health,flags=flags,timerMode=mode,raw=list(raw),call=captured[:],reads=reads[:],state=[get(BOSS+0x3f8c),get(BOSS+0x3f80),*words(BOSS+0x2bc,3),get(BOSS+0x2cc)]))
 flag_commands=[]
 for op,flags,value in itertools.product((542,543,567,568),(0,1,0x100,0x1ff,0xa5a5a5a5,0xffffffff),(-2147483648,-3,-2,-1,0,1,2,3,2147483647)):
  reset();args[:]=[value];put(SPELL+0x78,flags);put(SPELL+0x1c,0x1c);put(BOSS+0x3f8c,flags);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EDI,BOSS)
  va=img.u32(0x422ab8+img.read(0x422d70+op-300,1)[0]*4);m.emu_start(va,0x422a9b,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  flag_commands.append(dict(op=op,flags=flags,value=value,result=get(BOSS+0x3f8c) if op==568 else get(SPELL+0x78),closed=closed[:]))
 out=ROOT/'artifacts/th16/spell-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),begins=begins,factories=factories,updates=updates,ends=ends,commands=commands,flagCommands=flag_commands),separators=(',',':'))+'\n',encoding='utf8');print(len(begins),'begin /',len(factories),'visual requests /',len(updates),'update /',len(ends),'end /',len(commands),'ECL /',len(flag_commands),'flag commands')
if __name__=='__main__':main()
