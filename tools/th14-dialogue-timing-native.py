"""Complete original dialogue update clocks, wait and input gates."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def inputs(profile,frame):
 if profile==1:return 0,1 if frame%6==3 else 0,0,0
 if profile==2:return 0x200,0x200 if frame==0 else 0,frame+1,0
 if profile==3:return 1,1 if frame==0 else 0,0,frame+1
 if profile==4:return 0x200,0,frame+30,0
 if profile==5:return 0,0x80000 if frame%8==4 else 0,0,0
 if profile==6:return 1,0,0,frame+30
 if profile==7:
  n=frame%44
  if n<19:return 0x200,0x200 if n==0 else 0,n+1,0
  if 22<=n<43:return 0x200,0x200 if n==22 else 0,n-21,0
  return 0,0,0,0
 if profile==8:
  n=frame%50
  return (1,1 if n==0 else 0,0,n+1) if n<21 else (0,0,0,0)
 if profile==9:return 0x201,0x201 if frame==0 else 0,frame+1,frame+1
 return 0,0,0,0
def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x20000);d=base+0x1000;code=base+0x3000;stack=base+0x1f000;sounds=[];keys=[0,0]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,0);pop=4
  elif a==0x435590:uc.reg_write(UC_X86_REG_EAX,keys[0] if get(sp+4)==9 else keys[1]);pop=4
  elif a==0x46e3d0:sounds.append(get(sp+4));pop=8
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x47f0a0,0x435590,0x46e3d0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4f56cc,base+0x8000)
 def state():return [get(d+o) for o in (0x184,0x180,0x188,0x18c,8,12,0x1c,0x20,0x30,0x34)]+[get(d+0x158)-code,len(sounds)]
 rows=[]
 for flags,rate,duration,profile in itertools.product((0,1,0x40,0x41),(.5,1.,1.25),(0,1,3,15,60),range(10)):
  program=b''
  for time,op,payload in ((0,30,b''),(0,11,struct.pack('<i',duration)),(8,12,b''),(10,11,struct.pack('<i',duration+2)),(14,26,b''),(18,0,b'')):program+=struct.pack('<HBB',time,op,len(payload))+payload
  m.mem_write(d,bytes(0x200));m.mem_write(code,program);put(d+0x158,code);put(d+0x184,flags);put(d+0x180,3);put(d+0x188,1);put(d+0x18c,1);m.mem_write(0x4d8f58,struct.pack('<f',rate))
  for timer in (d+4,d+0x18,d+0x2c):put(timer,0xffffffff);put(timer+12,0x4d8f58);put(timer+16,1)
  sounds.clear();frames=[]
  for frame in range(640):
   held,pressed,skip,fire=inputs(profile,frame);put(0x4d6a90,held);put(0x4d6a9c,pressed);put(0x4d6a30,skip);put(0x4d6a0c,fire);keys[:]=[skip,fire];put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,d);m.reg_write(UC_X86_REG_MXCSR,0x1f80);
   try:m.emu_start(0x432390,base,count=100000)
   except Exception:print(flags,rate,duration,profile,frame,hex(m.reg_read(UC_X86_REG_EIP)));raise
   assert m.reg_read(UC_X86_REG_EIP)==base;status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(input=[held,pressed,skip,fire],status=status,state=state()))
   if status:break
  assert frames[-1]['status']==1,(flags,rate,duration,profile)
  rows.append(dict(input=[flags,rate,duration,profile],frames=frames))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Full original432390 wrapper and432400 dialogue interpreter, original timers408b00/4115a0, six synthetic MSG instructions with two waits and release/style reset. Original held/pressed globals and key duration globals populated; ten input schedules include preheld Ctrl/Z, latch preset, 19-frame Ctrl release/repress, 21-frame Z release and simultaneous holds;435590 returns controlled matching key durations; sound and absent-panel lookup controlled. No original ANM/resources/world/GPU execution.')
 (ROOT/'artifacts/th14/dialogue-timing-native.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native dialogue timing',len(rows),sum(len(r['frames']) for r in rows))
if __name__=='__main__':main()
