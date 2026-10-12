"""Execute retail TH14 ETEX 10 setup/consumer and RNG, with sound controlled."""
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
 def sound(machine,a,size,user):sounds.append(get(m.reg_read(UC_X86_REG_ESP)+4));m.reg_write(UC_X86_REG_EAX,0)
 m.mem_write(0x4854a0,b'\xc3');m.mem_write(0x46e3d0,b'\xc2\x08\x00');m.hook_add(UC_HOOK_CODE,sound,begin=0x46e3d0,end=0x46e3d0)
 offsets=(0xc04,0xc20,0xbd8,0xbdc,0xbcc,0xbd0,0xbd4,0x102c,0x1030,0x1018,0x101c,0x1020,0x104c,0x1050,0x1054,0x1058,0x105c,0x12b4,0x12b8,0x12bc,0x12c0,0x12c4)
 def state():return [get(bullet+n) for n in offsets]+[get(0x4db510),get(0x4db514),len(sounds)]
 def call(a):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);m.emu_start(a,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 rows=[]
 for mode in (0,1,2,3,4,5,6,9):
  for duration in (-1,0,1,30):
   for rate in (.5,1.,1.25):
    for angle in (-99999.,-990.,-.4,990.,99999.):
     for target in (-999.,3.):
      m.mem_write(bullet,bytes(0x3000));sounds.clear();put(0x4db67c,player);floats(player+0x5e0,60.,400.,0.);floats(0x4d8f58,rate);put(0x4db510,1234);put(0x4db514,0)
      floats(bullet+0xbc0,-12.25,70.5,0.,2.5,-.125,.25,2.75,.375);floats(bullet+0x12b4,1.5,-.2,20.,150.,2.);floats(bullet+0x1030,.625);put(bullet+0xc1c,38)
      t=bullet+0xc28;floats(t,angle,target,0.,0.);put(t+0x10,duration);put(t+0x14,2);put(t+0x18,mode);put(t+0x1c,19);put(t+0x20,0x10)
      m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
      call(0x418140);initial=state();frames=[]
      for frame in range(96):frames.append(dict(status=call(0x419ae0),state=state()))
      rows.append(dict(mode=mode,duration=duration,rate=rate,angle=angle,target=target,initial=initial,frames=frames))
 out=ROOT/'artifacts/th14/bullet-step-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} step setups / {len(rows)*96} updates.')
if __name__=='__main__':main()
