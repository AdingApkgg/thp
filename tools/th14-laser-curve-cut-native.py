"""Actual 4433d0 selection, truncation and delivery requests at reward/effect boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,samples,center,stack=0x70000000,0x70001000,0x70004000,0x70007000,0x7000f000;m.mem_map(end,0x1000000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 rewards=[];effects=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x41ae00:rewards.append([m.reg_read(UC_X86_REG_EDX),*words(m.reg_read(UC_X86_REG_ECX),3)])
  elif a==0x47ed10:effects.append([get(sp+8),*words(get(sp+12),3)])
  else:
   p,v,n=get(sp+4),get(sp+8),get(sp+12);m.mem_write(p,bytes([v&255])*n)
 for a,cleanup in ((0x41ae00,0),(0x47ed10,28),(0x48f980,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4db530,end+0x20000);rows=[]
 patterns=('0000000','1111111','1110000','0000111','0011100','0101010','1010101','0111001','0000010')
 for pattern in patterns:
  for radius in (0.,-3.5,3.5):
   for skip,protection in ((0,0),(1,0),(0,1),(1,1)):
    rewards.clear();effects.clear();m.mem_write(obj,bytes(0x2000));m.mem_write(stack-0x1000,bytes(0x1100));put(obj+0x14ac,samples);put(obj+0x5e0,len(pattern));put(obj+0x5b4,protection);put(obj+0x5dc,14)
    initial=[]
    for j,c in enumerate(pattern):
     row=list(map(bits,(12.25+(0 if c=='1' else 50),80.5,j*.125,j*.25,-j*.125,3.5,j*.0625,4+j*.25)));initial.append(row);m.mem_write(samples+j*32,struct.pack('<8I',*row))
    position=list(map(bits,(12.25,80.5,0)));m.mem_write(center,struct.pack('<3I',*position));put(stack,end)
    for j,v in enumerate((center,bits(radius),1,skip)):put(stack+4+j*4,v)
    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.emu_start(0x4433d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
    rows.append(dict(initial=initial,center=position,radius=bits(radius),skip=skip,protection=protection,count=m.reg_read(UC_X86_REG_EAX),flags=get(obj+0xc),samples=[words(samples+j*32,8) for j in range(get(obj+0x5e0))],rewards=rewards[:],effects=effects[:]))
 out=ROOT/'artifacts/th14/laser-curve-cut-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail curved-laser circle selections and truncations.')
if __name__=='__main__':main()
