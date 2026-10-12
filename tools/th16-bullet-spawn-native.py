"""Retail TH16 zero/appearance-delay ETEX spawn; binding/update/interrupt are controlled."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x1600000)
 manager,bullet,emitter,player,stack,ret=0x70001000,0x71500000,0x71504000,0x71505000,0x715fd000,0x715fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 bindings=[];interrupts=[];updates=[]
 def boundary(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP);vm=machine.reg_read(UC_X86_REG_ECX)
  if address==0x45f160:
   vm=get(sp+4);bindings.append([vm-bullet,get(sp+8)]);machine.reg_write(UC_X86_REG_EAX,vm)
  elif address==0x4174d0:interrupts.append([vm-bullet,get(sp+4)]);put(vm+0x490,get(sp+4))
  elif address==0x45f980:updates.append(vm-bullet);machine.reg_write(UC_X86_REG_EAX,0)
 for address,cleanup in ((0x4090f0,0),(0x45f160,8),(0x4174d0,4),(0x45f980,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4a6dac,manager);put(0x4a6ef8,player);rows=[]
 for style in range(44):
  for color in range(16):
   for delayed in (0,1,2):
    m.mem_write(bullet,bytes(0x2000));m.mem_write(emitter,bytes(0x380));put(manager+0x60,bullet);put(manager+0x70,0);put(manager+0x1403b24,0x71508000);put(manager+0x44,0)
    m.mem_write(emitter+8,struct.pack('<8f',1,2,3,.3,.5,2,1,0));m.mem_write(emitter+0x364,struct.pack('<3h',1,1,1))
    put(emitter,style);put(emitter+4,color);put(emitter+0x36c,0x23);put(emitter+0x374,38)
    if delayed:put(emitter+0x48,2);put(emitter+0x38,delayed)
    put(stack,ret);put(stack+4,emitter);put(stack+8,0);put(stack+12,0);put(stack+16,0)
    bindings.clear();interrupts.clear();updates.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
    m.emu_start(0x412cb0,ret,count=20000);assert m.reg_read(UC_X86_REG_EIP)==ret
    offsets=(0x20,0x24,0xc20,0xc24,0xc28,0xc2c,0xc30,0xc34,0xc38,0xc3c,0xc40,0xc44,0xc58,0xc5c,0xc60,0xc64,0xc68,0xc6c,0xc72,0xc7c,0xc80,0xc84,0x141c,0x1474)
    rows.append(dict(style=style,color=color,delayed=delayed,output=[get(bullet+o) for o in offsets],bindings=list(bindings),interrupts=list(interrupts),updates=list(updates)))
 out=ROOT/'artifacts/th16/bullet-spawn-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} TH16 native spawn/appearance/delay cases')
if __name__=='__main__':main()
