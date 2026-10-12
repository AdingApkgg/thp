"""Whole425240/41a980/41b540 with real linked-list traversal, no helper hooks."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x100000);manager,base,nodes,pos,out,stack,ret=0x70001000,0x70010000,0x70080000,0x70081000,0x70082000,0x700ff000,0x700fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def call(address,args=(),ecx=0):
  put(stack,ret)
  for i,v in enumerate(args):put(stack+4+i*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.emu_start(address,ret,count=20000);assert m.reg_read(UC_X86_REG_EIP)==ret;return m.reg_read(UC_X86_REG_EAX)
 put(0x4a6dc0,manager);cases=[]
 for n in range(2048):
  count=n%9;radius=(0,1,16,256,-16,1024)[(n//9)%6];point=((0,0),(7.25,300.5),(-192,448),(100000,100000))[(n//54)%4]
  entries=[]
  for i in range(count):
   dx,dy=((0,0),(1,0),(-1,0),(0,16),(16,0),(255.875,.25),(100000,-100000),(0,-16))[i%8]
   x,y=point[0]+dx,point[1]+dy;ident=(0,7,7,11,13,0xffffffff,99,123)[i];flags=(0,1,0x20,0x4000000,0x8000000,0x2000000,0x100,0)[(i+n//216)%8]
   enemy=base+i*0x6000;node=nodes+i*12;put(node,enemy);put(node+4,node+12 if i+1<count else 0);put(enemy+0x5740,ident);put(enemy+0x526c,flags);m.mem_write(enemy+0x1250,struct.pack('<fff',x,y,i+.125));entries.append(dict(id=ident,flags=flags,position=[x,y,i+.125]))
  put(manager+0x180,nodes if count else 0);m.mem_write(pos,struct.pack('<fff',*point,.75));m.reg_write(UC_X86_REG_XMM3,struct.unpack('<I',struct.pack('<f',radius))[0]);call(0x425240,(out,pos));nearest=get(out)
  target=(0,7,13,123,0xffffffff,888)[(n//5)%6];valid=call(0x41a980,(target,));put(out,target);pointer=call(0x41b540,ecx=out);lookup=(pointer-base)//0x6000 if pointer else -1
  cases.append(dict(n=n,point=[*point,.75],radius=radius,target=target,entries=entries,output=[nearest,valid,lookup]))
 (ROOT/'artifacts/th16/enemy-targets-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases))+'\n',encoding='utf8');print(f'{len(cases)} native enemy target list cases / {len(cases)*3} whole calls')
if __name__=='__main__':main()
