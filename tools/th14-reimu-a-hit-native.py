"""Actual 414020 hit effect including its script RNG; unwritten polar z is controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,im.data[raw:raw+n])
 end,area,hit,effect,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 requests=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47ed10:requests.append([get(sp+8),*[get(get(sp+12)+i*4)for i in range(3)],get(sp+16)])
  if a==0x4144a0:put(m.reg_read(UC_X86_REG_ECX)+8,0)
 m.mem_write(0x47ed10,b'\xc2\x1c\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=0x47ed10,end=0x47ed10);m.hook_add(UC_HOOK_CODE,boundary,begin=0x4144a0,end=0x4144a0)
 rows=[]
 for seed,(x,y),damage in itertools.product((0,1,1337,65535),((0,0),(1,0),(0,1),(-1,-1),(.37,-.51),(100,-200)),(0,300,-20)):
  m.mem_write(end,bytes(0xf0000));requests.clear();floats(area+0x2c,12.25,300,3);floats(hit,12.25+x,300+y,4);put(area+0x84,damage);put(0x4db53c,effect);put(effect+0x10,effect+0x100);put(0x4db508,seed);put(0x4db50c,0);put(0x4db510,54321);put(0x4db514,77)
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,area);m.reg_write(UC_X86_REG_EDX,hit);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(0x414020,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end and len(requests)==1
  rows.append(dict(args=[seed,12.25,300,3,12.25+x,300+y,4,damage],result=[m.reg_read(UC_X86_REG_EAX),get(0x4db508)&65535,get(0x4db50c),get(0x4db510)&65535,get(0x4db514)],effect=requests[0]))
 (ROOT/'artifacts/th14/reimu-a-hit-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),controlledPolarScratchZ=0,rows=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} Reimu A hit callbacks.')
if __name__=='__main__':main()
