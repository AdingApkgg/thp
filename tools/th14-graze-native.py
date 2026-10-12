"""Retail 450410 counters, effect and sound delivery; two factory boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,player,effect,contact,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x7000f000;m.mem_map(end,0x10000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 events=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47ed10:events.extend([get(sp+8),*words(get(sp+12),3)])
  else:events.append(get(sp+4));assert m.reg_read(UC_X86_REG_XMM2)&0xffffffff==get(contact)
 for a,cleanup in ((0x47ed10,28),(0x46e470,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4db67c,player);put(0x4db53c,effect);rows=[]
 for graze in (-2147483648,-1,0,99999998,99999999,2147483647):
  for point in (-2147483648,-100,0,999999,2147483640):
   for maximum in (-1,0,1000000,2147483647):
    for p,c in (((0,400,0),(12.25,400,3)),((-12.5,0,0),(48.75,-0.,-3)),((1e10,-1e10,2),(-1e10,1e10,7))):
     events.clear();m.mem_write(stack-0x1000,bytes(0x1100))
     for a,v in ((0x4f5840,graze),(0x4f584c,point),(0x4f5854,maximum)):put(a,v)
     for j,v in enumerate(p):put(player+0x5e0+j*4,bits(v))
     for j,v in enumerate(c):put(contact+j*4,bits(v))
     put(stack,end);put(stack+4,contact);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
     m.emu_start(0x450410,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
     rows.append(dict(input=[graze,point,maximum,*map(bits,p),*map(bits,c)],result=[get(0x4f5840),get(0x4f584c),*events]))
 out=ROOT/'artifacts/th14/graze-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail graze reward/effect/sound cases.')
if __name__=='__main__':main()
