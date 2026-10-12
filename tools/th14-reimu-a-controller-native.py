"""Retail Reimu A startup/common tick with actual rectangle allocation.
ANM, audio, heap/registry and bullet/laser consumers are controlled boundaries.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,im.data[raw:raw+n])
 end,player,bomb,spell,manager,pool,vms,shake,stack=0x70000000,0x70001000,0x70021000,0x70023000,0x70025000,0x70034000,0x70040000,0x70049000,0x700ff000
 bullet=0x71000000;m.mem_map(end,0x100000);m.mem_map(bullet,0xa00000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));point=lambda p:[get(p+i*4)for i in range(3)]
 events=[];created=[];missing=False
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x485540:m.reg_write(UC_X86_REG_EAX,pool)
  elif a==0x4854af:m.reg_write(UC_X86_REG_EAX,shake)
  elif a==0x401570:m.reg_write(UC_X86_REG_EAX,shake+0x100)
  elif a==0x48f980:m.mem_write(get(sp+4),bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x47ed10:
   created.append([get(sp+8),*point(get(sp+12))]);put(get(sp+4),len(created));m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,0 if missing and get(sp+4)==1 else vms+get(sp+4)*0x1000)
  elif a==0x47f140:put(vms+get(sp+4)*0x1000+0x4a0,get(sp+8))
  elif a==0x46e3d0:events.append(['sound',get(sp+4),0,0])
  elif a==0x46e470:events.append(['sound',get(sp+4),1,m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  elif a==0x41b4f0:events.append(['cancel',*point(get(sp+4)),*point(get(sp+8))[:2],m.reg_read(UC_X86_REG_XMM3)&0xffffffff,get(sp+12)])
  elif a==0x47fcb0:m.reg_write(UC_X86_REG_EAX,vms+0x5000)
  elif a==0x40af00:created.append([get(sp+8),0,0,0]);put(get(sp+4)+0x580,get(sp+4))
  elif a==0x47e890:
   created[-1][1:]=point(vms+0x5000+0x59c);put(get(sp+4),3);m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x413e81:events.append(['shake',get(shake+0x1c),get(shake+0x20),get(shake+0x24)]) if shake_event else None
  elif a==0x4144a0:
   # The retail polar helper writes only x/y; its caller reads the unwritten
   # third stack word. Control that undefined scratch input explicitly.
   put(m.reg_read(UC_X86_REG_ECX)+8,0)
 hooks=[(0x485540,0),(0x4855d2,0),(0x4854af,0),(0x401570,4),(0x401120,8),(0x48f980,0),(0x4854a0,0),(0x403cd0,0),(0x403df0,0),(0x47ed10,28),(0x47f0a0,4),(0x47f140,8),(0x46e3d0,8),(0x46e470,4),(0x41b4f0,12),(0x47fcb0,0),(0x40af00,8),(0x46fe50,0),(0x47e890,8)]
 for a,n in hooks:
  m.mem_write(a,b'\xc2'+struct.pack('<H',n)if n else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 m.hook_add(UC_HOOK_CODE,sink,begin=0x413e81,end=0x413e81)
 m.hook_add(UC_HOOK_CODE,sink,begin=0x4144a0,end=0x4144a0)
 def reset(rate=1):
  m.mem_write(end,bytes(0xf0000));events.clear();created.clear()
  for p,v in [(0x4db67c,player),(0x4db52c,bomb),(0x4db534,spell),(0x4db544,manager),(0x4db530,bullet),(0x4db664,manager+0x2000),(bomb,0x4bd850),(bomb+0x61c,pool),(bomb+0x40,1),(player+0x10,manager+0x4000),(player+0x182d0,1),(player+0x182c4,10),(manager+0x14,7)]:put(p,v)
  floats(player+0x5e0,12.25,400,3);floats(bomb+0x624,12.25,400,3);floats(0x4d8f58,rate);m.mem_write(0x4f5815,b'\0')
 def call(entry):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bomb);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(entry,end,count=300000)
  except Exception as e:raise RuntimeError(hex(m.reg_read(UC_X86_REG_EIP)))from e
  assert m.reg_read(UC_X86_REG_EIP)==end
 def area_values(a):return [get(a+n)for n in (0x10,0x1c,0x24,0x28,0x2c,0x30,0x34,0x70,0x74,0x78,0x84,0x88,0x8c,0x90)]+[int(get(a+0xa0)==0x414020)]
 starts=[];shake_event=False
 for flags,t,rate in itertools.product((0,1,0x23),(0,59,60,120),(.5,1,1.25)):
  reset(rate);missing=False;put(spell+0x7c,flags);put(spell+0x28,t);put(spell+0x80,12345);call(0x413240)
  starts.append(dict(args=[flags,t,rate],result=[get(spell+0x7c),get(spell+0x80),get(manager+0x14),get(player+0x182c4),get(player+0x182d4)],events=events[:],created=created[:],areas=[area_values(get(pool+4+i*4))for i in range(4)],history=[point(pool+0x14+i*12)for i in range(10)]))
 ticks=[]
 for t,active,rate,kind,angle,advanced in itertools.product((0,1,15,18,20,21,23,24,26,29,30,31,50,51,60,249,250,251),(0,1,2),(.5,1,1.25),(0,1,2,3),(-3.,.37,9.),(False,True)):
  reset(rate);missing=kind==0;shake_event=active!=0 and t<250 and t%30==20;put(bomb+0x44,1);put(bomb+0x4c,2);put(pool,1);put(bomb+0x40,active);put(bomb+0x18,t-int(advanced));put(bomb+0x1c,t);floats(bomb+0x20,t);put(bomb+0x24,0x4d8f58);put(bomb+0x28,1);put(player+0x182d4,0x24);floats(player+0xd6dc,.75);floats(player+0xd6e0,2,3,4)
  for i in range(4):
   a=player+0xde18+i*0xa4;put(pool+4+i*4,a);put(a+0x10,5);put(a+0x84,[300,100,70,50][i]);put(a+0x8c,9999999);put(a+0x90,10);put(a+0xa0,0x414020);floats(a+0x24,128,[96,80,64,40][i]);floats(a+0x2c,12.25,400,3);put(a+0x70,299);put(a+0x74,300);floats(a+0x78,300)
  for i in range(10):floats(pool+0x14+i*12,10+i,100+i,3);floats(pool+0x8c+i*4,.1*i)
  floats(pool+0xb4,0,-12,0,0,0);put(pool+0xc8,2);put(pool+0xcc,3);floats(pool+0xd0,3);put(pool+0xd4,0x4d8f58);put(pool+0xd8,1);put(pool+0xdc,20);put(pool+0xe0,22)
  root=vms+0x1000;child=vms+0x3000;last=vms+0x4000;put(root+0x580,root);put(root+0x584,child+0x580);put(child+0x580,child);put(child+0x584,last+0x580 if kind==3 else 0);m.mem_write(child+0x4aa,struct.pack('<h',-2 if kind==3 else 13));floats(child+0x50,angle);floats(child+0x60,-1 if kind==2 else 1);put(last+0x580,last);floats(last+0x50,1.5);floats(last+0x60,1)
  call(0x412200)
  result=[get(bomb+0x40),int(get(pool)!=0),get(bomb+0x1c),get(bomb+0x20),get(player+0x182c4),get(player+0x182d4),get(player+0xd6dc),*point(player+0xd6e0),int(get(bomb+0x61c)!=0),get(root+0x1c),get(child+0x1c),get(last+0x1c),get(vms+0x2000+0x4a0)]
  ticks.append(dict(args=[t,active,rate,kind,angle,int(advanced)],result=result,events=events[:],created=created[:],areas=[area_values(player+0xde18+i*0xa4)for i in range(4)],history=[point(pool+0x14+i*12)+[get(pool+0x8c+i*4)]for i in range(10)],interpolator=[get(pool+n)for n in (0xb4,0xb8,0xc8,0xcc,0xd0,0xdc,0xe0)]))
 (ROOT/'artifacts/th14/reimu-a-controller-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),start=starts,ticks=ticks),indent=2)+'\n',encoding='utf8')
 print(f'{len(starts)} Reimu A startups / {len(ticks)} common updates.')
if __name__=='__main__':main()
