"""Whole4449b0 circle allocation, actual timer initialization, controlled memset only."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x100000);player,pos,stack,ret=0x70001000,0x70050000,0x700ff000,0x700fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 def clear(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP);dest,value,count=[get(sp+k) for k in (4,8,12)];m.mem_write(dest,bytes([value&255])*count);machine.reg_write(UC_X86_REG_EAX,dest)
 m.mem_write(0x477920,b'\xc3');m.hook_add(UC_HOOK_CODE,clear,begin=0x477920,end=0x477920);m.mem_write(pos,struct.pack('<fff',-12.25,80.5,1.25));cases=[]
 for n in range(512):
  cursor=(0,1,254,255)[n%4];mode=(n//4)%6;tf=(0,1,2,0xffffffff)[(n//24)%4];radius=(-32,0,32,.125)[(n//96)%4];growth=(-16,0,16,.25)[(n//13)%4];duration=(-2147483648,-1,0,1,30,2147483647)[(n//7)%6];damage=(-2147483648,-1,0,150,2147483647)[(n//11)%5];seed=n+1
  table=[]
  for i in range(256):
   values=[(0x12340000+(i*37+j)*17+seed)&0xffffffff for j in range(37)];active=0 if mode==0 else i==(cursor+1)%256 if mode==1 else 1 if mode==2 else i!=17 if mode==3 else i!=0 if mode==4 else (i+seed)%2;values[0]=0x40000084|int(active);values[28]=tf;values[27]=5;table.extend(values)
  put(player+0xd110,cursor);m.mem_write(player+0xd114,struct.pack('<9472I',*table));put(stack,ret);put(stack+4,pos);put(stack+8,duration);put(stack+12,damage);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_XMM2,bits(radius));m.reg_write(UC_X86_REG_XMM3,bits(growth));m.emu_start(0x4449b0,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  ident=m.reg_read(UC_X86_REG_EAX);pool=bytes(m.mem_read(player+0xd114,9472*4));cases.append(dict(n=n,cursor=cursor,mode=mode,timerFlags=tf,radius=radius,growth=growth,duration=duration,damage=damage,seed=seed,id=ident,outputCursor=get(player+0xd110),poolSha256=hashlib.sha256(pool).hexdigest()))
 (ROOT/'artifacts/th16/damage-circle-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} native circle factories with whole9472-word pool snapshots')
if __name__=='__main__':main()
