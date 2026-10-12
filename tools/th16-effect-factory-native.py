"""Own TH16 500/501 stores and chapter-count side effect, controlled float args."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);file,vm,position,buffer,stack=0x70001000,0x70004000,0x70006000,0x70007000,0x7001e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def boundary(machine,address,size,user):
  if address==0x46f600:machine.reg_write(UC_X86_REG_EAX,vm)
  elif address==0x45f980:machine.reg_write(UC_X86_REG_EAX,0)
 for address,cleanup in ((0x46f600,0),(0x407b20,8),(0x45f980,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4c10b6,0);rows=[]
 for layer in (-1,0,23,24,35):
  for flags in (0,0x80000,0x40000,0xffffffff):
   for rotation in (0,-0.,.375,-3.25):
    for present in (0,1):
     m.mem_write(vm,bytes(0x700));put(vm+0x534,flags);put(vm+0x18,0);m.mem_write(position,struct.pack('<3f',-12.25,70.5,.25))
     for i,v in enumerate((0,buffer,0,position if present else 0,struct.unpack('<I',struct.pack('<f',rotation))[0],layer,7)):put(stack+i*4,v)
     m.reg_write(UC_X86_REG_ECX,file);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x40e5c0,0x40e67e,count=2000);assert m.reg_read(UC_X86_REG_EIP)==0x40e67e
     rows.append(dict(layer=layer,flags=flags,rotation=rotation,present=present,output=[get(vm+o) for o in (0x18,0x534,0x5e0,0x5e4,0x5e8,0x40)]))
 out=ROOT/'artifacts/th16/effect-factory-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} TH16 effect factory prefix cases')
if __name__=='__main__':main()
