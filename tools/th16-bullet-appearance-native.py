"""Whole413860 ETEX512 scalar metadata and VM service order; VM reset/bind controlled."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
FIELDS=(0x20,0xc40,0xc44,0x1474,0xc84,0xc5c,0x55c,0x4b8,0xc68,0xc60,0xc4c)
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x1600000);bullet,manager,stack,ret=0x70001000,0x70008000,0x715fd000,0x715fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def event(kind,script=0):events.append([kind,script,get(bullet+0x20),get(bullet+0x1474),get(bullet+0xc40),get(bullet+0xc84)])
 def hook(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x4090f0:event(0 if machine.reg_read(UC_X86_REG_ECX)==bullet+0x28 else 2)
  else:event(1,get(sp+8));machine.reg_write(UC_X86_REG_EAX,get(sp+4))
 for a,n in ((0x4090f0,0),(0x45f160,8),(0x47499b,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3')
  if a!=0x47499b:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4a6dac,manager);put(manager+0x1403b24,0x71500000);rows=[]
 for n in range(2816):
  style=n%44;color=n//44%16;packed=color|(0,0x8000,0x10000,0x18000)[n//704%4];flags=(0,0xffffffff)[n//3%2];flags2=(0,0x89abcdef)[n//5%2];active=n//7%2;index=n//11%2;concurrent=n//13%2
  m.mem_write(bullet,bytes(0x2000));put(bullet+0x20,flags);put(bullet+0x55c,flags2);put(bullet+0x1474,0x12340002);put(bullet+0xc5c,-55);put(bullet+0xc84,9);put(bullet+0xc4c,19);put(bullet+0xc60,index);put(bullet+0xc68,active);put(bullet+0xc80,-1)
  t=bullet+0xc88+index*0x2c;put(t+0x10,style);put(t+0x14,packed);put(t+0x20,512);put(t+0x24,concurrent);put(t+0x2c+0x10,37);put(t+0x2c+0x20,32768);put(t+0x2c+0x24,1)
  events.clear();put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);m.emu_start(0x413860,ret,count=20000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(input=[style,packed,flags,flags2,active,index,concurrent],output=[get(bullet+o) for o in FIELDS],events=events[:]))
 (ROOT/'artifacts/th16/bullet-appearance-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} own ETEX512 appearance replacements')
if __name__=='__main__':main()
