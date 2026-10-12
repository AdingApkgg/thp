"""Retail hit callback 452e20 and its moving circle through 44e005.
Actual 450130 allocation, libm, movement, radius and clock updates run;
ANM interrupt, audio and memset are controlled delivery boundaries.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 end,obj,spec,old,player,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x70010000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 events=[]
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x48f980:m.mem_write(get(sp+4),bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x47f140:events.append(['interrupt',get(sp+4),get(sp+8)])
  else:events.append(['sound',get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
 for a,n in ((0x48f980,0),(0x47f140,8),(0x46e470,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 def fp():m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
 def area_state(a):
  return [get(a+o) for o in (0x10,0x14,0x18,0x1c,0x20,0x2c,0x30,0x34,0x60,0x64,0x68,0x44,0x48,0x4c,0x50,0x54,0x58,0x6c,0x70,0x74,0x78,0x84,0x88,0x8c,0x90,0x94,0xa0)]
 rows=[]
 for angle,rate,z,tail in itertools.product((-3.2,-3.1415927410125732,-1.25,0,3.1415927410125732,3.2),(0,.5,1,1.25),(-.5,0,.25),((17,31),(0xffffffff,0xfffffff0))):
  m.mem_write(obj,bytes(0x100));m.mem_write(spec,bytes(0x100));m.mem_write(old,bytes(0xa4));m.mem_write(player,bytes(0x19000));events.clear();put(0x4db67c,player);put(0x4d8f58,bits(rate))
  put(obj+0xbc,spec);put(obj+0xc0,old);put(obj+0x14,73);put(obj+0x98,1);put(obj+0xac,19);put(old+0x10,0x85);m.mem_write(spec+2,struct.pack('<h',22));put(spec+0x38,tail[0]);put(spec+0x3c,tail[1]);put(player+0x184b8,5678);put(player+0x184bc,1234)
  floats(obj+0x54,12.25,301.125,.1);floats(obj+0x6c,8,angle,7,.25,.125,1.5,0);floats(obj+0x88,-2,3,z);put(obj+0x94,0)
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);fp();m.emu_start(0x452e20,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  a=player+0xde18;result=[get(obj+0x98),get(obj+0x6c),get(old+0x10),int(get(obj+0xc0)!=0),get(player+0x184b8),get(player+0x184bc),m.reg_read(UC_X86_REG_EAX)];initial=area_state(a);frames=[]
  for i in range(24):
   put(stack+0x1c,1);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBX,a+0x78);m.reg_write(UC_X86_REG_EDI,player);m.reg_write(UC_X86_REG_EAX,1);fp();m.emu_start(0x44e005,0x44e0fa,count=100000);frames.append(area_state(a))
  rows.append(dict(args=[angle,rate,z,*tail],result=result,events=events[:],initial=initial,frames=frames))
 (ROOT/'artifacts/th14/shot-explosion-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} native explosive hits, {sum(len(r["frames"]) for r in rows)} moving-circle updates')
if __name__=='__main__':main()
