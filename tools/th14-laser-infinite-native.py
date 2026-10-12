"""Retail kind-1 initializer, motion/lifecycle and full cancellation.
ANM delivery, sound and item creation are recorded boundaries. State/math run natively.
The update stops at 43e27c, before collision and ANM delivery.
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
 end,obj,request,manager,boss,resource,effect,stack=0x70000000,0x70001000,0x70004000,0x70005000,0x70006000,0x70010000,0x70011000,0x700ff000;m.mem_map(end,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 deliveries=[];effect_script=0;fragments=[];cursor=0x70020000
 def boundary(machine,a,size,user):
  nonlocal effect_script,cursor
  sp=m.reg_read(UC_X86_REG_ESP);vm=m.reg_read(UC_X86_REG_ECX)
  if a in (0x40cc90,0x40d0c0):m.mem_write(vm,bytes(0x5cc))
  elif a in (0x46f520,0x40af00):
   vm=get(sp+4);script=get(sp+8)
   if vm==effect:effect_script=script
  elif a==0x47fcb0:m.mem_write(effect,bytes(0x5cc));m.reg_write(UC_X86_REG_EAX,effect)
  elif a==0x46fe50 and vm==effect:deliveries.append([effect_script,*words(effect+0x59c,3)])
  elif a==0x47ed10:deliveries.append([get(sp+8),*words(get(sp+12),3)])
  elif a==0x4854af:
   size=get(sp+4);m.mem_write(cursor,bytes(size));m.reg_write(UC_X86_REG_EAX,cursor);cursor+=(size+15)&~15;return
  elif a==0x43aca0:fragments.append(words(get(sp+4),0x354//4))
  elif a==0x41ae00:
   reward=m.reg_read(UC_X86_REG_EDX)
   if reward:deliveries.append([0x10000+reward,*words(vm,3)])
  m.reg_write(UC_X86_REG_EAX,0 if a!=0x47fcb0 else effect)
 for a,cleanup in ((0x40cc90,0),(0x40d0c0,0),(0x46f520,8),(0x40af00,8),(0x46fe50,0),(0x46e470,4),(0x47fcb0,0),(0x47e890,8),(0x47ed10,28),(0x41ae00,0),(0x4854af,0),(0x43aca0,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def call(a,args=(),stop=None):
  m.mem_write(stack-0x3000,bytes(0x3100));put(stack,end)
  for j,v in enumerate(args):put(stack+4+4*j,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(a,stop or end,count=1000000)
  assert m.reg_read(UC_X86_REG_EIP) in (stop,end),hex(m.reg_read(UC_X86_REG_EIP))
  return m.reg_read(UC_X86_REG_EAX) if m.reg_read(UC_X86_REG_EIP)==end else 0
 fields=(0x10,0x14,0x54,0x58,0x5c,0x6c,0x70,0x74,0x78,0x80,0x5b4,0x594,0x598,0x2c,0x30,0x34,0x18,0x1c,0x20)
 def state():return [get(obj+o) for o in fields]
 put(0x4db664,manager);put(manager+0x5f4,resource);put(0x4db544,manager);put(manager+0x5c,boss)
 m.mem_write(boss+0x1234,struct.pack('<3f',7.5,120.25,-3.5));put(0x4f5815,0)
 # The cancellation's bullet-manager resource pointer is far into its owner.
 bullet_owner=0x71000000;m.mem_map(bullet_owner,0x9c0000);put(0x4db530,bullet_owner);put(bullet_owner+0x9bf6cc,resource)
 rows=[]
 for variant in range(20):
  for rate in (0.,.5,1.,1.25):
   for program in (0,1,2):
    r=[0]*(0x374//4);r[0:3]=list(map(bits,(-22.25,40.5,3.25)));r[3:6]=list(map(bits,(.125,-.25,.03125)))
    r[6:12]=list(map(bits,((-200.,-.125,3.15,200.)[variant%4],(-.125,0.,.1)[variant%3],(16.,100.,640.)[variant%3],(-1.,0.,7.,24.)[variant%4],(0.,8.,24.,64.)[variant%4],(-1.,0.,.25,8.)[variant%4])))
    r[12:16]=[(0,1,7,30)[variant%4],(0,1,8)[variant%3],(0,1,5,60)[variant%4],(0,1,9)[variant%3]]
    r[16:23]=[0xffffffff,0xffffffff,0x12345678,bits((0.,7.25)[variant%2]),variant%43,variant%16,variant%2]
    if program:
     for j,(op,p,concurrent) in enumerate(((0x80,7,1),(0x100000,program-1,0),(4,60,1),(0x400,0,1))):
      t=23+j*11;r[t+4]=p;r[t+8]=op;r[t+9]=concurrent
    m.mem_write(obj,bytes(0x2000));m.mem_write(request,struct.pack('<221I',*r));put(0x4d8f58,bits(rate));call(0x43a8f0);call(0x43ddc0,(request,));initial=state();frames=[]
    for frame in range(150):
     result=call(0x43e040,stop=0x43e27c)
     if not result:
      # Manager advances the base lifetime after a surviving update.
      put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj+0x18);m.emu_start(0x408690,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
     frames.append(dict(result=result,state=state()))
     if result:break
    rows.append(dict(request=r,rate=rate,initial=initial,frames=frames))
 cancellations=[]
 for sprite in (0,17,18,26,30,31,32,33,37,40):
  for length in (0.,16.,16.125,32.,40.,128.,640.):
   for angle in (-3.15,0.,.125,1.57079637):
    for mode in (0,1,2):
     deliveries.clear();m.mem_write(obj,bytes(0x2000));put(obj+0x5b8,sprite);put(obj+0x614,7);put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x10,2);put(obj+0x5b4,3 if mode==2 else 0)
     result=call(0x43f8f0,(mode!=0,mode==2))
     cancellations.append(dict(sprite=sprite,length=bits(length),angle=bits(angle),mode=mode,result=result,state=get(obj+0x10),deliveries=deliveries[:]))
 circles=[];center=0x70009000
 for sprite in (0,18,31,40):
  for length in (0.,16.,16.125,32.,128.,640.):
   for angle in (-3.15,0.,.125,1.57079637):
    for radius in (0.,8.,32.,640.):
     for mode in (0,1,2):
      deliveries.clear();fragments.clear();cursor=0x70020000;m.mem_write(obj,bytes(0x2000));put(manager+0x5d0,obj);put(manager+0x5d4,1);put(manager+0x5d8,0x10000)
      put(obj+0x5b8,sprite);put(obj+0x610,sprite);put(obj+0x614,7);put(obj+0x5e0,bits(800));put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));put(obj+0x74,bits(24));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x5b4,3 if mode==2 else 0)
      m.mem_write(center,struct.pack('<3f',-140.25,7.5,0));result=call(0x43f220,(center,bits(radius),mode==1,mode==2))
      circles.append(dict(sprite=sprite,length=bits(length),angle=bits(angle),radius=bits(radius),mode=mode,result=result,newLength=get(obj+0x70),deliveries=deliveries[:],fragments=fragments[:]))
 rectangles=[];sizep=0x70009020
 for sprite in (0,18,31,40):
  for length in (0.,16.,16.125,32.,128.,640.):
   for angle in (-3.15,0.,.125,1.57079637):
    for variant in range(108):
     width,height=((0.,0.),(16.,16.),(80.,24.),(640.,1280.))[variant%4]
     rotation=(-.5,0.,.125)[(variant//4)%3];mode=(variant//12)%3;flags=variant%4;placement=(variant//36)%3
     deliveries.clear();fragments.clear();cursor=0x70020000;m.mem_write(obj,bytes(0x2000));put(manager+0x5d0,obj);put(manager+0x5d4,1);put(manager+0x5d8,0x10000)
     put(obj+0x5b8,sprite);put(obj+0x610,sprite);put(obj+0x614,7);put(obj+0x618,flags);put(obj+0x5e0,bits(800));put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));put(obj+0x74,bits(24));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x5b4,3 if mode==2 else 0)
     position=((-140.25,7.5,0),(-180.25,7.5,0),(900,-500,0))[placement];m.mem_write(center,struct.pack('<3f',*position));m.mem_write(sizep,struct.pack('<2f',width,height))
     result=call(0x43e500,(center,sizep,bits(rotation),mode==1,mode==2))
     rectangles.append(dict(sprite=sprite,length=bits(length),angle=bits(angle),width=bits(width),height=bits(height),rotation=bits(rotation),mode=mode,flags=flags,placement=placement,result=result,newLength=get(obj+0x70),deliveries=deliveries[:],fragments=fragments[:]))
 out=ROOT/'artifacts/th14/laser-infinite-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,cancellations=cancellations,circles=circles,rectangles=rectangles),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} initializations, {sum(len(r["frames"]) for r in rows)} lifecycle frames, {len(cancellations)} cancellations, {len(circles)} circle cuts, {len(rectangles)} rectangle cuts.')
if __name__=='__main__':main()
