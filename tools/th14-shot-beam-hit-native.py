"""Retail 452700 hit geometry and 41be50 effect interpolation setup."""
import hashlib,importlib,itertools,json,struct,math
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 end,obj,area,target,rect,vm,player,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x70004000,0x70005000,0x70010000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));events=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47f140:events.append(['interrupt',get(sp+8)])
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vm)
  else:
   pos=get(sp+12);events.append(['effect',get(sp+8),*[get(pos+i*4) for i in range(3)]]);put(get(sp+4),73)
 for a,n in ((0x47f140,8),(0x47f0a0,4),(0x47ed10,28),(0x4854a0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3')
  if a!=0x4854a0:m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4db67c,player);put(0x4d8f58,bits(1));floats(0x4f7afc,0,0,0)
 def call(a):
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_EDX,target);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
 rows=[]
 for kind,angle,distance,across,age,advanced in itertools.product((0,1),(-3.1415927410125732,-1.5707963705062866,-.37,0,.37,1.5707963705062866),(-8,0,8,100,400,1200),(-200,-8,0,8,200),(-4,-2,0,1,2,4,8),(0,1)):
  if not kind and abs(across)>8:continue
  for p,n in ((obj,0x100),(area,0x100),(vm,0x600),(player,0x19000)):m.mem_write(p,bytes(n))
  events.clear();put(obj+0x14,71);put(obj+0xc0,area);floats(obj+0x54,12.25,301.125,.1);put(obj+0x70,bits(angle));put(obj+0xb0,bits(512));put(obj+0xa8,age&1);put(obj+0x18,age-advanced);put(obj+0x1c,age);put(area+0x28,bits(12));put(area+0x24,bits(333));put(area+0x84,19);put(player+0x184b4,0xfffffffe)
  x=12.25+math.cos(angle)*distance-math.sin(angle)*across;y=301.125+math.sin(angle)*distance+math.cos(angle)*across
  floats(target,x,y,0);floats(rect,24,40);enemy_angle=(0,.37,-1.25)[age%3]
  put(stack,end);put(stack+4,rect if kind else 0);put(stack+8,bits(enemy_angle));put(stack+12,bits(10));call(0x452700)
  result=[get(obj+0xb0),get(area+0x24),get(obj+0xa4),get(obj+0xa8),get(player+0x184b4),m.reg_read(UC_X86_REG_EAX)]
  effect=[]
  if any(e[0]=='effect' for e in events):effect=[get(vm+o) for o in (0x18,0x50,0xec,0xf0,0x9c,0xa0,0xa4,0xa8,0xac,0xb0,0xb4,0xb8,0xbc,0xc0,0xc4,0xc8,0xd8,0xdc,0xe0)]
  rows.append(dict(args=[kind,angle,distance,across,age,advanced,x,y,enemy_angle],result=result,events=events[:],effect=effect))
 edges=[]
 capture=json.loads((ROOT/'artifacts/th14/native-beam-fallback-oct10.json').read_text(encoding='utf-8'))
 for r in capture['beamFallbacks']:
  for age,advanced,scratch in itertools.product((-4,-2,0,1,2,4,8,1411),(0,1),(-8.,-131.4933624267578,-10000.)):
   for p,n in ((obj,0x100),(area,0x100),(vm,0x600),(player,0x19000)):m.mem_write(p,bytes(n))
   events.clear();put(obj+0x14,71);put(obj+0xc0,area);floats(obj+0x54,*r['origin']);put(obj+0x70,bits(r['angle']));put(obj+0xb0,bits(r['size'][0]));put(obj+0xa8,age&1);put(obj+0x18,age-advanced);put(obj+0x1c,age)
   floats(area+0x24,*r['size']);put(area+0x84,19);put(player+0x184b4,0xfffffffe);floats(target,*r['target'])
   put(stack,end);put(stack+4,0);put(stack+8,0);put(stack+12,bits(r['radius']));put(stack-36,bits(scratch));call(0x452700)
   result=[get(obj+0xb0),get(area+0x24),get(obj+0xa4),get(obj+0xa8),get(player+0x184b4),m.reg_read(UC_X86_REG_EAX)]
   edges.append(dict(args=[*r['origin'][:2],r['angle'],*r['size'],*r['target'][:2],r['radius'],age,advanced],scratch=scratch,result=result,events=events[:]))
 (ROOT/'artifacts/th14/shot-beam-hit-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,edges=edges),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} beam hits / {len(edges)} measured negative-scratch edge cases')
if __name__=='__main__':main()
