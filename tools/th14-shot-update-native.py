"""Retail 4510b0 with actual motion, quad query, bounds and clock.
ANM lookup/release and security cookie are controlled boundaries. Callback zero,
motion mode zero, no extra VM. Display origin is controlled, not inferred.
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
 end,obj,spec,player,vm,area,stack=0x70000000,0x70001000,0x70002000,0x70010000,0x70040000,0x70042000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));present=True
 def boundary(machine,a,size,user):
  if a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vm if present else 0)
  elif a==0x47f6e0:put(m.reg_read(UC_X86_REG_ECX),0);put(vm+0x1c,get(vm+0x1c)|0x20)
 for a,n in ((0x47f0a0,4),(0x47f6e0,0),(0x4854a0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n)if n else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 rows=[]
 for kind,flags,age,rate,present,hint,x,callback,state in itertools.product((0,2,3,5),(0,1,3,0x3d),(0,9,10,22),(0.,.5,1.,1.25),(False,True),(0,1),(-220.125,-192.,-180.,0.,180.,220.125),(0,1,8),(1,2)):
  m.mem_write(end,bytes(0xf0000))
  for p,v in ((0x4db67c,player),(obj+0x98,1),(obj+0xbc,spec),(obj+0x10,flags),(obj+0x14,73),(obj+0xc0,area),(obj+0xac,19),(obj+0x18,age-1),(obj+0x1c,age),(obj+0x24,0x4d8f58),(obj+0x28,0x81),(area+0x10,0x81),(area+0x84,7),(vm+0x18,2),(vm+0x1c,0x20200|(0x40 if hint else 0)),(player+0x1834c,3),(player+0x18350,2),(0x4f7a70,128),(0x4f7a74,16),(0x4f7a88,320),(0x4f7a8c,16),(0x4f7a80,320),(0x4f7a84,16)):put(p,v)
  enemy_manager,enemy=0x70050000,0x70060000
  put(obj+0x98,state);put(spec+0x2c,{0:0,1:0x4518d0,8:0x4538f0}[callback]);put(spec+0x38,10);put(0x4db544,enemy_manager);put(enemy_manager+0xd0,enemy+0x14d8);put(enemy+0x14d8,enemy);put(enemy+0x11e4,73);floats(enemy+0x1234,100,200,0)
  floats(0x4f7a6c,1);floats(0x4d8f58,rate);floats(obj+0x20,age+.375);floats(obj+0x54,x,80.125,3);floats(obj+0x6c,8.125,-2.37);floats(obj+0x88,99,88,1.5);floats(obj+0xb0,24,40)
  m.mem_write(spec+0x21,struct.pack('<b',kind));floats(vm+0x59c,x,80.125,3);floats(vm+0x3c,.125,3.25,0);floats(vm+0x60,1,1,1,1);floats(vm+0x80,24,40);floats(vm+0x50,.37)
  floats(area+0x1c,.61);floats(area+0x24,12,15,-11,-12,7)
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(0x4510b0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  result=[get(obj+n)for n in (0x98,0x10,0x14,0x18,0x1c,0x20,0x28,0x54,0x58,0x5c,0x6c,0x70,0x88,0x8c,0x90)]+[get(vm+n)for n in (0x18,0x1c,0x50,0x59c,0x5a0,0x5a4)]+[get(area+n)for n in (0x10,0x1c,0x24,0x28,0x2c,0x30,0x34,0x84)]+[get(player+0x1834c),get(player+0x18350)]
  result[2]=int(result[2]!=0) # Normalized registry ID, not a pointer/ID equality claim.
  rows.append(dict(args=[kind,flags,age,rate,int(present),hint,x,callback,state],result=result,retired=m.reg_read(UC_X86_REG_EAX)!=0))
 (ROOT/'artifacts/th14/shot-update-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} retail common shot updates.')
if __name__=='__main__':main()
