"""Observe retail 423ee5..42407c with declared enemy/VM inputs and a sound sink."""
from pathlib import Path
import hashlib,importlib,itertools,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x20000);vm=base+0x10000;stack=base+0x1f000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 sound=[]
 def sink(u,a,n,data):sound.append(get(u.reg_read(UC_X86_REG_ESP)+4))
 m.mem_write(0x46e470,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,sink,begin=0x46e470,end=0x46e470)
 rows=[]
 flags=(0,0x200000,0x40000000,0x800000,0x40800000,0x80000000,0x80200000,0x4080000,0x8000000,0xffffffff,0x40a00000,0xc0800000)
 for flag,life,flash,spell,health,mode in itertools.product(flags,(-1,0,1,4),(0,1,-1),(0,1,8,9),(-1,99,100,499,500),(0x20000,0x40000,0x60000,0x80000007)):
  sound.clear()
  for p,v in ((base+0x4054,flag),(base+0x2c0,life),(base+0x3fe0,flash),(base+0x3fe8,-1),(base+0x40ec,base+0x8000),(base+0xd16c,health),(0x4db534,base+0xe000),(base+0xe07c,spell),(vm+0x18,mode),(vm+0x538,0x12345678)):put(p,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ECX,vm)
  m.emu_start(0x423ee5,0x42407c,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x42407c
  rows.append([flag,life,flash,spell,health,mode,get(base+0x3fe0),get(vm+0x18),get(vm+0x538),sound[0]if sound else 0xffffffff]);assert len(sound)<=1
 out=ROOT/'artifacts/th14/enemy-hit-flash-check';out.mkdir(parents=True,exist_ok=True)
 (out/'native.json').write_text(json.dumps(dict(originalExecutableSha256=hashlib.sha256(img.data).hexdigest(),actualBranch='423ee5..42407c',controlledVmAndEnemy=True,soundSinkPatched=True,rows=rows),separators=(',',':'))+'\n')
 print(json.dumps(dict(cases=len(rows),originalBranch='423ee5..42407c')))
if __name__=='__main__':main()
