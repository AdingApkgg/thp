"""Retail 41ae00 reward dispatch, RNG, pool allocation and ordinary factory.
Only resource ANM binding/ticking, zero-handle cleanup and effect/audio sinks
are replaced. Cancel slots, signed counters, delay and polar math are native.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x1900000)
 items,bullets,spell,pos,stack,stop=[base+n for n in (0,0xe00000,0x1800000,0x1850000,0x18ff000,0x18fe000)]
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 slot=lambda n:items+0x14+n*0xc18
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x40af00:
   vm=get(sp+4);m.mem_write(vm,bytes(0x5cc));put(vm+0x18,1)
  elif a==0x47f140:assert get(sp+4)==0
  elif a==0x47ed10:m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x40af00,8),(0x46fe50,0),(0x47f140,8),(0x47ed10,28),(0x46e3d0,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 put(0x4db660,items);put(0x4db530,bullets);put(0x4db534,spell)
 m.mem_write(0x4db508,struct.pack('<HHI',54321,0,123))
 def run(reward,flags,count,seed,load,spawn,available,p,ordinary_full=False):
  for n in (599,4695,4694):m.mem_write(slot(n),bytes(0xc18))
  put(items+0xddd858,0 if ordinary_full else slot(599));put(slot(599)+8,items+0xddd854)
  put(items+0xddd868,slot(4695) if available else 0)
  if available:
   put(slot(4695)+8,items+0xddd864);put(slot(4695)+4,slot(4694) if available==2 else 0)
   if available==2:put(slot(4694)+8,slot(4695))
  put(items+0xddd878,spawn);put(items+0xddd87c,load);put(items+0xddd880,0x12345678)
  put(bullets+0x9bf6c8,count);put(spell+0x7c,flags);m.mem_write(pos,struct.pack('<III',*p))
  m.mem_write(0x4db510,struct.pack('<HHI',seed,0,0));put(stack,stop)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,pos);m.reg_write(UC_X86_REG_EDX,reward)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x41ae00,stop,count=30000);assert m.reg_read(UC_X86_REG_EIP)==stop
  def value(n):return [get(slot(n)+o) for o in (0xbf0,0xbf4,0xbf8,0xbac,0xbb0,0xbb4,0xbb8,0xbbc,0xbc0,0xc00,0xc04,0xbc8,0xbcc,0xbd0)]
  return dict(rewards=reward,flags=flags,count=count,seed=seed,load=load,spawn=spawn,available=available,ordinaryFull=ordinary_full,positionBits=p,
   result=[get(bullets+0x9bf6c8),get(items+0xddd878),int.from_bytes(m.mem_read(0x4db510,2),'little'),get(0x4db514)],slots=[value(n) for n in (4695,4694,599)])
 rows=[];p=[bits(17.25),bits(61.5),bits(2)]
 for reward in (0,1,2,3,4):
  for flags in (0,1,0x23):
   for count in (0,3,4,0x7fffffff,0xfffffffa,0xffffffff):
    for seed in (0,12345):
     for available in (0,1,2):
      rows.append(run(reward,flags,count,seed,512,0xffffffff,available,p))
 for reward in (1,2,3):
  for load in (0,255,256,511,512,1023,1024):
   for spawn in (0,1,3,0x7ffffffe,0x7fffffff,0xfffffffe,0xffffffff):
    for available in (0,1,2):rows.append(run(reward,0,4,65535,load,spawn,available,p))
 for reward in (0,1,2,3,4):
  for xy in ((-224,0),(-223.99998,0),(224,0),(223.99998,0),(0,-32),(0,-31.999998),(0,480),(0,479.99997),(0,0),(float('nan'),100),(0,float('nan')),(float('inf'),100),(float('-inf'),100),(0,float('inf')),(0,float('-inf'))):
   rows.append(run(reward,0,4,12345,0,0,2,[bits(xy[0]),bits(xy[1]),0]))
 for available in (0,1,2):rows.append(run(2,0,4,12345,0,0,available,p,True))
 assert int.from_bytes(m.mem_read(0x4db508,2),'little')==54321 and get(0x4db50c)==123
 out=ROOT/'artifacts/th14/bomb-reward-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} retail Bomb reward cases, types 0/1/2/3/4.')
if __name__=='__main__':main()
