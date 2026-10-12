"""Retail TH16 423050 descriptors; argument resolvers and allocation are boundaries."""
import importlib,hashlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,OWNER,CONTEXT,CODE,MANAGER,FILES,TABLE,STACK,RETURN=(0x70000000,0x70010000,0x70016000,0x70018000,0x70020000,0x70022000,0x70024000,0x700ff000,0x700fe000)
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(BASE,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 output=[];resolutions=[];values=[];refs=0;boss=0;lookups=[]
 def boundary(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x477920:m.mem_write(get(sp+4),bytes([get(sp+8)&255])*get(sp+12))
  elif address==0x473ef0:
   index=get(sp+4);resolutions.append(index);raw=machine.reg_read(UC_X86_REG_XMM2)&0xffffffff
   machine.reg_write(UC_X86_REG_XMM0,struct.unpack('<I',struct.pack('<f',values[index-1]))[0] if refs&(1<<index) else raw)
  elif address==0x473e40:
   index=get(sp+4);resolutions.append(index);machine.reg_write(UC_X86_REG_EAX,(int(values[index-1]) if refs&(1<<index) else get(sp+8))&0xffffffff)
  elif address==0x41aa70:
   assert get(sp+12)==0 and bytes(m.mem_read(get(sp+4),11)).startswith(b'MapleEnemy\0')
   output.extend(struct.unpack('<21I',m.mem_read(get(sp+8),84)))
  elif address==0x417580:lookups.append(get(sp+4));machine.reg_write(UC_X86_REG_EAX,boss)
 for address,cleanup in ((0x477920,0),(0x473ef0,4),(0x473e40,8),(0x41aa70,12),(0x47499b,0),(0x417580,4)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 rows=[]
 for op in (300,301,304,305,309,310,311,312,321):
  for flags in (0,0x80000):
   for refs in (0,62):
    for n in range(4):
     values=[.125+n*13.5,-20.25+n*11.25,100+n,1000+n,-1+n];position=[-99.5+n*32.25,27.75-n*9.5,9]
     name=b'MapleEnemy\0\0';arguments=struct.pack('<I',len(name))+name
     arguments+=struct.pack('<ffiii',64,68,72,76,80) if refs else struct.pack('<ffiii',*values)
     code=struct.pack('<iHHHBBI',0,op,16+len(arguments),refs,255,6,0)+arguments
     m.mem_write(BASE,bytes(0x5000));m.mem_write(CODE,bytes(16)+code);put(BASE+0x4060,flags);put(BASE+0x44b8,OWNER);put(OWNER+0xc,CONTEXT)
     put(CONTEXT+4,0);put(CONTEXT+8,0);put(CONTEXT+0x1018,OWNER);put(OWNER+0x11f8,FILES);put(FILES+0x8c,TABLE);put(TABLE+4,CODE)
     put(OWNER+0x5740,123+n);put(0x4a6dc0,MANAGER);put(MANAGER+0x18c,2);put(MANAGER+0x8c,99999);m.mem_write(BASE+0x44,struct.pack('<3f',*position))
     inherited=[0x12340000+i*100+n for i in range(12)]
     for i,v in enumerate(inherited):put(BASE+0x28c+i*4,v)
     put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,BASE);output.clear();resolutions.clear();m.emu_start(0x423050,RETURN,count=5000)
     assert m.reg_read(UC_X86_REG_EIP)==RETURN and len(output)==21 and resolutions==[1,2,3,4,5]
     rows.append(dict(opcode=op,flags=flags,refs=refs,values=values,position=position,inherited=inherited,parent=123+n,code=code.hex(),output=list(output)))
 guards=[]
 for op in (300,301,304,305,309,310,311,312,321):
  for boss in (0,1):
   for count,capacity in ((0,1),(1,1),(2,1),(0,99999),(0,0xffffffff),(0xffffffff,0)):
    put(CODE+16+4,(get(CODE+16+4)&0xffff0000)|op);put(MANAGER+0x18c,count);put(MANAGER+0x8c,capacity);output.clear();lookups.clear()
    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EDI,BASE)
    address=img.u32(0x422ab8+img.read(0x422d70+op-300,1)[0]*4);m.emu_start(address,0x422a9b,count=5000)
    assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
    guards.append(dict(op=op,boss=boss,count=count,capacity=capacity,created=bool(output),lookups=list(lookups)))
 out=ROOT/'artifacts/th16/enemy-spawn-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,guards=guards),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} TH16 native descriptors; {len(guards)} dispatch/capacity guards.')
if __name__=='__main__':main()
