"""Own ECL339 request arm and ECL556 copying; external VM consumers controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x100000);m.mem_map(0x12340000,0x1000);data,owner,context,manager,vm,code,stack,bp=0x70001000,0x70010000,0x70011000,0x70012000,0x70014000,0x70018000,0x700f0000,0x700f8000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 put(data+0x44b8,owner);put(owner+12,context);put(0x4a6dc0,manager)
 for n in range(16):put(manager+0x164+n*4,0x12340000+n)
 args=[];events=[];reads=[];ticks=0;counts=[];positioned=False
 def boundary(machine,address,size,user):
  nonlocal ticks
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x473d40:
   index=get(sp+4);reads.append(index);machine.reg_write(UC_X86_REG_XMM0,args[index])
  elif address==0x473c90:
   index=get(sp+4);reads.append(index);value=args[index] if index<2 else counts[min(ticks,len(counts)-1)];machine.reg_write(UC_X86_REG_EAX,value&0xffffffff)
  elif address==0x426160:
   dest,script,layer=get(sp+4),get(sp+8),get(sp+12);events.append([0,machine.reg_read(UC_X86_REG_ECX)-0x12340000,script,layer]);put(dest,37);machine.reg_write(UC_X86_REG_EAX,dest)
  elif address==0x41aa00:events.append([1,get(sp+4),0,0]);machine.reg_write(UC_X86_REG_EAX,0x80000000)
  elif address==0x46f2e0:events.append([2,0,0,0]);machine.reg_write(UC_X86_REG_EAX,vm)
  elif address==0x46f600:machine.reg_write(UC_X86_REG_EAX,vm)
  elif address==0x407b20:events.append([4,machine.reg_read(UC_X86_REG_ECX)-0x12340000,get(sp+8),0])
  elif address==0x46e890:dest=get(sp+4);events.append([5,0,0,0]);put(dest,37);machine.reg_write(UC_X86_REG_EAX,dest)
  else:events.append([3,0,0,0]);ticks+=1;machine.reg_write(UC_X86_REG_EAX,1)
 for address,cleanup in ((0x473d40,4),(0x473c90,4),(0x426160,12),(0x41aa00,4),(0x46f2e0,0),(0x45f980,0),(0x46f600,0),(0x407b20,8),(0x46e890,8)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 animations=[]
 for file,script,counts_ in itertools.product((0,1,2,3,15),(-1,0,7,999,2147483647),((-1,),(0,),(1,),(3,),(8,),(5,1),(1,3,1))):
  args=[file,script];counts=list(counts_);events.clear();reads.clear();ticks=0;m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_EDX,owner);m.emu_start(0x41e274,0x422a9b,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  animations.append(dict(file=file,script=script,counts=counts,events=list(events),reads=list(reads)))
 animation308=[]
 for file,script in itertools.product((0,1,2,3,15),(-1,0,7,999,2147483647)):
  args=[file,script];counts=[0];events.clear();reads.clear();ticks=0;m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_EDX,owner);m.emu_start(0x41e22b,0x422a9b,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  animation308.append(dict(file=file,script=script,events=list(events),reads=list(reads)))
 animation307=[]
 for file,position in itertools.product(range(16),((0.,0.,0.),(-32.125,48.5,3.75),(-0.,-0.,-0.),(192.,448.,.25))):
  args=[file,0];counts=[0];events.clear();reads.clear();ticks=0;m.mem_write(vm,bytes(0x700));put(vm+0x18,14);m.mem_write(data+0x44,struct.pack('<fff',*position));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_EDX,owner);m.emu_start(0x41e118,0x422a9b,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  animation307.append(dict(file=file,positionBits=list(struct.unpack('<III',struct.pack('<fff',*position))),events=list(events),reads=list(reads),output=[get(vm+o) for o in (0x18,0x534,0x5e0,0x5e4,0x5e8,0x40,0x51c)]))
 animation338=[]
 for file,position,offset in itertools.product(range(16),((0.,0.,0.),(-32.125,48.5,3.75),(-0.,-0.,-0.),(192.,448.,.25)),((0.,0.,0.),(-0.,-0.,-0.),(-19.25,37.875,-1.5707963705062866),(10000.5,-10000.25,3.1415927410125732))):
  offsetBits=list(struct.unpack('<III',struct.pack('<fff',*offset)));args=[file,0,*offsetBits];counts=[0];events.clear();reads.clear();ticks=0;m.mem_write(vm,bytes(0x700));put(vm+0x18,14);m.mem_write(data+0x44,struct.pack('<fff',*position));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_EDX,owner);m.emu_start(0x41dfc7,0x422a9b,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  animation338.append(dict(file=file,positionBits=list(struct.unpack('<III',struct.pack('<fff',*position))),offsetBits=offsetBits,events=list(events),reads=list(reads),output=[get(vm+o) for o in (0x18,0x534,0x5e0,0x5e4,0x5e8,0x40,0x51c)]))
 copies=[]
 for length,seed in itertools.product((0,1,7,31,62,63),(0,1,7,255)):
  name=bytes(65+(i%26) for i in range(length));initial=bytes((seed+i*3)&255 for i in range(64));m.mem_write(data+0x44d8,initial);m.mem_write(code+20,name+b'\0');m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ESI,code);m.reg_write(UC_X86_REG_EDI,data);m.emu_start(0x421633,0x422a9b,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  copies.append(dict(length=length,seed=seed,output=list(m.mem_read(data+0x44d8,64))))
 (ROOT/'artifacts/th16/entry-commands-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),animations=animations,animation308=animation308,animation307=animation307,animation338=animation338,copies=copies),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(animations)} native ECL339 requests / {len(animation308)} ECL308 requests / {len(animation307)} ECL307 requests / {len(animation338)} ECL338 requests / {len(copies)} death-script copies')
if __name__=='__main__':main()
