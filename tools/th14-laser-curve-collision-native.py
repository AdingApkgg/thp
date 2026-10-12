"""Retail 440d80 kind-2 geometry, graze timer and rectangular-hit request.
Player collision/graze and rectangle consumer are recorded boundaries;
The rectangle consumer is a recorded boundary; the original code issues the request.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,player,stack=0x70000000,0x70001000,0x70004000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 words=lambda p,n:list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 deliveries=[];hit=0
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x44f0b0:
   deliveries.append([0,*words(get(sp+4),3),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,m.reg_read(UC_X86_REG_XMM3)&0xffffffff,get(sp+8),get(sp+12)])
   m.reg_write(UC_X86_REG_EAX,hit)
  elif a==0x450410:deliveries.append([1,*words(get(sp+4),3)])
  elif a==0x442a00:
   deliveries.append([2,*words(get(sp+4),3),*words(get(sp+8),2),get(sp+12),get(sp+16),get(sp+20)]);m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x44f0b0,12),(0x450410,4),(0x442a00,20),(0x46fe50,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4db67c,player);m.mem_write(player+0x5e0,struct.pack('<3f',17.25,120.5,3.25));rows=[];samples=0x70008000
 for count,width,angle,speed,rate,age,hit,probe in itertools.product((1,2,7,20),(0.,24.,64.),(-3.15,0.,.125),(0.,2.,8.,16.),(.5,1.,1.25),(0,1,3),(0,1,2),(0,1)):
  deliveries.clear();m.mem_write(obj,bytes(0x2000));put(obj,0x4be2fc);put(obj+0x5e0,count);put(obj+0x14ac,samples);put(obj+0x74,bits(width));m.mem_write(obj+0x2c,struct.pack('<5I',age-1&0xffffffff,age,bits(float(age)),0x4d8f58,1));put(0x4d8f58,bits(rate))
  initial=[]
  for j in range(count):
   row=list(map(bits,(-22.25+j*.75,40.5-j*.125,3.25+j*.25,0,0,0,angle,speed)));initial.append(row);m.mem_write(samples+j*32,struct.pack('<8I',*row))
  m.mem_write(stack-0x3000,bytes(0x3100));put(stack,end);put(stack+4,probe);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x440d80,end,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(initial=initial,width=bits(width),rate=rate,age=age,hit=hit,probe=probe,result=m.reg_read(UC_X86_REG_EAX),timer=words(obj+0x2c,3),deliveries=deliveries[:]))
 (ROOT/'artifacts/th14/laser-curve-collision-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} native kind-2 collision cases.')
if __name__=='__main__':main()
