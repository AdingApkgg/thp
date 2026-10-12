"""Retail reward 41ae00, pool reset 41d8c0, full item tick 438550 and
draw 439640. ANM bind/tick/draw and zero-handle cleanup are delivery boundaries.
RNG, polar math, timers, free-list operations and pickup counters execute natively.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE=0x70000000
ITEMS,BULLETS,PLAYER,GAME,BOMB,HEADER,POS,STACK=tuple(BASE+n for n in (0,0xe00000,0x1800000,0x1820000,0x1830000,0x1840000,0x1850000,0x18ff000))
STOP=BASE+0x18fe000
CAPACITY=4696;STRIDE=0xc18
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(BASE,0x1900000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 def slot(p):return (p-ITEMS-0x14)//STRIDE if p else -1
 m.mem_write(0x4db508,struct.pack('<HHI',54321,0,123))
 events=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);ecx=m.reg_read(UC_X86_REG_ECX)
  if a==0x48f980:m.mem_write(get(sp+4),bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x40af00:
   vm,script=get(sp+4),get(sp+8);events.append([0,script]);m.mem_write(vm,bytes(0x5cc));put(vm+0x18,1);m.mem_write(vm+0x4aa,struct.pack('<h',script))
  elif a==0x46fe50:events.append([1,slot(ecx-0x10)])
  elif a==0x46e470:events.append([2,get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  elif a==0x47f140:assert get(sp+4)==0,'nonzero item auxiliary handle is outside this proof'
  elif a==0x47ed10:
   p=get(sp+12);events.append([4,get(sp+8),get(p),get(p+4),get(p+8)]);m.reg_write(UC_X86_REG_EAX,0)
  elif a==0x46e3d0:events.append([5,get(sp+4)])
  elif a==0x478f60:
   vm=get(sp+4);events.append([3,slot(vm-0x10),get(vm+0x3c),get(vm+0x40),get(vm+0x44)])
 for a,cleanup in ((0x48f980,0),(0x40af00,8),(0x46fe50,0),(0x46e470,4),(0x47f140,8),(0x478f60,4),(0x47ed10,28),(0x46e3d0,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def call(a,ecx,args=(),edx=0):
  put(STACK,STOP)
  for n,v in enumerate(args):put(STACK+4+n*4,v)
  m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_EDX,edx)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(a,STOP,count=500000);assert m.reg_read(UC_X86_REG_EIP)==STOP,hex(m.reg_read(UC_X86_REG_EIP))
 def reset(seed=0,count=0,load=0,generation=0,full=False):
  call(0x41d8c0,ITEMS);events.clear()
  put(0x4db660,ITEMS);put(0x4db530,BULLETS);put(0x4db67c,PLAYER);put(0x4db550,GAME);put(0x4db52c,BOMB)
  put(0x4db53c,GAME+0x800);put(GAME+0x810,0);put(0x4f5894,0)
  put(BULLETS+0x9bf6c8,19);put(BULLETS+0x9bf6cc,0x60000000)
  put(ITEMS+0xddd878,count);put(ITEMS+0xddd87c,load);put(ITEMS+0xddd880,generation)
  for a in (ITEMS+0xddd874,0x4f5830,0x4f584c,0x4f5840):put(a,0)
  m.mem_write(0x4db510,struct.pack('<HHI',seed,0,0))
  if full:put(ITEMS+0xddd868,0)
  return ITEMS+0x14+(CAPACITY-1)*STRIDE
 def values(p):
  offsets=(0xbac,0xbb0,0xbb4,0xbb8,0xbbc,0xbc0,0xbc4,0xbc8,0xbcc,0xbd0,0xbd8,0xbf0,0xbf4,0xbf8,0xbfc,0xc00,0xc04,0xba8)
  return [*[get(p+o) for o in offsets],get(ITEMS+0xddd878),get(ITEMS+0xddd87c),slot(get(ITEMS+0xddd868))&0xffffffff,get(BULLETS+0x9bf6c8),int.from_bytes(m.mem_read(0x4db510,2),'little'),get(0x4db514),get(ITEMS+0xddd874),get(0x4f5830),get(0x4f584c),get(0x4f5840),slot(get(ITEMS+0xddd858))&0xffffffff]
 # Execute the actual constructor list loop and record both entire free chains.
 reset();chains=[]
 for off in (0xddd858,0xddd868):
  p=get(ITEMS+off);chain=[]
  while p:chain.append(slot(p));p=get(p+4)
  chains.append(chain)
 rows=[]
 for seed in (0,1,12345,65535):
  for load in (0,255,256,511,512,1023,1024):
   for count in (0,1,3,2147483646,2147483647,4294967294,4294967295):
    for full in (False,True):
     p=reset(seed,count,load,0x12345678,full);floats(POS,17.25,61.5,2)
     call(0x41ae00,POS,edx=1)
     rows.append(dict(seed=seed,count=count,load=load,generation=0x12345678,full=full,position=[17.25,61.5,2],result=values(p)))
 # Strict on-screen bounds including f32-rounded edges; no RNG when outside.
 for position in ((-224,0,0),(-223.99998,0,0),(224,0,0),(223.99998,0,0),(0,-32,0),(0,-31.999998,0),(0,480,0),(0,479.99997,0),(0,0,0)):
  p=reset(12345);floats(POS,*position);call(0x41ae00,POS,edx=1)
  rows.append(dict(seed=12345,count=0,load=0,generation=0,full=False,position=position,result=values(p)))
 for raw in ((0x7fc00000,bits(100),0),(bits(0),0x7fc00000,0),(0x7f800000,bits(100),0),(0xff800000,bits(100),0),(bits(0),0x7f800000,0),(bits(0),0xff800000,0)):
  p=reset(12345);m.mem_write(POS,struct.pack('<III',*raw));call(0x41ae00,POS,edx=1)
  rows.append(dict(seed=12345,count=0,load=0,generation=0,full=False,positionBits=raw,result=values(p)))
 # Stateful pool exhaustion executes 4,098 rewards and validates slot ordering.
 reset(12345);floats(POS,0,100,0);allocations=[]
 for n in range(4098):
  before=get(ITEMS+0xddd868);call(0x41ae00,POS,edx=1);allocations.append(slot(before))
 exhaustion=dict(slots=allocations,count=get(ITEMS+0xddd878),rewardCount=get(BULLETS+0x9bf6c8),rngSeed=int.from_bytes(m.mem_read(0x4db510,2),'little'),rngCalls=get(0x4db514))
 ordinary=[]
 for kind in (*range(1,9),12):
  for rate in (.5,1,1.25):
   for position in ((-224,100,2),(-192,100,2),(0,100,2),(192,100,2),(224,100,2)):
    for angle in (-1.5707963705062866,0,.75):
     reset();p=ITEMS+0x14+599*STRIDE;floats(POS,*position);floats(0x4d8f58,rate)
     call(0x4397b0,ITEMS,(kind,POS,0,bits(angle),bits(2.2),0))
     ordinary.append(dict(kind=kind,rate=rate,position=position,angle=angle,result=values(p),events=events[:],counter=get(0x4f5894)))
 special=[]
 for counter in (-2147483648,-6,-5,-2,-1,0,1,3,4,5,99,2147483647):
  for full in (False,True):
   reset();put(0x4f5894,counter);p=ITEMS+0x14+599*STRIDE
   if full:put(ITEMS+0xddd858,0)
   floats(POS,12.25,99.5,2);call(0x4397b0,ITEMS,(12,POS,0,bits(-1.5707963705062866),bits(2.2),0))
   special.append(dict(counter=counter,full=full,result=values(p),nextCounter=get(0x4f5894),events=events[:]))
 ticks=[]
 for state in (1,2,3,5):
  for rate in (.5,.99,1,1.01,1.25):
   for case in range(12):
    p=reset();put(ITEMS+0xddd868,get(p+4));put(get(p+4)+8,ITEMS+0xddd864);put(p+4,0);put(p+8,0)
    m.mem_write(PLAYER,bytes(0x20000));m.mem_write(GAME,bytes(0x1000));m.mem_write(BOMB,bytes(0x1000))
    player_state=(1,2,4)[case%3];character=case%3;collect=case>=9
    floats(PLAYER+0x5e0,0,100,0);put(PLAYER+0x684,player_state);put(PLAYER+0x688,HEADER);floats(HEADER+8,8)
    for offset in (0x1835c,0x18374,0x1838c):floats(PLAYER+offset,*((-1000,-1000,0,1000,1000) if collect else (1,1,0,-1,-1)))
    put(0x4f5828,character);put(0x4f5884,0);put(0x4d6a90,0);put(0x4f5830,999999998 if collect else 0);put(0x4f584c,999950 if collect else 0);put(0x4f5854,1000000);put(0x4f5840,7);floats(0x4d8f58,rate)
    position=(0,100,0) if collect else ((0,100,0) if case%4==0 else (17.25,61.5,2) if case%4==1 else (-30,472.1,0) if case%4==2 else (10,148,0))
    velocity=(.25,0,0) if case%4==0 else (1.25,-.75,.5) if case%4==1 else (0,-2.2,0) if case%4==2 else (.25,-.01,0)
    floats(p+0xbac,*position);floats(p+0xbb8,*velocity);floats(p+0xbfc,8)
    put(p+0xbf0,state);put(p+0xbf4,10);put(p+0xbf8,10);put(p+0xc00,case%4-1)
    put(p+0xbc8,19);put(p+0xbcc,20);floats(p+0xbd0,20.5);put(p+0xbd4,0x4d8f58);put(p+0xbd8,1);put(p+0x28,1)
    call(0x438550,ITEMS);ticks.append(dict(state=state,rate=rate,case=case,position=position,velocity=velocity,playerState=player_state,character=character,collect=collect,result=values(p),events=events[:]))
 attraction=[]
 for kind in (1,2,4,6):
  for state in (1,2,3,4):
   for rate in (.5,1,1.25):
    for variant in range(12):
     reset();p=ITEMS+0x14+599*STRIDE;events.clear();m.mem_write(PLAYER,bytes(0x20000));m.mem_write(GAME,bytes(0x1000));m.mem_write(BOMB,bytes(0x1000))
     player_state=2 if variant in (6,11) else 4 if variant==7 else 1;character=variant%3;y=(100,128,148,400,400,400,100,100,400,400,400,400)[variant];delay=1 if variant==6 else 2 if variant==7 else 0
     floats(PLAYER+0x5e0,0,y,0);put(PLAYER+0x684,player_state);put(PLAYER+0x688,HEADER);floats(HEADER+8,8)
     for offset in (0x1835c,0x18374,0x1838c):floats(PLAYER+offset,1,1,0,-1,-1)
     if variant in (8,10,11):floats(PLAYER+0x1838c,-1000,-1000,0,1000,1000)
     if variant==9:floats(PLAYER+0x18374,-1000,-1000,0,1000,1000)
     put(0x4d6a90,8 if variant in (9,10) else 0)
     put(0x4f5828,character);put(0x4f5884,8);put(0x4f5880,0);put(0x4f5878,0);put(GAME+0x194,int(variant==5));put(BOMB+0x40,int(variant==4));put(BOMB+0x1c,59);floats(0x4d8f58,rate)
     floats(p+0xbac,17.25,61.5,2);floats(p+0xbb8,1.25,-.75,.5);floats(p+0xbfc,8)
     put(p+0xbf0,state);put(p+0xbf4,kind);put(p+0xbf8,0);put(p+0xc00,delay)
     put(p+0xbc8,19);put(p+0xbcc,20);floats(p+0xbd0,20.5);put(p+0xbd4,0x4d8f58);put(p+0xbd8,1)
     call(0x438550,ITEMS)
     attraction.append(dict(input=[kind,state,rate,variant],result=values(p),timer=get(0x4f5884),events=events[:]))
 draws=[]
 for state in (0,2,5):
  for y in (-8.0001,-8,-1,100):
   for delay in (-1,0,1):
    p=reset();put(p+0xbf0,state);put(p+0xc00,delay);put(p+0xbf8,10);put(p+0x28,1);floats(p+0xbac,17.25,y,2)
    call(0x439640,ITEMS);draws.append(dict(state=state,y=y,delay=delay,display=get(p+0xbf8),events=events[:]))
 assert int.from_bytes(m.mem_read(0x4db508,2),'little')==54321 and get(0x4db50c)==123, 'item path consumed the ANM/shake stream'
 out=ROOT/'artifacts/th14/item-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),chains=chains,rewards=rows,exhaustion=exhaustion,ordinary=ordinary,special=special,ticks=ticks,attraction=attraction,draws=draws),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} rewards, {len(ticks)} ticks, {len(draws)} draw requests; full 4,096-slot depletion.')
if __name__=='__main__':main()
