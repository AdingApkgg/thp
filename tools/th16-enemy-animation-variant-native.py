"""Own41e6ab ECL316 through retirement/lookup/visibility; VM factory controlled."""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x30000)
 data,owner,context,manager,resource,old,new,stack,ret=(0x70000000+x for x in (0,0x6000,0x7000,0x9000,0xa000,0xb000,0xc000,0x2d000,0x2e000))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 args=[];request=[];reads=[]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x473c90:
   index=get(sp+4);reads.append(index);machine.reg_write(UC_X86_REG_EAX,args[index]&0xffffffff)
  elif a==0x46efa0:machine.reg_write(UC_X86_REG_EAX,new if get(sp+4)==1000 else old)
  else:
   request[:]=[get(sp+8),get(sp+12),3];put(get(sp+4),1000);machine.reg_write(UC_X86_REG_EAX,get(sp+4))
 for a,n in ((0x473c90,4),(0x46efa0,4),(0x426160,16)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n));m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 rows=[]
 for slot,variant,base,facing,flags,oldflags in itertools.product((0,1,9,10,15),(-7,-1,0,3),(5,40,120),(-8,-7,0,16,17),(0,32,0xaabbccdd),(0,0x40,0xffffffff)):
  m.mem_write(data,bytes(0x4500));m.mem_write(old,bytes(0x600));m.mem_write(new,bytes(0x600));request.clear();reads.clear();args=[slot,variant]
  for p,v in ((data+0x44b8,owner),(owner+12,context),(data+0x264,3),(data+0x270,base),(data+0x274,2),(data+0x27c,facing),(data+0x4060,flags),(data+0x3f58,0x41300000),(data+0x3f5c,0x41500000),(manager+0x164+12,resource),(0x4a6dc0,manager),(new+0x50,0x3f800000),(new+0x54,0x3f800000),(new+0x530,3),(old+0x534,oldflags)):put(p,v)
  for n in range(16):put(data+0x124+n*4,100+n)
  m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_EDX,owner);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack-0x100);put(stack,ret)
  m.emu_start(0x41e6ab,0x422a9b,count=4000)
  assert m.reg_read(UC_X86_REG_EIP)==0x422a9b and reads==[0,1]
  output=request+[get(data+o) for o in (0x3f58,0x3f5c,0x4060,0x274,0x270)]+[get(new+0x530)&2,get(old+0x534)]+[get(data+0x124+n*4) for n in range(16)]
  rows.append(dict(slot=slot,variant=variant,base=base,facing=facing,flags=flags,oldflags=oldflags,output=output))
 (ROOT/'artifacts/th16/enemy-animation-variant-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8')
 print(f'{len(rows)} own ECL316 animation replacement cases')
if __name__=='__main__':main()
