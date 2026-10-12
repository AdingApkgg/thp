"""Retail 452050; effect allocation/interrupt/sound are recorded boundaries.
The scratch stack starts at zero; the native polar helper writes only X/Y.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,area,player,visual,stack=0x70000000,0x70001000,0x70002000,0x70010000,0x70030000,0x700ff000;m.mem_map(end,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 events=[];effect=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47f140:events.append(['interrupt',get(sp+8)])
  elif a==0x46e470:events.append(['sound',get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  else:
   p=get(sp+12);effect.extend([get(p),get(p+4),get(p+8),get(sp+16)]);events.append(['effect',get(sp+8),get(sp+20),get(sp+24),get(sp+28)])
 for a,cleanup in ((0x47f140,8),(0x46e470,4),(0x47ed10,28)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 rows=[]
 for n in range(4096):
  age=(-16,-8,-1,0,1,7,8,16,24,30,32,240)[n%12];advanced=n//12%2;power=n//24%5;seed=(0,1,0x9630,0xffff,12345,54321)[n//120%6]
  radius=(0.,4.,32.,70.)[n//720%4];angle=(-3.1415927410125732,-1.25,0.,3.1415927410125732)[n//5%4];speed=(-2.,0.,8.,16.)[n//20%4]
  events.clear();effect.clear();m.mem_write(obj,bytes(0x100));m.mem_write(area,bytes(0x100));m.mem_write(player,bytes(0x19000));m.mem_write(stack-0x2000,bytes(0x2100))
  put(0x4db67c,player);put(0x4db53c,visual);put(visual+0x10,visual+0x100);put(obj+0x14,73);put(obj+0xc0,area);put(obj+0x18,age-advanced);put(obj+0x1c,age);floats(obj+0x54,17,123,.1);floats(obj+0x6c,8,angle);floats(obj+0xb8,speed)
  put(obj+0x40,9);put(obj+0x44,10);floats(obj+0x48,10);put(obj+0x4c,0x4d8f58);put(obj+0x50,1);floats(area+0x14,radius);put(area+0x84,19);put(player+0x184b8,1234);put(0x4f5858,power*40);put(0x4f5860,40);put(0x4db508,seed);put(0x4db50c,123);floats(0x4d8f58,1)
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x452050,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  result=[get(obj+0x6c),get(obj+0xb8),*[get(obj+0x40+j*4) for j in range(3)],get(player+0x184b8),get(0x4db508),get(0x4db50c),int(bool(effect)),m.reg_read(UC_X86_REG_EAX),*(effect or [0,0,0,0])]
  rows.append(dict(age=age,advanced=advanced,power=power,seed=seed,radius=radius,angle=angle,speed=speed,result=result,events=events[:]))
 out=ROOT/'artifacts/th14/shot-hit-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} focused hit callbacks.')
if __name__=='__main__':main()
