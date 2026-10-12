"""Full own4233a0 simple setters; controlled argument resolvers and registry lookup."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000)
 data,owner,context,full,manager,table,code,vm,stack,ret=(0x70000000+v for v in (0,0x5000,0x6000,0x8000,0xa000,0xb000,0xc000,0xd000,0x1d000,0x1e000))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 args=[];reads=[];lookups=[];available=False
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP);index=get(sp+4)
  if a==0x46efa0:lookups.append(index);machine.reg_write(UC_X86_REG_EAX,vm if available else 0)
  else:reads.append(index);machine.reg_write(UC_X86_REG_EAX if a==0x473c90 else UC_X86_REG_XMM0,args[index]&0xffffffff)
 for a in (0x46efa0,0x473c90,0x473d40):m.mem_write(a,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 for p,v in ((data+0x44b8,owner),(owner+12,context),(context+4,0),(context+8,0),(context+0x1018,full),(full+0x11f8,manager),(manager+0x8c,table),(table+4,code-16)):put(p,v)
 cases=[]
 values=((0,0,0),(0x80000000,0x3f800000,-1),(0x3f000000,0xbf800000,255),(0x7f7fffff,0x00800000,256),(-2147483648,2147483647,-257))
 for op,slot,available,flags,values_ in itertools.product((319,325,327,329,331,335,337),(-1,0,9,10,15,16,2147483647),(False,True),(0,0xffffffff,0xaabbccdd),values):
  args=[slot,*values_];reads.clear();lookups.clear()
  for n in range(16):put(data+0x124+n*4,100+n)
  for off,v in ((0x40,0x3ec00000),(0x50,0x40000000),(0x54,0xc0400000),(0x58,0x3e000000),(0x5c,0xbf000000),(0x520,0x11223344),(0x524,0xaabbccdd),(0x530,flags)):put(vm+off,v)
  m.mem_write(code+4,struct.pack('<h',op));put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,data);m.emu_start(0x4233a0,ret,count=1500);assert m.reg_read(UC_X86_REG_EIP)==ret
  output=[get(vm+off) for off in (0x40,0x50,0x54,0x58,0x5c,0x520,0x524,0x530)]+[get(data+0x124+n*4) for n in range(16)]
  cases.append(dict(op=op,slot=slot,available=available,flags=flags,args=args,output=output,reads=list(reads),lookups=list(lookups)))
 sounds=[];sound_events=[]
 def sound_boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x4251d0:machine.reg_write(UC_X86_REG_EAX,args[get(sp+4)]&0xffffffff)
  else:sound_events.extend([get(sp+4),machine.reg_read(UC_X86_REG_XMM2)&0xffffffff])
 for a in (0x4251d0,0x45e1f0):m.mem_write(a,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,sound_boundary,begin=a,end=a)
 for id_,x in itertools.product((-2147483648,-1,0,3,42,2147483647),(0,0x80000000,0xc3382000,0x43400000,0x501502f9)):
  args=[id_];sound_events.clear();put(data+0x44,x);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x421668,0x422a9b,count=500);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  sounds.append(dict(id=id_,x=x,output=list(sound_events)))
 (ROOT/'artifacts/th16/enemy-anm-setters-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,sounds=sounds),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own enemy ANM simple setters; {len(sounds)} positional sound requests')
if __name__=='__main__':main()
