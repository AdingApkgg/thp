"""Execute retail 414510, including nearest target, movement and libm.
Only ANM lookup is replaced by a controlled VM boundary.
"""
import hashlib,importlib,json,struct,itertools
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,player,manager,enemy,vm,stack=0x70000000,0x70001000,0x70002000,0x70022000,0x70024000,0x7002a000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 # A synthetic ANM VM is returned for the position write at 414831.
 m.mem_write(0x47f0a0,b'\xb8'+struct.pack('<I',vm)+b'\xc2\x04\x00')
 offsets=[4,8,12,0x38,0x3c,0x40,0xb8,0xbc,0xc0,0x1c,0x20,0x24,0x28,0x44,0xa4,0xa8,0xac]
 def setup(words,target,manager_present,enemy_flags,enemy_pos,rate,index):
  m.mem_write(obj,bytes(0xd0));m.mem_write(enemy,bytes(0x6000));m.mem_write(vm,bytes(0x600));m.mem_write(manager,bytes(0x2000))
  for p,v in zip(offsets,words):put(obj+p,v)
  put(obj,1);put(obj+0xc8,index);put(obj+0xc4,enemy if target else 0);put(obj+0xb0,0x4d8f58);put(obj+0xb4,1)
  put(0x4db67c,player);put(0x4db544,manager if manager_present else 0);floats(player+0x5e0,12.25,300,3);floats(0x4d8f58,rate)
  put(manager+0xd0,enemy+0x14d8);put(enemy+0x14d8,enemy);put(enemy+0x14dc,0);put(enemy+0x5244,enemy_flags);floats(enemy+0x1234,*enemy_pos,0)
 def call():
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x414510,end,count=200000);assert m.reg_read(UC_X86_REG_EIP)==end
 def state():return [get(obj+p) for p in offsets]+[int(get(obj+0xc4)==enemy)]
 cases=[]
 for i in range(864):
  index=i%8;age=(-2,0,1,89,90,91,(index+9)*10-1,(index+9)*10,(index+9)*10+1,175,199,210)[i//8%12]
  rate=(0,.5,1,1.25)[i//96%4];advanced=i//384%2
  flag=(0,1,0x20,0x4000000,0x8000000,0x400000)[i%6];pos=((0,40),(100,280),(-40,440),(700,300),(12.25,300),(-400,-200))[i//6%6]
  target=i//36%2;present=i//72%2;kind=2 if age<=(index+9)*10 else 0
  words=[*map(bits,(14.25,300,4,12.25,300,3,1.25,-2.5,0,4,(-3.1,-1.25,0,3.1)[i%4],100,.04908738657832146)),kind|0x80,(age-advanced)&0xffffffff,age&0xffffffff,bits(float(age))]
  setup(words,target,present,flag,pos,rate,index);call();cases.append(dict(words=words,target=target,present=present,flags=flag,position=pos,rate=rate,index=index,result=state()))
 paths=[]
 for index,rate in itertools.product(range(8),(.5,1,1.25)):
  words=[*map(bits,(0,0,0,12.25,300,3,0,0,0,0,index*.7853981852531433,0,.04908738657832146)),2,0xffffffff,0,0]
  setup(words,0,1,0,(0,100),rate,index);frames=[]
  for frame in range(205):call();frames.append(state())
  paths.append(dict(index=index,rate=rate,words=words,result=frames))
 (ROOT/'artifacts/th14/reimu-orb-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,paths=paths),indent=2)+'\n',encoding='utf-8')
 print(f'{len(cases)} isolated orb frames, {len(paths)} paths / {sum(len(p["result"]) for p in paths)} sequential frames')
if __name__=='__main__':main()
