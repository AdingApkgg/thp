"""Own422966 ECL800 with real lookup, thread release, context reset and sub selection."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x100000)
 caller,targets,nodes,manager,code,stack=(0x70000000+x for x in (0x1000,0x10000,0x30000,0x31000,0x32000,0xfe000))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 freed=[];selected=[];ident=0;exists=False
 def hook(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x4251d0:assert get(sp+4)==0;machine.reg_write(UC_X86_REG_EAX,ident&0xffffffff)
  elif a==0x4749df:freed.append(get(sp+4))
  else:
   assert bytes(m.mem_read(get(sp+4),7))==b'Switch\0';selected.append(get(sp+4));machine.reg_write(UC_X86_REG_EAX,0 if exists else 0xffffffff)
 for a,n in ((0x4251d0,4),(0x4749df,0),(0x474740,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[]
 for n in range(768):
  count=n%3;ident=(0,7,9,123,-1)[n//3%5];threads=n//15%4;dirty=(0,128,4092)[n//7%3];exists=bool(n//5%2);duration=(-1,0,17)[n//11%3];flags=(0,1,0xffffffff)[n//13%3]
  m.mem_write(caller,bytes(0x4000));m.mem_write(targets,bytes(0x20000));m.mem_write(nodes,bytes(0x3000));put(0x4a6dc0,manager);put(manager+0x180,nodes if count else 0);m.mem_write(code+24,b'Switch\0');freed.clear();selected.clear()
  for j in range(2):
   target=targets+j*0x8000;put(nodes+j*16,target);put(nodes+j*16+4,nodes+(j+1)*16 if j+1<count else 0)
   for off,v in ((0x5740,7+j*2),(0xc,target+0x10),(0x10,0x40600000),(0x14,4),(0x18,128),(0x1c,0x12345678),(0x101c,dirty),(0x1020,dirty),(0x1024,37),(0x1028,target),(0x102c,9),(0x1030,0xa),(0x11f4,flags),(0x1200,targets+0x10000+j*0x1000 if threads else 0)):put(target+off,v)
   for k in range(8):put(target+0x105c+k*0x30,duration+k);put(target+0x1044+k*0x30,0x3f800000+k)
   for k in range(threads):
    node=targets+0x10000+j*0x1000+k*16;put(node,targets+0x13000+j*0x5000+k*0x1200);put(node+4,node+16 if k+1<threads else 0)
  m.reg_write(UC_X86_REG_EDI,caller);m.reg_write(UC_X86_REG_ESI,code);m.reg_write(UC_X86_REG_ESP,stack);put(stack,0x700ff000);m.emu_start(0x422966,0x422a9b,count=20000)
  assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  index=0xffffffff if not count or not ident else 0 if ident==7 else 1 if count==2 else 0
  assert len(freed)==(0 if index==0xffffffff else threads*2) and len(selected)==(0 if index==0xffffffff else 1)
  output=[index]
  for j in range(2):
   target=targets+j*0x8000
   output += [get(target+0x10),int(get(target+0x14)!=0xffffffff),get(target+0x18),get(target+0x101c),get(target+0x1020),get(target+0x1024),get(target+0x102c),get(target+0x1030),get(target+0x1c)]
   output += [get(target+0x105c+k*0x30) for k in range(8)]+[get(target+0x1044+k*0x30) for k in range(8)]+[int(bool(get(target+0x1200))),int(get(target+0xc)==target+0x10)]
  rows.append(dict(count=count,id=ident,threads=threads,dirty=dirty,exists=exists,duration=duration,flags=flags,output=output))
 (ROOT/'artifacts/th16/enemy-script-switch-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} own ECL800 script switch cases')
if __name__=='__main__':main()
