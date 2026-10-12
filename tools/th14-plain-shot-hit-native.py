"""Retail hit callbacks 452240/4538b0/453910 with full RNG; ANM and termination sinks."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 ret,obj,spec,player,effect,visual,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x70020000,0x70022000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 request=[];terminations=0
 def sink(machine,a,size,user):
  nonlocal terminations
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47ed10:
   p=get(sp+12);request.extend([get(sp+8),get(p),get(p+4),get(p+8),get(sp+16)]);put(get(sp+4),1);m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,effect)
  elif a==0x451820:terminations+=1;m.reg_write(UC_X86_REG_EAX,19)
 for a,n in ((0x47ed10,28),(0x47f0a0,4),(0x451820,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 rows=[]
 for callback,power,age,focus,seed,angle in itertools.product((2,5,7),(0,1,2,3,4),(-1,0,1,2,3,4,6,9,10),(0,1),(0,1,12345,65535),(-3.1415927410125732,-1.25,0,3.1415927410125732)):
  m.mem_write(obj,bytes(0x200));m.mem_write(spec,bytes(0x100));m.mem_write(player,bytes(0x19000));m.mem_write(effect,bytes(0x1000));m.mem_write(stack-0x1000,bytes(0x1100));request.clear();terminations=0
  for p,v in ((obj+0xbc,spec),(spec+0x38,17),(obj+0x10,focus*2),(obj+0x1c,age),(0x4db67c,player),(0x4db53c,visual),(visual+0x10,ret),(0x4f5858,power*40),(0x4f5860,40),(0x4db508,seed),(0x4db50c,123),(player+0x184b4,1234),(player+0x184b8,5678),(stack,ret)):put(p,v)
  m.mem_write(obj+0x54,struct.pack('<fff',12.25,301,.1));m.mem_write(obj+0x70,struct.pack('<f',angle));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start({2:0x452240,5:0x4538b0,7:0x453910}[callback],ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret and terminations==1
  rows.append(dict(input=[callback,power,age,focus,seed,angle],result=[get(player+0x184b4),get(player+0x184b8),get(0x4db508),get(0x4db50c),*request,get(effect+0x534)]))
 (ROOT/'artifacts/th14/plain-shot-hit-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} plain shot hit callbacks.')
if __name__=='__main__':main()
