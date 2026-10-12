"""Complete442380; empty callback fields, controlled handle lookup/interrupt."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,arena,stack=0x70000000,0x70001000,0x70040000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 handles={i+1:arena+i*0x1000 for i in range(24)}
 def hook(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);v=handles.get(get(sp+4),0)
  if a==0x46efa0:m.reg_write(UC_X86_REG_EAX,v)
  elif v:put(v+0x490,get(sp+8))
 for a,n in ((0x46efa0,4),(0x46f0b0,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n));m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[];fields=(0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xd0,0xd4)
 for base,focus,recall,clock,lerp,seed,snap,present in itertools.product((0,4),(0,1),(0,1),(0,29,30,31),(0,29,30,100,2147483647),(0,1,2),(0,1),(0,1)):
  m.mem_write(player,bytes(0x30000))
  for off,v in ((0x61c,(-321,2147480000,-2147480000)[seed]),(0x620,(50319,-2147480000,2147480000)[seed]),(0x165c8,focus),(0x1664c,recall*2),(0x16680,lerp),(0x16684,clock)):put(player+off,v)
  for i in range(12):
   o=player+0x660+i*0xe4
   for k in fields:put(o+k,17+i*31+k+seed*100000003)
   put(o,0 if i%3==seed else 2);put(o+0xd4,snap)
   for aux in range(2):
    id=i*2+aux+1;v=handles[id];put(o+0xb0+aux*4,id if present else 0);m.mem_write(v,bytes(0x600));m.mem_write(v+0x5e0,struct.pack('<fff',91.,-72.,33.));put(v+0x490,77)
  put(stack,ret);put(stack+4,player+0x660+base*0xe4);put(stack+8,4 if base==0 else 8);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x442380,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(base=base,focus=focus,recall=recall,clock=clock,lerp=lerp,seed=seed,snap=snap,present=present,options=[[get(player+0x660+i*0xe4+k) for k in fields] for i in range(12)],animations=[[get(v+k) for k in (0x5e0,0x5e4,0x5e8,0x490)] for v in handles.values()]))
 (ROOT/'artifacts/th16/option-motion-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 option movement cases')
if __name__=='__main__':main()
