"""Retail Reimu B 414be0 / common update 412200 through 414cc0.
ANM, sound, allocator, damage-area factory and cancellation are boundaries.
Orb motion, bookkeeping and explosion ordering execute as retail x86.
"""
import hashlib,importlib,json,struct,itertools
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 end,player,bomb,spell,manager,pool,areas,vms,shake,stack=0x70000000,0x70001000,0x70021000,0x70023000,0x70025000,0x70034000,0x70035000,0x70040000,0x70049000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 point=lambda p:[get(p+i*4) for i in range(3)]
 events=[];created=[];area_cursor=0;vm_cursor=0
 def sink(machine,a,size,user):
  nonlocal area_cursor,vm_cursor
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x485540:m.reg_write(UC_X86_REG_EAX,pool)
  elif a==0x4854af:m.reg_write(UC_X86_REG_EAX,shake)
  elif a==0x401570:m.reg_write(UC_X86_REG_EAX,shake+0x100)
  elif a==0x48f980:m.mem_write(get(sp+4),bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x47ed10:
   vm_cursor+=1;created.append([get(sp+8),*point(get(sp+12))]);put(get(sp+4),vm_cursor);m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vms+get(sp+4)*0x600)
  elif a==0x47f140:put(vms+get(sp+4)*0x600+0x4a0,get(sp+8))
  elif a in (0x414e59,0x41506c):events.append(['shake',get(shake+0x1c),get(shake+0x20),get(shake+0x24)])
  elif a==0x46e3d0:events.append(['sound',get(sp+4),0,0])
  elif a==0x46e470:events.append(['sound',get(sp+4),1,m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  elif a==0x41b3f0:events.append(['cancel',*point(get(sp+4)),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,get(sp+8)])
  elif a==0x450130:
   p=areas+area_cursor*0xa4;area_cursor+=1;m.mem_write(p,bytes(0xa4));put(p+0x10,3);m.mem_write(p+0x2c,bytes(m.mem_read(get(sp+4),12)));put(p+0x14,m.reg_read(UC_X86_REG_XMM2)&0xffffffff);put(p+0x18,m.reg_read(UC_X86_REG_XMM3)&0xffffffff);put(p+0x84,get(sp+12));put(p+0x8c,9999999);put(p+0x90,1)
   if get(sp+8)!=9999:events.append(['circle',*point(get(sp+4)),get(p+0x14),get(p+0x18),get(sp+8),get(sp+12)])
   m.reg_write(UC_X86_REG_EAX,p)
 for a,n in [(0x485540,0),(0x4855d2,0),(0x4854af,0),(0x401570,4),(0x401120,8),(0x48f980,0),(0x4854a0,0),(0x47ed10,28),(0x47f0a0,4),(0x47f140,8),(0x46e3d0,8),(0x46e470,4),(0x41b3f0,8),(0x450130,12)]:
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 for a in (0x414e59,0x41506c):m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 def reset():
  nonlocal area_cursor,vm_cursor
  m.mem_write(end,bytes(0xf0000));events.clear();created.clear();area_cursor=vm_cursor=0
  for p,v in [(0x4db67c,player),(0x4db52c,bomb),(0x4db534,spell),(0x4db544,manager),(0x4db664,manager+0x2000),(bomb,0x4bd834),(bomb+0x61c,pool),(bomb+0x40,1),(player+0x182d0,1),(player+0x182c4,10),(manager+0x14,7)]:put(p,v)
  floats(player+0x5e0,12.25,400,3);floats(bomb+0x624,12.25,400,3);floats(0x4d8f58,1)
 def call(entry):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bomb);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(entry,end,count=300000);assert m.reg_read(UC_X86_REG_EIP)==end
 starts=[]
 for flags,t in itertools.product((0,1,0x23),(0,59,60,120)):
  reset();put(spell+0x7c,flags);put(spell+0x28,t);put(spell+0x80,12345);call(0x414be0)
  starts.append(dict(flags=flags,time=t,result=[get(spell+0x7c),get(spell+0x80),get(manager+0x14),get(player+0x182c4)],events=events[:],created=created[:]))
 offsets=[4,8,12,0x38,0x3c,0x40,0xb8,0xbc,0xc0,0x1c,0x20,0x24,0x28,0x44,0xa4,0xa8,0xac]
 def orb_state(i):
  p=pool+i*0xd0;a=get(p+0xcc)
  return [*[get(p+o) for o in offsets],get(p+0xa0),int(get(p)!=0),int(a!=0),*[get(a+o) if a else 0 for o in (0x10,0x84,0x88,0x8c,0x90,0x2c,0x30,0x34)],get(vms+(i+1)*0x600+0x4a0)]
 rows=[]
 for t,active,rate,spellflags,total in itertools.product((0,1,7,8,89,90,100,169,199,200,201),(0,1,2),(.5,1,1.25),(0,1),(0,300)):
  reset();put(bomb+0x40,active);put(bomb+0x18,t-1);put(bomb+0x1c,t);floats(bomb+0x20,float(t));put(bomb+0x24,0x4d8f58);floats(0x4d8f58,rate);put(spell+0x7c,spellflags);put(bomb+0x4c,9);vm_cursor=9
  if t:
   for i in range(8):
    p=pool+i*0xd0;a=areas+i*0xa4;put(p,i+1);put(p+0xa0,1);put(p+0xc8,i);put(p+0xcc,a);floats(p+4,10+i,100+i,3);floats(p+0x38,12.25,400,3);floats(p+0xb8,1.25,-2.5,0);floats(p+0x1c,4,-1.25,100,.04908738657832146);put(p+0x44,2 if t<=(i+9)*10 else 0);put(p+0xa4,t-1);put(p+0xa8,t);floats(p+0xac,float(t));put(p+0xb0,0x4d8f58);put(p+0xb4,1)
    put(a+0x10,7);put(a+0x84,15);put(a+0x88,total if i==3 else 0);put(a+0x8c,300);put(a+0x90,3);m.mem_write(a+0x2c,bytes(m.mem_read(p+4,12)))
   area_cursor=8
  # Newly created orbs use VM ids 1..8, as in the runtime fixture.
  if not t:vm_cursor=0
  call(0x412200)
  result=[get(bomb+0x40),get(bomb+0x1c),get(bomb+0x20),get(player+0x182c4),get(vms+9*0x600+0x4a0),int(get(bomb+0x61c)!=0)]
  rows.append(dict(args=[t,active,rate,spellflags,total],result=result,events=events[:],created=created[:],orbs=[orb_state(i) for i in range(8)]))
 (ROOT/'artifacts/th14/reimu-b-controller-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),start=starts,ticks=rows),indent=2)+'\n',encoding='utf-8')
 print(f'{len(starts)} startups, {len(rows)} retail common updates')
if __name__=='__main__':main()
