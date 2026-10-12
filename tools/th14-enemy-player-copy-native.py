"""Actual retail 427199/4271c2 player XYZ copy, without movement refresh."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,manager,player,stack=0x70001000,0x70010000,0x70011000,0x7003f000;m.mem_map(0x70000000,0x40000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 fields=(0,4,8,0x34,0x38,0x3c,0x18,0x1c,0x20,0x24,0x28,0x2c,0x40)
 raw=(0x80000000,0,0x7fc01234,0x7f800000,0xff800000,0x41234567,0x00000001,0x3f800000)
 rows=[]
 for op,variant in itertools.product((414,415),range(64)):
  m.mem_write(base,bytes(0x30000));put(0x4db544,manager);put(manager+0x5c,player)
  before=[raw[(variant+n)%8] for n in range(52)]+[0xa5a55a5a]
  for k,offset in enumerate((0,0x44,0x88,0xcc)):
   for n,field in enumerate(fields):put(base+offset+field,before[k*13+n])
  put(base+0x4054,before[-1]);xyz=[raw[variant%8],raw[variant//8],raw[(variant+3)%8]]
  for n,v in enumerate(xyz):put(player+0x1234+4*n,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base)
  m.emu_start(0x427199 if op==414 else 0x4271c2,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
  result=[get(base+offset+field) for offset in (0,0x44,0x88,0xcc) for field in fields]+[get(base+0x4054)]
  rows.append(dict(op=op,variant=variant,initial=before,player=xyz,result=result))
 output=ROOT/'artifacts/th14/enemy-player-copy-native.json';output.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows)),encoding='utf-8');print(f'native player position copy: {len(rows)} cases')
if __name__=='__main__':main()
