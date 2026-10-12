"""Own TH16 drop/HUD setters and complete normal interrupt configuration.

Argument resolvers are controlled; 424e40/424eb0 string consumers run unchanged.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x40000)
 full,code,hud,stack,bp=0x70001000,0x70008000,0x7000a000,0x70030000,0x70038000
 data=full+0x120c
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 args=[]
 def argument(machine,address,size,user):
  value=args[get(machine.reg_read(UC_X86_REG_ESP)+4)]&0xffffffff
  machine.reg_write(UC_X86_REG_EAX if address==0x4251d0 else UC_X86_REG_XMM0,value)
 for address in (0x4251d0,0x425200):
  m.mem_write(address,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,argument,begin=address,end=address)
 def execute(op):
  put(bp-0x42c,data);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_ESI,code);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_ESP,stack)
  entry=img.u32(0x422ab8+4*img.read(0x422d70+op-300,1)[0]);m.emu_start(entry,0x422a9b,count=2000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
 drops=[]
 for index in range(18):
  for value in (-2147483648,-1,0,1,17,2147483647):
   m.mem_write(data+0x3f90,bytes(0x50));args=[index,value];execute(507)
   drops.append(dict(op=507,args=args,output=[get(data+0x3f90+n*4) for n in range(20)]))
 for value in (-2147483648,-1,0,1,17,2147483647):
  m.mem_write(data+0x3f90,bytes(0x50));args=[value];execute(510)
  drops.append(dict(op=510,args=args,output=[get(data+0x3f90+n*4) for n in range(20)]))
 for x,y in ((0,0),(-0.0,0),(32,64),(-2.5,1e-10),(1e20,-1e20)):
  m.mem_write(data+0x3f90,bytes(0x50));args=[bits(x),bits(y)];execute(508)
  drops.append(dict(op=508,args=args,output=[get(data+0x3f90+n*4) for n in range(20)]))
 put(0x4a6dcc,hud);phase_counts=[]
 for value in (-2147483648,-100,-1,0,1,2,9,10,11,2147483647):
  put(hud+0x188,0xa5a5a5a5);args=[value];execute(540);phase_counts.append(dict(value=value,output=get(hud+0x188)))
 markers=[]
 for boss in range(4):
  for index in range(4):
   for maximum in (-2147483648,-1,1,999,1000,2147483647):
    for amount,kind in ((0,0),(1,-1),(500,0x11223344),(-77.25,-2147483648)):
     m.mem_write(hud,bytes(0x400));put(data+0x4070,boss);put(data+0x3f78,maximum);args=[index,bits(amount),kind];execute(527)
     markers.append(dict(boss=boss,index=index,maximum=maximum,amount=amount,kind=kind,output=[get(hud+0x1ec+b*0x54+n*8+off) for b in range(4) for n in range(4) for off in (0,4)]))
 interrupts=[];put(0x4a5bec,0);put(data+0x44b8,full)
 for op in (514,521):
  for index in range(8):
   for health,time,name in ((-1,90,'unused'),(0,0,''),(1000,1800,'Boss01Nonspell01'),(2147483647,-2147483648,'A'*63)):
    m.mem_write(data+0x4078,bytes(0x440));put(data+0x4078+index*0x88,37);put(data+0x407c+index*0x88,99)
    m.mem_write(data+0x4080+index*0x88,b'old-health\0');m.mem_write(data+0x40c0+index*0x88,b'old-timeout\0')
    m.mem_write(code,bytes(128));m.mem_write(code+(0x20 if op==514 else 0x18),name.encode()+b'\0');args=[index,health,time];execute(op)
    start=data+0x4078+index*0x88
    names=[bytes(m.mem_read(start+off,64)).split(b'\0')[0].decode() for off in (8,72)]
    interrupts.append(dict(op=op,index=index,health=health,time=time,name=name,output=[get(start),get(start+4)],names=names))
 spell,manager,bomb,ret=0x7000b000,0x7000c000,0x7000d000,0x7003f000
 put(0x4a6db0,spell);put(0x4a6dc0,manager);put(0x4a6da8,bomb)
 consumers=[]
 import itertools
 health_inputs=itertools.product(range(9),(-2147483648,-1,0,99,100,101,2147483647),(0,0x800000,0x1000000,0xffffffff),(-1,0,7),(1,2))
 timed_inputs=itertools.product(range(9),(-1,0,59,60,6000,2147483647),(0,0x800000),(0,1,8,9,0x23,0xffffffff),(59,60),(0,1,2))
 for path,inputs in ((0,health_inputs),(1,timed_inputs)):
  for values in inputs:
   if path==0:index,health,flags,credit,chapter=values;clock=60;spellflags=0x23;elapsed=60;special=1
   else:index,clock,flags,spellflags,elapsed,special=values;health=999;credit=7;chapter=2
   m.mem_write(full,bytes(0x6000))
   for n in range(8):put(full+0x5284+n*0x88,-1)
   if index<8:put(full+0x5284+index*0x88,100);put(full+0x5288+index*0x88,60)
   for off,v in ((0x5180,health),(0x5188,37),(0x5190,38),(0x526c,flags),(0x5734,1),(0x5738,credit),(0x14c8,19),(0x14cc,clock),(0x14d0,bits(clock+.5)),(0x14d4,0),(0x14d8,0)):put(full+off,v)
   put(hud+0x1d0,17);put(hud+0x1d4,18);put(spell+0x78,spellflags);put(spell+0x24,elapsed);put(spell+0x7c,31);put(manager+0x44,37);put(bomb+0x30,special);put(0x4a5798,chapter);put(0x4a5884,2147483647)
   put(stack,ret);m.reg_write(UC_X86_REG_ECX,full);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x424f00 if path==0 else 0x425010,ret,count=2000);assert m.reg_read(UC_X86_REG_EIP)==ret
   result=m.reg_read(UC_X86_REG_EAX);selection=0 if result==0 else ((result-full-(0x528c if path==0 else 0x52cc))//0x88)+1
   output=[get(full+off) for off in (0x5180,0x5188,0x5190,0x526c,0x5738,0x14c8,0x14cc,0x14d0)]+[int(bool(get(full+0x14d8)&1)),get(full+0x14d8)]+[get(hud+0x1d0),get(hud+0x1d4),get(spell+0x78),get(spell+0x7c),get(manager+0x44),get(0x4a5884)]+[get(full+0x5284+n*0x88) for n in range(8)]
   consumers.append(dict(path=path,index=index,health=health,clock=clock,flags=flags,credit=credit,chapter=chapter,spellflags=spellflags,elapsed=elapsed,special=special,selection=selection,output=output))
 deformations=[];events=[];obj=0x7000e000
 def deformation_boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x409d90:events.append(0)
  elif a==0x4749ac:machine.reg_write(UC_X86_REG_EAX,obj)
  else:events.append(get(sp+8));machine.reg_write(UC_X86_REG_EAX,obj)
 for a,cleanup in ((0x409d90,4),(0x4749ac,0),(0x418c70,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,deformation_boundary,begin=a,end=a)
 for old in (False,True):
  for target in (-1,0,16,32,128):
   for color in (0,0x008f8fff,0xffffffff):
    args=[bits(target),color];put(data+0x44bc,obj if old else 0);events.clear();execute(629)
    deformations.append(dict(old=old,target=target,color=color,output=[int(get(data+0x44bc)!=0)]+[get(data+o) for o in (0x44c4,0x44c8,0x44cc,0x44d0,0x44d4)],events=list(events)))
 out=ROOT/'artifacts/th16/enemy-phase-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),drops=drops,markers=markers,interrupts=interrupts,consumers=consumers,deformations=deformations,phaseCounts=phase_counts),separators=(',',':'))+'\n',encoding='utf-8')
 print(f'{len(drops)} drop setters; {len(markers)} boss markers; {len(interrupts)} normal interrupt configurations; {len(consumers)} health/time consumers')
if __name__=='__main__':main()
