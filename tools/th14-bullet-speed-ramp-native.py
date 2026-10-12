"""Actual retail ETEX 0x200000 setup (418140) and motion (419780), sound boundary."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,im.data[raw:raw+n])
 base=0x70000000;bullet=base+0x1000;player=base+0x4000;stack=base+0x1f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 sounds=[]
 def sound(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);sounds.append(get(sp+4));m.reg_write(UC_X86_REG_EAX,0)
 m.mem_write(0x4854a0,b'\xc3');m.mem_write(0x46e3d0,b'\xc2\x08\x00');m.hook_add(UC_HOOK_CODE,sound,begin=0x46e3d0,end=0x46e3d0)
 offsets=(0xc04,0xc20,0xbd8,0xbdc,0xbcc,0xbd0,0xbd4,0x1224,0x1228,0x1210,0x1214,0x1218,0x1244,0x1238,0x123c,0x1240)
 def state():return [get(bullet+n) for n in offsets]+[len(sounds)]
 def call(a):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);m.emu_start(a,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 rows=[]
 for index in (0,1):
  for duration in (-1,0,1,60):
   for rate in (.5,1.,1.25):
    for angle in (-99999.,-990.,-989.5,.4,990.,99999.):
     for acceleration in (-1.,2.75,5.):
      m.mem_write(bullet,bytes(0x3000));sounds.clear();put(0x4db67c,player);floats(player+0x5e0,60.,400.,0.);floats(0x4d8f58,rate)
      floats(bullet+0xbc0,-12.25,70.5,0.,2.5,-.125,.25,2.75,.375);floats(bullet+0x1240,.125);put(bullet+0xc20,index);put(bullet+0xc1c,38)
      t=bullet+0xc28+index*0x2c;floats(t,acceleration,angle,.35,0.);put(t+0x10,duration);put(t+0x20,0x200000)
      m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
      call(0x418140);initial=state();frames=[]
      for frame in range(96):frames.append(dict(status=call(0x419780),state=state()))
      rows.append(dict(index=index,duration=duration,rate=rate,angle=angle,acceleration=acceleration,initial=initial,frames=frames))
 out=ROOT/'artifacts/th14/bullet-speed-ramp-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} ETEX 0x200000 initializations / {len(rows)*96} motion frames.')
if __name__=='__main__':main()
