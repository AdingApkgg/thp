"""Own434730 circles/433860 rectangles and complete358-byte fragments.
Effects/rewards, registration ledger, ANM and fragment initialization are sinks.
The actual kind0 constructor and fragment allocation/linking execute.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
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
  if a in (0x4090f0,0x4093f0):m.mem_write(vm,bytes(0x5fc))
  elif a in (0x45f160,0x407b20):
   if get(sp+4)==effect:effect_script=get(sp+8)
  elif a==0x46f600:m.mem_write(effect,bytes(0x5fc))
  elif a==0x45f980 and vm==effect:deliveries.append([effect_script,*words(effect+0x5e0,3)])
  elif a==0x40e5c0:
   deliveries.append([get(sp+8),*words(get(sp+12),3)]);put(get(sp+4),123);m.reg_write(UC_X86_REG_EAX,get(sp+4));return
  elif a==0x416a00:
   reward=m.reg_read(UC_X86_REG_EDX)
   if reward:deliveries.append([0x10000+reward,*words(vm,3)])
  elif a==0x4749ac:
   n=get(sp+4);m.mem_write(cursor,bytes(n));m.reg_write(UC_X86_REG_EAX,cursor);cursor+=(n+15)&~15;return
  elif a==0x431b30:fragments.append(words(get(sp+4),214))
  m.reg_write(UC_X86_REG_EAX,effect if a==0x46f600 else 0)
 for a,cleanup in ((0x4090f0,0),(0x4093f0,0),(0x45f160,8),(0x407b20,8),(0x45f980,0),(0x45e1f0,4),(0x46f600,0),(0x46e7d0,8),(0x40e5c0,24),(0x416a00,0),(0x4749ac,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def call(a,args=(),stop=None,owner=None):
  m.mem_write(stack-0x3000,bytes(0x3100));put(stack,end)
  for j,v in enumerate(args):put(stack+4+4*j,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj if owner is None else owner);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(a,stop or end,count=1000000)
  assert m.reg_read(UC_X86_REG_EIP) in (stop,end),hex(m.reg_read(UC_X86_REG_EIP))
  return m.reg_read(UC_X86_REG_EAX) if m.reg_read(UC_X86_REG_EIP)==end else 0
 m.mem_write(0x47499b,b'\xc3');m.mem_write(0x41aa00,b'\xc2\x04\x00');m.mem_write(0x40e6c0,b'\xb8\xff\xff\xff\xff\xc3');put(0x4a6ee0,manager);put(manager+0x604,resource);put(0x4c10b6,0)
 bullet_owner=0x71000000;m.mem_map(bullet_owner,0x1410000);put(0x4a6dac,bullet_owner);put(bullet_owner+0x1403b24,resource)
 circles=[];rectangles=[];center=0x70009000;sizep=0x70009020
 m.mem_write(0x431b30,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=0x431b30,end=0x431b30)
 for sprite in (0,18,31,40):
  for length in (0.,16.,16.125,32.,40.,128.,640.):
   for angle in (-3.15,0.,.125,1.57079637):
    for radius in (0.,8.,32.,640.):
     for mode in (0,1,2):
      deliveries.clear();fragments.clear();cursor=0x70020000;m.mem_write(obj,bytes(0x2000));put(manager+0x5e0,obj);put(manager+0x5e4,1);put(manager+0x5e8,0x10000)
      r=[(j*0x12345)&0xffffffff for j in range(214)];r[:3]=list(map(bits,(-180.25,7.5,3.25)));r[3:9]=[bits(angle),bits(800.),bits(length),bits(900.),bits(24.),bits(8.)];r[9:13]=[sprite,7,0,0];r[-2:]=[0xffffffff,0xffffffff]
      m.mem_write(obj+0x5d4,struct.pack('<214I',*r));put(obj+0x5cc,sprite);put(obj+0x5d0,7);put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));put(obj+0x74,bits(24));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x5c8,3 if mode==2 else 0)
      m.mem_write(center,struct.pack('<3f',-140.25,7.5,0));result=call(0x434730,(center,bits(radius),mode==1,mode==2))
      circles.append(dict(request=r,radius=bits(radius),mode=mode,result=result,state=[get(obj+o) for o in (0xc,0x54,0x58,0x5c,0x70,0x7c,0x5e4)],deliveries=deliveries[:],fragments=fragments[:]))
      for rotation in (0.,.125,1.57079637):
       deliveries.clear();fragments.clear();cursor=0x70020000;m.mem_write(obj,bytes(0x2000));put(manager+0x5e0,obj);put(manager+0x5e4,1);put(manager+0x5e8,0x10000)
       m.mem_write(obj+0x5d4,struct.pack('<214I',*r));put(obj+0x5cc,sprite);put(obj+0x5d0,7);put(obj+0x6c,bits(angle));put(obj+0x70,bits(length));put(obj+0x74,bits(24));m.mem_write(obj+0x54,struct.pack('<3f',-180.25,7.5,3.25));put(obj+0x5c8,3 if mode==2 else 0)
       dimensions=list(map(bits,(radius*2,radius)));m.mem_write(sizep,struct.pack('<2I',*dimensions));result=call(0x433860,(center,sizep,bits(rotation),mode==1,mode==2))
       rectangles.append(dict(request=r,size=dimensions,angle=bits(rotation),mode=mode,result=result,state=[get(obj+o) for o in (0xc,0x54,0x58,0x5c,0x70,0x7c,0x5e4)],deliveries=deliveries[:],fragments=fragments[:]))
 out=ROOT/'artifacts/th16/laser-cut-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),circles=circles,rectangles=rectangles),indent=2)+'\n',encoding='utf-8')
 print(f'{len(circles)} own circles, {len(rectangles)} own rectangles')
if __name__=='__main__':main()
