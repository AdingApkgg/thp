"""Retail ETEX 1000 setup and 41a380 screen wrapping; sound is a boundary."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,sprite,stack=0x70000000,0x70001000,0x70005000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 sounds=[]
 def sink(machine,a,size,user):sounds.append(get(m.reg_read(UC_X86_REG_ESP)+4));m.reg_write(UC_X86_REG_EAX,0)
 m.mem_write(0x46e3d0,b'\xc2\x08\x00');m.hook_add(UC_HOOK_CODE,sink,begin=0x46e3d0,end=0x46e3d0)
 def call(a):
  m.mem_write(stack-0x3000,bytes(0x3100));put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end;return m.reg_read(UC_X86_REG_EAX)
 def state():return [get(obj+p) for p in (0xc04,0xc20,0xbc0,0xbc4,0xbc8,0x1124,0x1128,0x112c)]+[len(sounds)]
 rows=[]
 positions=((-202.25,40.5),(-202.,40.5),(-192.,40.5),(192.,40.5),(202.,40.5),(202.25,40.5),(12.25,-10.),(12.25,0.),(12.25,448.),(12.25,458.),(-210.,-20.),(210.,470.))
 for flags,limit,pos,dimension,sound in itertools.product(range(16),(-1,0,1,3),positions,((20.,12.),(8.,64.),(64.,8.)),(-1,38)):
  sounds.clear();m.mem_write(obj,bytes(0x2000));put(obj+0x54,sprite);put(sprite+0x34,bits(dimension[1]));put(sprite+0x38,bits(dimension[0]));m.mem_write(obj+0xbc0,struct.pack('<3f',*pos,3.25));put(obj+0xc1c,sound)
  put(obj+0xc28+0x10,limit);put(obj+0xc28+0x14,flags);put(obj+0xc28+0x20,0x1000);call(0x418140);initial=state();result=call(0x41a380)
  rows.append(dict(flags=flags,limit=limit,position=pos,dimension=dimension,sound=sound,initial=initial,result=result,state=state()))
 blends=[]
 for seed,blend,param,active,concurrent in itertools.product((0,1,0xffffffff,0x55555555,0xaaaaaaaa),range(16),(-1,0,1,2),(0,4,0x100),(0,1)):
  flags=(seed&~0x1e0)|(blend<<5);m.mem_write(obj,bytes(0x2000));put(obj+0x40,flags);put(obj+0xc04,active);put(obj+0xc28+0x10,param);put(obj+0xc28+0x20,0x100000);put(obj+0xc28+0x24,concurrent);call(0x418140)
  final=get(obj+0x40);blends.append(dict(flags=flags,param=param,active=active,concurrent=concurrent,state=[get(obj+0xc20),get(obj+0xc04),(final>>5)&15,int((final&~0x1e0)==(flags&~0x1e0))]))
 (ROOT/'artifacts/th14/bullet-wrap-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,blends=blends),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} native ETEX 1000 setup/wrap cases; {len(blends)} ETEX 100000 blend cases.')
if __name__=='__main__':main()
