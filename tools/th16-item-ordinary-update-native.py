"""Own42f4e0 single active season-item body; controlled VM/reward boundaries."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x2000000);manager,player,bomb,season,enemy,sht,stack=0x70000000,0x71d00000,0x71d40000,0x71d50000,0x71d60000,0x71d70000,0x71ffd000;item=manager+0x14;events=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a in (0x430052,0x43005f):machine.emu_stop();return
  if a==0x430d90:put(machine.reg_read(UC_X86_REG_ECX)+0xc50,0)
  elif a==0x43de50:events.append([0]);machine.reg_write(UC_X86_REG_EAX,0)
  elif a==0x43e080:events.append([1,get(sp+4)])
  elif a==0x42c600:events.append([2])
  elif a==0x45e1f0:events.append([3,get(sp+4),machine.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  else:events.append([4])
 for a,cleanup in ((0x430d90,0),(0x43de50,4),(0x43e080,4),(0x42c600,0),(0x45e1f0,4),(0x430d10,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 for a in (0x430052,0x43005f):m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def invalid(machine,access,address,size,value,user):
  print('unmapped',hex(machine.reg_read(UC_X86_REG_EIP)),hex(address),state,clock,rate,position,scenario,speed);return False
 m.hook_add(UC_HOOK_MEM_INVALID,invalid)
 for a,p in ((0x4a6ef8,player),(0x4a6da8,bomb),(0x4a6da4,season),(0x4a6dcc,enemy)):put(a,p)
 put(player+0x2c788,sht);put(sht+8,bits(8));put(manager+0xe4b974,bits(1));put(0x490eb0,0x4a5788)
 put(0x4a57e4,0);put(0x4a57e8,400);cases=[]
 scenarios=[(1,400,0,0,0,0),(2,400,0,0,0,0),(4,400,0,0,0,0),(1,100,0,0,0,0),(1,400,1,0,0,0),(1,400,0,1,0,0),(1,400,0,0,1,0),(1,400,0,0,0,1)]
 inputs=((kind,*v) for kind in range(1,9) for v in itertools.product((1,4,5),(0,31,32),(.5,1,2),((17.25,61.5,2),(199.5,471.5,0),(201,473,0)),(0,3,4,5,6,7),(1.9,)))
 for kind,state,clock,rate,position,scenario,speed in inputs:
  ps,py,ba,sa,spa,focused=scenarios[scenario];m.mem_write(item,bytes(0xc78));put(item,manager+0xe4b964);put(manager+0xe4b968,0);put(item+0xc50,state);put(item+0xc54,kind);put(item+0xc58,kind)
  for off,values in ((0xc08,position),(0xc14,(.125,-.25,.375)),(0xc20,(speed,.75)),(0xc5c,(2.5,))):
   for n,v in enumerate(values):put(item+off+n*4,bits(v))
  put(item+0xc28,clock-1);put(item+0xc2c,clock);put(item+0xc30,bits(clock));put(item+0xc38,1)
  put(player+0x610,bits(0));put(player+0x614,bits(py));put(player+0x165a8,ps);put(0x4a57a4,scenario%4);put(0x4a52c8,8 if focused else 0);put(bomb+0x30,ba);put(bomb+0x38,0);put(season+0x30,sa);put(season+0x38,0);put(enemy+0x1c8,spa);put(0x4a586c,0)
  for off,values in ((0x2c7dc,(-2,py-2,0,2,py+2)),(0x2c7f4,(-64,py-64,0,64,py+64)),(0x2c80c,(-32,py-32,0,32,py+32))):
   for n,v in enumerate(values):put(player+off+n*4,bits(v))
  if kind!=16:
   for off,v in ((0,9999),(4,9999),(12,10000),(16,10000)):put(player+0x2c7dc+off,bits(v))
  put(0x4a5788,bits(rate));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);events.clear();m.emu_start(0x42f4e0,0,count=5000);assert m.reg_read(UC_X86_REG_EIP) in (0x430052,0x43005f),hex(m.reg_read(UC_X86_REG_EIP))
  output=[get(item+off) for off in (0xc08,0xc0c,0xc10,0xc14,0xc18,0xc1c,0xc20,0xc24,0xc28,0xc2c,0xc30,0xc38,0xc50,0xc5c,0xc60,0xc68,0x530)]+[get(manager+0x1c972dc),get(0x4a586c)]
  cases.append(dict(kind=kind,state=state,clock=clock,rate=rate,position=position,scenario=scenario,speed=speed,output=output,events=list(events)))
 (ROOT/'artifacts/th16/item-ordinary-update-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),scenarios=scenarios,cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own item update bodies')
if __name__=='__main__':main()
