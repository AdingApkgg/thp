"""Complete retail4339c0 panel-follow callback and4352b0 parent transform."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x20000);dialogue=base;panel=base+0x2000;child=base+0x3000;line=base+0x4000;stack=base+0x1e000;end=base+0x1f000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,panel if get(sp+4)==200 else 0);pop=4
  elif a==0x4854a0:pop=0
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x47f0a0,0x4854a0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[]
 for speaker,layout,display,sx,sample in itertools.product(range(3),range(16),(1.,1.5,2.),(0.,.375,1.,1.25),range(3)):
  for p in (dialogue,panel,child,line):m.mem_write(p,bytes(0x700))
  put(dialogue+0x6c,200);put(dialogue+0x190,speaker);put(dialogue+0x1b4,layout);put(panel+0x580,panel);put(panel+0x584,child+0x580);put(child+0x580,child);m.mem_write(child+0x4aa,struct.pack('<h',168+layout))
  put(panel+0x1c,0x100000);put(child+0x1c,0x100000);put(child+0x594,panel);floats(panel+0x59c,(224+sample*.25,288-sample*3.75,0.));floats(panel+0x3c,(-48.,-2.,0.));floats(panel+0x4ec,(0.,0.,0.));floats(child+0x59c,(0.,0.,0.));floats(child+0x3c,(96.,sample*.125,.25));floats(child+0x4ec,(sample*.5,2.,.125));floats(child+0x60,(sx,1.));floats(0x4f7a6c,(display,))
  put(stack,end);put(stack+4,line);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,dialogue);m.emu_start(0x4339c0,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(input=[speaker,layout,display,sx,sample],position=[get(line+0x59c+i*4) for i in range(3)]))
 (ROOT/'artifacts/th14/dialogue-position-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n');print('PASS native callback',len(rows))
if __name__=='__main__':main()
