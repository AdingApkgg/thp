"""Actual 417080 bullet and 43a570 laser manager freeze dispatch.
Movement, timers and actual collision virtuals run natively. ANM delivery,
player collision result and graze delivery are recorded boundaries.
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
 base=0x70000000;m.mem_map(base,0xa20000)
 manager,obj,node,samples,stack,stop=[base+n for n in (0,0x9d0000,0x9d5000,0x9d6000,0xa1f000,0xa10000)]
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 events=[];graze=0;kind=-1
 def boundary(machine,a,size,user):
  nonlocal graze
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x44ee80:
   p=get(sp+4);s=get(sp+8);probe=get(sp+12);events.append([0,probe,get(p),get(p+4),get(s),get(s+4)]);m.reg_write(UC_X86_REG_EAX,2 if probe else 0)
  elif a==0x44f0b0:
   # 44f0b0 and graze 450410 read only x/y. 440d80 leaves its
   # temporary z uninitialized; do not equate that unused stack residue.
   p=get(sp+4);events.append([1,get(sp+12),get(p),get(p+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,m.reg_read(UC_X86_REG_XMM3)&0xffffffff,get(sp+8)]);m.reg_write(UC_X86_REG_EAX,2)
  elif a==0x450410:graze+=1
  elif a==0x46fe50:m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x44ee80,12),(0x44f0b0,12),(0x450410,4),(0x46fe50,0),(0x4854a0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def call(a):
  put(stack,stop);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  try:m.emu_start(a,stop,count=100000)
  except Exception as e:raise RuntimeError(f'entry {a:x} pc {m.reg_read(UC_X86_REG_EIP):x} kind {kind} state {state} timer {timer} rate {rate}') from e
  assert m.reg_read(UC_X86_REG_EIP)==stop,hex(m.reg_read(UC_X86_REG_EIP))
 rows=[]
 for flags in (0,2,6,0x100,0x102,0x106,0x302):
  for state in (1,2,3,4):
   for timer in (0,7,8):
    for rate in (.5,1,1.25):
     m.mem_write(manager,bytes(0x100));m.mem_write(obj,bytes(0x3000));put(0x4db558,0);put(0x4db530,manager);put(manager+0x80,node);put(node,obj);put(node+4,0)
     put(obj+0x20,flags);put(obj+0x24,3);m.mem_write(obj+0xc0e,struct.pack('<h',state));put(obj+0xc00,0xffffffff);put(obj+0xc24,2);put(obj+0xbfc,10)
     for off,v in ((0xbc0,12.25),(0xbc4,70.5),(0xbc8,2),(0xbcc,1.25),(0xbd0,-.75),(0xbd4,.5),(0xbe0,8),(0xbe4,8),(0x13c8,timer+.25),(0x13dc,5.5)):put(obj+off,bits(v))
     for off,v in ((0x13c0,timer-1),(0x13c4,timer),(0x13cc,0x4d8f58),(0x13d0,1),(0x13d4,4),(0x13d8,5),(0x13e0,0x4d8f58),(0x13e4,1)):put(obj+off,v)
     put(0x4d8f58,bits(rate));frames=[]
     for frame in range(5):
      events.clear();graze=0;call(0x417080)
      result=[get(obj+o) for o in (0x20,0x24,0xbc0,0xbc4,0xbc8,0x13c0,0x13c4,0x13c8,0x13d4,0x13d8,0x13dc)]
      result+=[int.from_bytes(m.mem_read(obj+0xc0e,2),'little'),get(manager+0x5c),int(bool(get(manager+0x1c)))]
      frames.append(dict(result=result,events=events[:],graze=graze))
     rows.append(dict(flags=flags,state=state,timer=timer,rate=rate,frames=frames))
 lasers=[]
 for kind in (1,2,3):
  for state in (2,3,4,5):
   for timer in (0,1,2,3,-1):
    for rate in (.5,1,1.25):
     m.mem_write(manager,bytes(0x600));m.mem_write(obj,bytes(0x3000));put(manager+0x18,obj);put(manager+0x5d0,obj);put(manager+0x5d4,1);put(obj+4,manager+0x10)
     put(obj,{1:0x4be3cc,2:0x4be2fc,3:0x4be364}[kind]);put(obj+0xc,8);put(obj+0x10,state);put(obj+0x14,kind)
     for off,v in ((0x18,8),(0x1c,9),(0x24,0x4d8f58),(0x28,1),(0x2c,timer-1),(0x30,timer),(0x38,0x4d8f58),(0x3c,1)):put(obj+off,v)
     for off,v in ((0x20,9.25),(0x34,timer+.25),(0x54,12.25),(0x58,70.5),(0x5c,2),(0x6c,.125),(0x70,64),(0x74,24)):put(obj+off,bits(v))
     put(obj+0x5e0,7);put(obj+0x14ac,samples)
     for j in range(7):m.mem_write(samples+j*32,struct.pack('<8f',12.25+j*.75,70.5-j*.125,2,0,0,0,.125,4))
     put(0x4d8f58,bits(rate));frames=[]
     for frame in range(8):
      events.clear();graze=0;call(0x43a570)
      frames.append(dict(result=[get(obj+o) for o in (0xc,0x10,0x18,0x1c,0x20,0x2c,0x30,0x34)],events=events[:],graze=graze))
     lasers.append(dict(kind=kind,state=state,timer=timer,rate=rate,frames=frames))
 out=ROOT/'artifacts/th14/time-freeze-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),bullets=rows,lasers=lasers),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)*5} bullet and {len(lasers)*8} laser manager freeze frames.')
if __name__=='__main__':main()
