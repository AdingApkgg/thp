"""Retail 410470 STD marker search; no helper replacement."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,stage,script,other,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x7000f000;m.mem_map(end,0x10000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 put(0x4db528,stage);rows=[]
 for variant in range(4):
  commands=[(10,16,7),(300,0,0),(700,16,2),(900,0,0),(1100,16,2),(1200,0,0),(-1,0,0)]
  if variant==1:commands[0]=(-1,16,7)
  if variant==2:commands[3]=(-1,0,0)
  if variant==3:commands[1]=(16777217,0,0)
  raw=b'';entries=[]
  for time,op,arg in commands:
   size=12 if op==16 else 8;entries.append(dict(time=time,opcode=op,offset=len(raw),argument=arg));raw+=struct.pack('<ihh',time,op,size)+(struct.pack('<i',arg) if op==16 else b'')
  m.mem_write(script,raw)
  for marker in (-2147483648,-1,0,2,7,2147483647):
   for flags in (0,1,2,3,0xa5a5a5a5,0xffffffff):
    for pointer in (0,other,0x4d8f58):
     m.mem_write(stage,bytes(0x100));put(stage+0x1c,script);put(stage+0x4c,script+0x777)
     for offset,value in ((0x38,123),(0x3c,456),(0x40,bits(789.25)),(0x44,pointer),(0x48,flags)):put(stage+offset,value)
     put(stack,end);put(stack+4,marker);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(0x410470,end,count=1000);assert m.reg_read(UC_X86_REG_EIP)==end
     p=get(stage+0x44);rows.append(dict(variant=variant,commands=entries,marker=marker,flags=flags,pointer=0 if pointer==0 else 1 if pointer==other else 2,result=[get(stage+0x4c)-script,get(stage+0x38),get(stage+0x3c),get(stage+0x40),get(stage+0x48),0 if p==0 else 1 if p==other else 2]))
 out=ROOT/'artifacts/th14/stage-interrupt-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} retail STD interrupt cases.')
if __name__=='__main__':main()
