"""Observe retail factory kind 3, its actual inert virtuals and registry lifetime.

Only allocation, free and memset are controlled host-library boundaries.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE=0x70000000
MANAGER,REQUEST,OBJECT,STACK=BASE+0x1000,BASE+0x4000,BASE+0x10000,BASE+0x3f000
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(BASE,0x40000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,4*n)))
 freed=[];allocated=[]
 def boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x48f980:
   p,value,n=(get(sp+i) for i in (4,8,12));m.mem_write(p,bytes([value&255])*n);m.reg_write(UC_X86_REG_EAX,p)
  elif address==0x4854af:
   assert get(sp+4)==0x1ee4;allocated.append(get(sp+4));m.reg_write(UC_X86_REG_EAX,OBJECT)
  else:freed.append(get(sp+4))
 for a in (0x48f980,0x4854af,0x4854fe):
  m.mem_write(a,b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def call(address,ecx=0,args=()):
  for i,v in enumerate((BASE,*args)):put(STACK+4*i,v)
  m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,ecx)
  m.emu_start(address,BASE,count=100000);assert m.reg_read(UC_X86_REG_EIP)==BASE,hex(m.reg_read(UC_X86_REG_EIP))
 def reset(count,next_id,rate,variant):
  m.mem_write(BASE,bytes(0x3e000));allocated.clear();freed.clear();put(0x4db664,MANAGER);put(MANAGER+0x5d0,MANAGER+0x10)
  put(MANAGER+0x5d4,count);put(MANAGER+0x5d8,next_id);m.mem_write(0x4d8f58,struct.pack('<f',rate))
  request=[(0x12345678+variant*0x97813+n*0x12345)&0xffffffff for n in range(0x354//4)]
  for offset,value in ((0,-12.25+variant),(4,80.5),(8,-3.75),(0x18,1.25+variant),(0x20,32.5+variant)):
   request[offset//4]=struct.unpack('<I',struct.pack('<f',value))[0]
  request[0x28//4]=(0,1,0xffffffff,0x7fffffff)[variant];request[0x2c//4]=variant*17
  m.mem_write(REQUEST,struct.pack('<'+'I'*len(request),*request));m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  call(0x43a750,args=(3,REQUEST));return request,m.reg_read(UC_X86_REG_EAX)
 def snapshot():
  alive=get(MANAGER+0x18)!=0
  return [get(MANAGER+0x5d4),get(MANAGER+0x5d8),int(alive),int(bool(freed)),*(
   [get(OBJECT+0xc),get(OBJECT+0x10),get(OBJECT+0x14),*words(OBJECT+0x18,3),*words(OBJECT+0x54,3),get(OBJECT+0x6c),get(OBJECT+0x70),get(OBJECT+0x74),get(OBJECT+0x80),get(OBJECT+0x5bc),get(OBJECT+0xee0)] if alive else [0]*15)]
 cases=[]
 for count in (0,255,256):
  for next_id in (-2,65536,2147483647):
   for rate in (0.,.5,1.,1.25):
    for variant in range(4):
     request,result=reset(count,next_id,rate,variant)
     cases.append(dict(count=count,nextId=next_id,rate=rate,variant=variant,request=request,result=result,snapshot=snapshot(),history=words(OBJECT+0xee4,512) if allocated else [],copied=words(OBJECT+0x5c0,0x354//4) if allocated else []))
 timelines=[]
 for rate in (0.,.5,1.,1.25):
  for reward in (0,1):
   for skip in (0,1):
    for variant in range(4):
     request,result=reset(0,65536,rate,variant);frames=[snapshot()]
     for j in range(12):
      if j==6:call(0x443cb0,OBJECT,(reward,skip))
      call(0x43a570,MANAGER);call(0x43a670,MANAGER);frames.append(snapshot())
     timelines.append(dict(rate=rate,reward=reward,skip=skip,variant=variant,request=request,result=result,frames=frames))
 out=ROOT/'artifacts/th14/laser-shell-native.json';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,timelines=timelines),indent=2)+'\n',encoding='utf-8')
 print(f'{len(cases)} factory cases, {len(timelines)} actual manager update/draw/cancel timelines.')
if __name__=='__main__':main()
