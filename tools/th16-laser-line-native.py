"""Own TH16 kind0 state/motion, collision requests, and full cancellation.

ANM allocation/binding/update, sound, player probe/hit, effects/rewards are
recorded boundaries. Native polar/math and all selected clocks execute.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,request,manager,resource,effect,player,stack=[0x70000000+n for n in (0,0x1000,0x4000,0x5000,0x10000,0x11000,0x12000,0xff000)];m.mem_map(end,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 deliveries=[];effect_script=0;hit=0
 def boundary(machine,a,size,user):
  nonlocal effect_script
  sp=m.reg_read(UC_X86_REG_ESP);vm=m.reg_read(UC_X86_REG_ECX)
  if a in (0x4090f0,0x4093f0):m.mem_write(vm,bytes(0x5fc))
  elif a in (0x45f160,0x407b20):
   if get(sp+4)==effect:effect_script=get(sp+8)
  elif a==0x46f600:m.mem_write(effect,bytes(0x5fc))
  elif a==0x45f980 and vm==effect:deliveries.append([effect_script,*words(effect+0x5e0,3)])
  elif a==0x40e5c0:
   p=get(sp+12);deliveries.append([get(sp+8),*words(p,3)]);put(get(sp+4),123);m.reg_write(UC_X86_REG_EAX,get(sp+4));return
  elif a==0x416a00:
   reward=m.reg_read(UC_X86_REG_EDX)
   if reward:deliveries.append([0x10000+reward,*words(vm,3)])
  m.reg_write(UC_X86_REG_EAX,effect if a==0x46f600 else 0)
 for a,cleanup in ((0x4090f0,0),(0x4093f0,0),(0x45f160,8),(0x407b20,8),(0x45f980,0),(0x45e1f0,4),(0x45e150,8),(0x46f600,0),(0x46e7d0,8),(0x40e5c0,24),(0x416a00,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 m.mem_write(0x47499b,b'\xc3')
 def call(a,args=(),stop=None,owner=None):
  m.mem_write(stack-0x4000,bytes(0x4100));put(stack,end)
  for j,v in enumerate(args):put(stack+4+4*j,v)
  for reg,v in [(UC_X86_REG_ESP,stack),(UC_X86_REG_ECX,obj if owner is None else owner),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,v)
  m.emu_start(a,stop or end,count=1000000)
  assert m.reg_read(UC_X86_REG_EIP) in (stop,end),hex(m.reg_read(UC_X86_REG_EIP))
  return m.reg_read(UC_X86_REG_EAX) if m.reg_read(UC_X86_REG_EIP)==end else 0
 fields=(0x10,0x14,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0x74,0x78,0x7c,0x594,0x598,0x5c8,0x5a0,0x5a4,0x5a8,0x2c,0x30,0x34,0x40,0x44,0x48,0x18,0x1c,0x20,0x5e4,0x80,0x5b4,0x5b8,0x5bc,0x1ec,0x1f0,0x1f4,0xcc,0xd0,0xd4,0xe0,0xe4,0xf4,0xf8,0xfc,0x100,0x15c,0x160,0x164,0x170,0x174,0x190,0x194,0x198,0x19c)
 def state():return [get(obj+o) for o in fields]+[get(obj+0xe5c)&0x1e0]
 put(0x4a6ee0,manager);put(manager+0x604,resource);put(0x4a6ef8,player);put(0x4c10b6,0)
 # Cancel effect resource is normally reached through the bullet manager.
 bullet_owner=0x71000000;m.mem_map(bullet_owner,0x1410000);put(0x4a6dac,bullet_owner);put(bullet_owner+0x1403b24,resource)
 rows=[]
 def set_transform(r,j,op,p=0,q=0,mode=0,a=0,b=0,concurrent=1):
  n=14+j*11;r[n]=bits(a);r[n+1]=bits(b);r[n+4]=p&0xffffffff;r[n+5]=q&0xffffffff;r[n+6]=mode&0xffffffff;r[n+8]=op;r[n+9]=concurrent
 for variant in range(64):
  for rate in (0.,.5,1.,1.25):
   r=[0]*214;r[:3]=list(map(bits,((-220.,-192.,-22.25,192.)[variant%4],(-40.,0.,40.5,448.)[(variant//4)%4],3.25)))
   r[3:9]=list(map(bits,((-3.15,-.125,0.,200.)[variant%4],(0.,16.,100.,640.)[(variant//4)%4],(0.,8.,100.,640.)[(variant//16)%4],(-1.,0.,128.,800.)[variant%4],(0.,3.,24.,64.)[variant%4],(-1.,0.,.25,8.)[(variant//4)%4])))
   r[9:14]=[variant%44,variant%16,bits((0.,7.25)[variant%2]),0,1];r[-2:]=[0xffffffff,0xffffffff]
   kind=variant%8
   if kind==1:
    for j,(op,p) in enumerate(((0x80,7),(0x100,4),(0x100000,variant%2),(0x8000,0x12345678),(0x400,0),(0x800,17))):set_transform(r,j,op,p)
   elif kind==2:
    set_transform(r,0,4,p=12,a=.25,b=-999999);set_transform(r,1,0x80000000,p=3,concurrent=0);set_transform(r,2,0x100000,p=0,concurrent=0)
   elif kind==3:
    set_transform(r,0,16,p=4,q=3,a=.125,b=2);set_transform(r,1,0x8000,p=234,concurrent=0)
   elif kind==4:
    set_transform(r,0,0x80000000,p=4);set_transform(r,1,0x80,p=2,concurrent=0);set_transform(r,2,4,p=3,a=-.125,b=.5)
   elif kind==5:
    set_transform(r,0,1);set_transform(r,1,8,p=6,a=.1,b=.5);set_transform(r,2,0x1000,p=2)
   elif kind==6:
    set_transform(r,0,0x10000,p=2);set_transform(r,1,0x2000);set_transform(r,2,0x100,p=-1);set_transform(r,3,16,p=4,q=3,mode=1,a=.125,b=-999999)
   elif kind==7:
    r[12]=1;set_transform(r,0,0x2000);set_transform(r,1,4,p=0,a=1,b=.5);set_transform(r,2,16,p=0,q=1,a=.5,b=2,concurrent=0)
   m.mem_write(obj,bytes(0x2000));put(obj,0x492424);m.mem_write(request,struct.pack('<214I',*r));put(0x4a5788,bits(rate));put(obj+0x18,0xffffffff);put(obj+0x28,1)
   call(0x431b30,(request,));initial=state();frames=[]
   for frame in range(100):
    result=call(0x432f40,stop=0x4333ae)
    if not result:call(0x406190,(0,),owner=obj+0x40);call(0x406190,(0,),owner=obj+0x18)
    frames.append(dict(result=result,state=state()))
    if result:break
   rows.append(dict(request=r,rate=rate,initial=initial,frames=frames))
 cancellations=[]
 for sprite in (0,17,18,27,31,32,33,34,38,43):
  for length in (0.,16.,16.125,32.,40.,128.,640.):
   for angle in (-3.15,0.,.125,1.57079637):
    for mode in (0,1,2):
     deliveries.clear();m.mem_write(obj,bytes(0x2000));put(obj+0x5cc,sprite);put(obj+0x5fc,7);put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x10,2);put(obj+0x5c8,3 if mode==2 else 0)
     result=call(0x434cd0,(mode!=0,mode==2));cancellations.append(dict(sprite=sprite,length=bits(length),angle=bits(angle),mode=mode,result=result,state=get(obj+0x10),deliveries=deliveries[:]))
 # Own433510 executes native polar/projection; downstream consumers are sinks.
 collisions=[];events=[]
 def collision_boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x443af0:events.append([0,*words(get(sp+4),3),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,m.reg_read(UC_X86_REG_XMM3)&0xffffffff,get(sp+8),get(sp+12)]);m.reg_write(UC_X86_REG_EAX,hit)
  elif a==0x444cf0:events.append([1,*words(get(sp+4),3)])
  elif a==0x433860:events.append([2,*words(get(sp+4),3),*words(get(sp+8),2),get(sp+12),get(sp+16),get(sp+20)])
 for a,cleanup in ((0x443af0,12),(0x444cf0,4),(0x433860,20)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,collision_boundary,begin=a,end=a)
 for variant in range(48):
  for rate in (.5,1.,1.25):
   for age in (0,1,3):
    for hit in (0,1,2):
     events.clear();m.mem_write(obj,bytes(0x2000));put(obj,0x492424);length=(0,16,16.125,128)[variant%4];width=(3,3.125,24,32)[variant%4];angle=(-3.15,-.125,0,.5,1.57079637,200)[(variant//4)%6];flags=2 if variant>=24 else 0
     m.mem_write(obj+0x54,struct.pack('<3f',-22.25,40.5,3.25));put(obj+0x70,bits(length));put(obj+0x74,bits(width));put(obj+0x6c,bits(angle));put(obj+0x608,flags);put(0x4a5788,bits(rate));m.mem_write(player+0x610,struct.pack('<3f',17.25,120.5,3.25));call(0x406490,(age,),owner=obj+0x2c)
     result=call(0x433510,(variant%2,));collisions.append(dict(input=[bits(length),bits(width),bits(angle),rate,age,hit,variant%2,flags],result=result,timer=words(obj+0x2c,3),events=events[:]))
 out=ROOT/'artifacts/th16/laser-line-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,cancellations=cancellations,collisions=collisions),separators=(',',':'))+'\n',encoding='utf-8')
 print(f'{len(rows)} own TH16 initializations, {sum(len(r["frames"]) for r in rows)} motion frames, {len(cancellations)} cancellations, {len(collisions)} collision cases')
if __name__=='__main__':main()
