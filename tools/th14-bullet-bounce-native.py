"""Retail TH14 bounce setup and consumer, including all real wall helpers."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,im.data[raw:raw+n])
 base=0x70000000;bullet=base+0x1000;manager=base+0x6000;stack=base+0x1f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 sounds=[]
 def sound(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);sounds.append(get(sp+4));m.reg_write(UC_X86_REG_EAX,0)
 m.mem_write(0x4854a0,b'\xc3');m.mem_write(0x46e3d0,b'\xc2\x08\x00');m.hook_add(UC_HOOK_CODE,sound,begin=0x46e3d0,end=0x46e3d0)
 offsets=(0xc04,0xc20,0xbc0,0xbc4,0xbc8,0xbcc,0xbd0,0xbd4,0xbd8,0xbdc,0x1074,0x1078,0x107c,0x1080,0x1084,0x1094,0x1098,0x10a0)
 def state():return [get(bullet+n) for n in offsets]+[len(sounds)]
 def call(a):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);m.emu_start(a,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 rows=[]
 for override,(ow,oh) in enumerate(((0.,0.),(160.,300.),(0.,300.))):
  for mask in range(64):
   w=ow if ow>0 else (256. if mask&32 else 384.);h=oh if oh>0 else (320. if mask&32 else 448.)
   left,right,top,bottom=-w*.5,w*.5,224.-h*.5,224.+h*.5
   positions=((0.,224.),(left,top),(left-.125,top-.125),(right,bottom),(right-.125,bottom-.125),(0.,top),(0.,top-.125),(0.,bottom),(left,224.),(left-.125,224.),(right,224.),(right+.125,224.))
   for pos,(x,y) in enumerate(positions):
    for speed in (-99999.,-990.,2.25):
     for limit in (0,2):
      angle=(-500.,-0.,.375,500.)[(mask+pos+limit)%4]
      m.mem_write(bullet,bytes(0x3000));sounds.clear();put(0x4db530,manager);floats(manager+0x64,ow,oh);floats(0x4d8f58,1.)
      floats(bullet+0xbc0,x,y,3.,2.5,-.125,.25,2.75,angle);floats(bullet+0x1078,-.625);floats(bullet+0x1084,.125);put(bullet+0xc1c,38)
      t=bullet+0xc28;floats(t,speed,256.,320.,0.);put(t+0x10,limit);put(t+0x14,mask);put(t+0x20,0x40)
      m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
      call(0x418140);initial=state();frames=[]
      for frame in range(2):frames.append(dict(status=call(0x41a1a0),state=state()))
      rows.append(dict(override=override,mask=mask,x=x,y=y,angle=angle,speed=speed,limit=limit,initial=initial,frames=frames))
 out=ROOT/'artifacts/th14/bullet-bounce-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} bounce setups / {len(rows)*2} updates.')
if __name__=='__main__':main()
