"""565 setter and actual 423b27..423b72 bomb damage scaling, sound sink only."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,stack=0x70000000,0x7000f000;m.mem_map(base,0x10000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 sound=[];ratio=0
 def hook(machine,address,size,user):
  if address==0x42c230:m.reg_write(UC_X86_REG_XMM0,ratio)
  else:sound.append([get(m.reg_read(UC_X86_REG_ESP)+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
 for p in (0x42c230,0x46e470):m.mem_write(p,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,hook,begin=p,end=p)
 cases=[]
 for ratio in (bits(0),bits(-0.),bits(.2),bits(.999),bits(1),bits(2),bits(-.5),0x7fc01234,0x7f800000,0xff800000):
  for damage in (-2147483648,-16777217,-1,0,1,5,100,16777217,2147483647):
   for active in (0,1,2):
    m.mem_write(base,bytes(0xe000));sound.clear();put(base+0x4034,bits(1));put(base+0x44,bits(-12.25));put(0x4db52c,base+0x8000);put(base+0x8040,active)
    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.emu_start(0x427704,0x429c28,count=1000);assert get(base+0x4034)==ratio
    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESI,damage&0xffffffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.emu_start(0x423b27,0x423b72,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x423b72
    cases.append(dict(ratio=ratio,damage=damage,active=active,result=m.reg_read(UC_X86_REG_ESI),sound=sound[:]))
 hits=[]
 for override in (-1,36,2147483647):
  for flags in (0,0x40000000,0x800000,0xffffffff):
   for spell in (0,1,8,9):
    for health in (-1,199,200,899,900):
     m.mem_write(base,bytes(0xe000));sound.clear();put(base+0x3fe8,override);put(base+0x4054,flags);put(base+0x40ec,base+0x8000);put(base+0xd16c,health);put(base+0x44,bits(-12.25));put(0x4db534,base+0x9000);put(base+0x907c,spell)
     m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.emu_start(0x423f61,0x42407c,count=1000)
     assert get(base+0x3fe0)==4 and len(sound)==1
     hits.append(dict(override=override,flags=flags,spell=spell,health=health,sound=sound[:]))
 out=ROOT/'artifacts/th14/enemy-bomb-damage-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,hits=hits))+'\n',encoding='utf8');print(f'{len(cases)} retail bomb damage cases, {len(hits)} hit sound cases.')
if __name__=='__main__':main()
