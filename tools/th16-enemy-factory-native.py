"""Retail41aa70 parameter binding/death metadata; allocator, constructor, frame boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x30000);enemy,manager,params,stack,ret=0x70001000,0x70010000,0x70012000,0x7002e000,0x7002f000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 seen=[]
 def boundary(machine,address,size,user):
  if address in (0x4749ac,0x41b580):machine.reg_write(UC_X86_REG_EAX,enemy)
  elif address==0x41d1e0:seen.append(machine.reg_read(UC_X86_REG_ECX));machine.reg_write(UC_X86_REG_EAX,0)
 for address,cleanup in ((0x4749ac,0),(0x41b580,4),(0x41d1e0,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 rows=[]
 for flags in (0,0xffffffff):
  for mirrored,world in ((0,0),(1,1),(2,2),(3,3)):
   for health in (-1,999,1000,1001):
    for file,script,death in ((0,5,0),(1,5,0),(2,5,0),(2,10,0),(2,15,0),(2,25,0),(2,30,0),(2,35,0),(2,40,0),(2,53,0),(2,56,0),(2,79,0),(2,83,0),(2,91,0),(2,999,0),(2,5,77)):
     m.mem_write(enemy,bytes(0x6000));m.mem_write(manager,bytes(0x200));m.mem_write(params,bytes(84));put(0x4a6dc0,manager);put(0x4a57b4,1);put(0x4a5798,9)
     put(enemy+0x526c,flags);put(enemy+0x5740,22);put(enemy+0x1474,file);put(enemy+0x1478,script);put(enemy+0x51f4,death);put(enemy+0x51f8,6)
     for o,v in ((0x0,0x3f800000),(0x4,0xc0000000),(0x8,0x40400000),(0xc,1007),(0x10,4),(0x14,health),(0x18,mirrored),(0x1c,world),(0x50,123)):put(params+o,v)
     for j in range(12):put(params+0x20+j*4,0x12340000+j)
     put(stack,ret);put(stack+4,params);put(stack+8,params);put(stack+12,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);seen.clear();m.emu_start(0x41aa70,ret,count=10000)
     assert m.reg_read(UC_X86_REG_EIP)==ret and seen==[enemy] and get(manager+0x18c)==1
     offsets=(0x1294,0x1298,0x129c,0x517c,0x5180,0x5184,0x519c,0x526c,0x5744,0x51dc,0x5248,0x524c,0x5250,0x525c,0x5260,0x5734,0x51f0,0x51f4,0x51f8)
     rows.append(dict(flags=flags,mirrored=mirrored,world=world,health=health,file=file,script=script,death=death,output=[get(enemy+o) for o in offsets]+[get(enemy+0x1498+j*4) for j in range(12)]))
 out=ROOT/'artifacts/th16/enemy-factory-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} native TH16 parameter-binding/death-metadata cases')
if __name__=='__main__':main()
