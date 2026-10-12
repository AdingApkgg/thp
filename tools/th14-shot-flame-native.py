"""Retail focused Marisa A callbacks 452d20/452ca0/452da0."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 end,obj,area,stack=0x70000000,0x70001000,0x70002000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];events=[]
 def boundary(machine,a,size,user):events.append(get(m.reg_read(UC_X86_REG_ESP)+8))
 m.mem_write(0x47f140,b'\xc2\x08\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=0x47f140,end=0x47f140)
 def setup(seed,speed,age,flags,damage,present):
  m.mem_write(obj,bytes(0x100));m.mem_write(area,bytes(0x100));put(obj+0x14,73);put(obj+0x10,flags);put(obj+0x6c,bits(speed));put(obj+0x1c,age);put(obj+0xc0,area if present else 0);put(area+0x84,damage);put(0x4db510,seed);put(0x4db514,123);events.clear()
 def call(a):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(a,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
 spawns=[]
 for seed,angle,flags in itertools.product((0,1,17,12345,32767,65534,65535),(-3.2,-3.1415927410125732,-1.25,0,3.1415927410125732,3.2),(0,1,2,0x3c,0xff)):
  setup(seed,8,0,flags,19,1);put(obj+0x70,bits(angle));call(0x452d20);spawns.append(dict(args=[seed,angle,flags],result=[get(obj+0x70),get(obj+0x10),get(0x4db510),get(0x4db514)]))
 updates=[]
 for seed,speed,age,flags,damage,present in itertools.product((0,1,17,12345,32767,65534,65535),(-2.,0.,1.,2.5,8.,16.),(3,35,36,37,100),(0,1,2,4,0x38,0x3c,0xff),(-19,19),(0,1)):
  setup(seed,speed,age,flags,damage,present);call(0x452ca0);updates.append(dict(args=[seed,speed,age,flags,damage,present],result=[get(obj+0x6c),get(obj+0x10),get(area+0x84),get(0x4db510),get(0x4db514)],events=events[:]))
 small=[]
 for state,speed,age,advanced in itertools.product((0,1,2),(-2.,0.,1.,2.5,8.,16.),(0,2,3,4,36),(0,1)):
  setup(1,speed,age,1,19,1);put(obj+0x98,state);put(obj+0x18,age-advanced);call(0x452da0);small.append(dict(args=[state,speed,age,advanced],result=[get(obj+0x6c),get(obj+0x98)],events=events[:]))
 (ROOT/'artifacts/th14/shot-flame-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),spawns=spawns,updates=updates,small=small),indent=2)+'\n',encoding='utf-8');print(f'{len(spawns)} flame spawns / {len(updates)} flame updates / {len(small)} small-flame updates')
if __name__=='__main__':main()
