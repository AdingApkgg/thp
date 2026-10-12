"""Retail circle allocation and stationary area clock; movement is a boundary."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main(kind='circle'):
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,im.data[raw:raw+n])
 base=0x70000000;player=base+0x1000;stack=base+0x3f000;position=base+0x30000;m.mem_map(base,0x40000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 def boundary(machine,a,size,user):
  if a==0x48f980:
   sp=m.reg_read(UC_X86_REG_ESP);p=get(sp+4);m.mem_write(p,bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,p)
 for a in (0x403cd0,0x403df0,0x48f980):
  m.mem_write(a,b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def snapshot(a):return [get(a+n) for n in (0x10,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c,0x30,0x34,0x70,0x74,0x78,0x84,0x88,0x8c,0x90,0x94,0xa0)]
 m.hook_add(UC_HOOK_MEM_INVALID,lambda machine,access,address,size,value,user: print("invalid",hex(address),"eip",hex(machine.reg_read(UC_X86_REG_EIP))) or False)
 rows=[]
 for cursor,occupied in ((0,0),(0,3),(254,3),(255,0),(256,2)):
  for duration in (-1,0,1,30):
   for rate in (.5,1.,1.5):
    for variant,(radius,growth,angle,angular) in enumerate(((32.,16.,0.,0.),(-2.,.25,3.1,.1),(0.,-1.,-3.1,-.1),(5.,0.,8.,0.))):
     m.mem_write(base,bytes(0x3e000));put(player+0xde14,cursor);put(0x4db67c,player)
     for n in range(256):
      a=player+0xde18+n*0xa4
      for off,v in ((0x10,0x8006),(0x1c,bits(angle)),(0x20,bits(angular)),(0x24,bits(17.)),(0x28,bits(19.)),(0x88,77),(0x94,66),(0xa0,55)):put(a+off,v)
     for n in range(occupied):put(player+0xde18+((cursor%256+n)%256)*0xa4+0x10,0x8007)
     for n,f in enumerate((-12.5,400.,2.)):put(position+n*4,bits(f))
     put(0x4d8f58,bits(rate));put(stack,base);put(stack+4,position)
     if kind=='circle':put(stack+8,duration);put(stack+12,150)
     else:put(stack+8,bits(angle));put(stack+12,duration);put(stack+16,150)
     m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_XMM2,bits(radius));m.reg_write(UC_X86_REG_XMM3,bits(growth));m.reg_write(UC_X86_REG_MXCSR,0x1f80)
     m.emu_start(0x450130 if kind=='circle' else 0x450270,base,count=20000);a=m.reg_read(UC_X86_REG_EAX);index=(a-player-0xde18)//0xa4
     assert 0<=index<256;frames=[snapshot(a)]
     for frame in range(64):
      m.reg_write(UC_X86_REG_ESP,stack);put(stack+0x1c,256);m.reg_write(UC_X86_REG_EBX,player+0xde90);m.reg_write(UC_X86_REG_EDI,player);m.reg_write(UC_X86_REG_EAX,256)
      m.emu_start(0x44e005,0x44e0fa,count=50000);frames.append(snapshot(a))
     rows.append(dict(cursor=cursor,occupied=occupied,duration=duration,rate=rate,variant=variant,index=index,resultCursor=get(player+0xde14),frames=frames))
 out=ROOT/f'artifacts/th14/damage-{kind}-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} {kind} allocations / {len(rows)*64} stationary update frames.')
if __name__=='__main__':main()
