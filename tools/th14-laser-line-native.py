"""TH14 kind-0 retail state/motion and full cancel; ANM/sound/items are boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,request,manager,resource,effect,stack=0x70000000,0x70001000,0x70004000,0x70005000,0x70010000,0x70011000,0x700ff000;m.mem_map(end,0x100000)
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
   if get(sp+4)==effect:effect_script=get(sp+8)
  elif a==0x47fcb0:m.mem_write(effect,bytes(0x5cc))
  elif a==0x46fe50 and vm==effect:deliveries.append([effect_script,*words(effect+0x59c,3)])
  elif a==0x47ed10:deliveries.append([get(sp+8),*words(get(sp+12),3)])
  elif a==0x41ae00:
   reward=m.reg_read(UC_X86_REG_EDX)
   if reward:deliveries.append([0x10000+reward,*words(vm,3)])
  elif a==0x4854af:
   n=get(sp+4);m.mem_write(cursor,bytes(n));m.reg_write(UC_X86_REG_EAX,cursor);cursor+=(n+15)&~15;return
  elif a==0x43aca0:fragments.append(words(get(sp+4),213))
  m.reg_write(UC_X86_REG_EAX,effect if a==0x47fcb0 else 0)
 for a,cleanup in ((0x40cc90,0),(0x40d0c0,0),(0x46f520,8),(0x40af00,8),(0x46fe50,0),(0x46e470,4),(0x47fcb0,0),(0x47e890,8),(0x47ed10,28),(0x41ae00,0),(0x4854af,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def call(a,args=(),stop=None,owner=None):
  m.mem_write(stack-0x3000,bytes(0x3100));put(stack,end)
  for j,v in enumerate(args):put(stack+4+4*j,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj if owner is None else owner);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(a,stop or end,count=1000000)
  assert m.reg_read(UC_X86_REG_EIP) in (stop,end),hex(m.reg_read(UC_X86_REG_EIP))
  return m.reg_read(UC_X86_REG_EAX) if m.reg_read(UC_X86_REG_EIP)==end else 0
 fields=(0x10,0x14,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0x74,0x78,0x7c,0x594,0x598,0x5b4,0x5a0,0x5a4,0x5a8,0x2c,0x30,0x34,0x40,0x44,0x48,0x18,0x1c,0x20,0x5d0,0x80)
 def state():return [get(obj+o) for o in fields]+[get(obj+0x92c)&0x1e0]
 put(0x4db664,manager);put(manager+0x5f4,resource);put(0x4f5815,0)
 bullet_owner=0x71000000;m.mem_map(bullet_owner,0x9c0000);put(0x4db530,bullet_owner);put(bullet_owner+0x9bf6cc,resource)
 rows=[]
 for variant in range(48):
  for rate in (0.,.5,1.,1.25):
   r=[0]*(0x354//4);r[:3]=list(map(bits,((-220.,-192.,-22.25,192.)[variant%4],(-40.,0.,40.5,448.)[(variant//4)%4],3.25)))
   r[3:9]=list(map(bits,((-200.,-.125,3.15,200.)[variant%4],(0.,16.,100.,640.)[(variant//4)%4],(0.,8.,100.)[(variant//16)%3],(-1.,0.,128.,800.)[variant%4],(0.,3.,24.,64.)[variant%4],(-1.,0.,.25,8.)[(variant//4)%4])))
   r[9:13]=[variant%43,variant%16,bits((0.,7.25)[variant%2]),0xffffffff];r[-2:]=[0xffffffff,0xffffffff]
   if variant%3:
    program=[(0x80,7),(0x100000,variant%2),(0x8000,0x12345678),(0x400,0),(0x800,17)]
    if variant%3==2:program=[(0x10000,2),(4,60),*program]
    for j,(op,param) in enumerate(program):r[13+j*11+4]=param;r[13+j*11+8]=op;r[13+j*11+9]=1
   m.mem_write(obj,bytes(0x2000));m.mem_write(request,struct.pack('<213I',*r));put(0x4d8f58,bits(rate));call(0x43a8a0);call(0x43aca0,(request,));initial=state();frames=[]
   for frame in range(100):
    result=call(0x43be20,stop=0x43c179)
    if not result:call(0x408690,owner=obj+0x18)
    frames.append(dict(result=result,state=state()))
    if result:break
   rows.append(dict(request=r,rate=rate,initial=initial,frames=frames))
 cancellations=[]
 for sprite in (0,17,18,26,30,31,32,33,37,40):
  for length in (0.,16.,16.125,32.,40.,128.,640.):
   for angle in (-3.15,0.,.125,1.57079637):
    for mode in (0,1,2):
     deliveries.clear();m.mem_write(obj,bytes(0x2000));put(obj+0x5b8,sprite);put(obj+0x5e8,7);put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x10,2);put(obj+0x5b4,3 if mode==2 else 0)
     result=call(0x43da10,(mode!=0,mode==2));cancellations.append(dict(sprite=sprite,length=bits(length),angle=bits(angle),mode=mode,result=result,state=get(obj+0x10),deliveries=deliveries[:]))
 circles=[];rectangles=[];center=0x70009000;sizep=0x70009020
 m.mem_write(0x43aca0,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=0x43aca0,end=0x43aca0)
 for sprite in (0,18,31,40):
  for length in (0.,16.,16.125,32.,40.,128.,640.):
   for angle in (-3.15,0.,.125,1.57079637):
    for radius in (0.,8.,32.,640.):
     for mode in (0,1,2):
      deliveries.clear();fragments.clear();cursor=0x70020000;m.mem_write(obj,bytes(0x2000));put(manager+0x5d0,obj);put(manager+0x5d4,1);put(manager+0x5d8,0x10000)
      r=[(j*0x12345)&0xffffffff for j in range(213)];r[:3]=list(map(bits,(-180.25,7.5,3.25)));r[3:9]=[bits(angle),bits(800.),bits(length),bits(900.),bits(24.),bits(8.)];r[9:13]=[sprite,7,0,0];r[-2:]=[0xffffffff,0xffffffff]
      m.mem_write(obj+0x5c0,struct.pack('<213I',*r));put(obj+0x5b8,sprite);put(obj+0x5bc,7);put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));put(obj+0x74,bits(24));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x5b4,3 if mode==2 else 0)
      m.mem_write(center,struct.pack('<3f',-140.25,7.5,0));result=call(0x43d300,(center,bits(radius),mode==1,mode==2))
      circles.append(dict(request=r,radius=bits(radius),mode=mode,result=result,state=[get(obj+o) for o in (0xc,0x54,0x58,0x5c,0x70,0x7c,0x5d0)],deliveries=deliveries[:],fragments=fragments[:]))
      for rotation in (0.,.125,1.57079637):
       deliveries.clear();fragments.clear();cursor=0x70020000;m.mem_write(obj,bytes(0x2000));put(manager+0x5d0,obj);put(manager+0x5d4,1);put(manager+0x5d8,0x10000)
       m.mem_write(obj+0x5c0,struct.pack('<213I',*r));put(obj+0x5b8,sprite);put(obj+0x5bc,7);put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));put(obj+0x74,bits(24));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x5b4,3 if mode==2 else 0)
       dimensions=list(map(bits,(radius*2,radius)));m.mem_write(sizep,struct.pack('<2I',*dimensions));result=call(0x43c500,(center,sizep,bits(rotation),mode==1,mode==2))
       rectangles.append(dict(request=r,size=dimensions,angle=bits(rotation),mode=mode,result=result,state=[get(obj+o) for o in (0xc,0x54,0x58,0x5c,0x70,0x7c,0x5d0)],deliveries=deliveries[:],fragments=fragments[:]))
 out=ROOT/'artifacts/th14/laser-line-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,cancellations=cancellations,circles=circles,rectangles=rectangles),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} initializations, {sum(len(r["frames"]) for r in rows)} lifecycle frames, {len(cancellations)} cancellations.')
if __name__=='__main__':main()
