"""Retail467940 font initialization; scratch DIB creation and GDI fonts controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 arena=0x70000000;m.mem_map(arena,0x10000);stack=arena+0xf000;font_call=arena+0x1000;m.mem_write(font_call,b'\xc3');m.mem_write(0x4b1038,struct.pack('<I',font_call))
 scratch=[];fonts=[];first_success=True
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x466860:scratch.append(get(sp+12));uc.reg_write(UC_X86_REG_EAX,first_success or len(scratch)>1);pop=12
  elif a==font_call:
   args=[get(sp+i*4) for i in range(1,14)];p=get(sp+56);face=bytearray()
   while m.mem_read(p,1)!=b'\0':face.extend(m.mem_read(p,1));p+=1
   fonts.append(dict(args=args,face=face.hex()));uc.reg_write(UC_X86_REG_EAX,len(fonts));pop=56
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook);m.mem_write(0x4f5815,b'\0');rows=[]
 for seed,calls,first_success in itertools.product((0,1,904,13971,65535),(0,97,0xffffff80),(False,True)):
  scratch.clear();fonts.clear();put(0x4db508,seed);put(0x4db50c,calls);m.mem_write(0x4d99e8,bytes([0xa5])*256);put(stack,arena);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x467940,arena,count=12000);assert m.reg_read(UC_X86_REG_EIP)==arena
  rows.append(dict(seed=seed,calls=calls,firstSuccess=first_success,noise=bytes(m.mem_read(0x4d99e8,256)).hex(),finalSeed=get(0x4db508)&65535,finalCalls=get(0x4db50c),scratchFormats=scratch[:],fonts=fonts[:]))
 (ROOT/'artifacts/th14/font-initialization-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} retail font initialization states')
if __name__=='__main__':main()
